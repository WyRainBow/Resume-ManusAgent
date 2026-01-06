"""
OpenManus Web Server - Refactored modular architecture.

This server provides:
- WebSocket endpoint for agent interaction with real-time streaming
- HTTP API for resume data management
- HTTP API for chat history and checkpoint management

Architecture:
- Uses ConnectionManager for WebSocket connection lifecycle
- Uses SessionManager for agent session management
- Uses MessageHandler for WebSocket message routing
- Uses StreamProcessor for agent execution streaming
- Uses modular routes for HTTP API endpoints
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent.manus import Manus
from app.llm import LLM
from app.logger import logger
from app.schema import AgentState, Message, Memory, Role

# Import refactored modules
from app.web.websocket.connection_manager import connection_manager
from app.web.websocket.session_manager import session_manager
from app.web.websocket.message_handler import MessageHandler
from app.web.streaming.agent_stream import StreamProcessor
from app.web.streaming.state_machine import AgentStateMachine
from app.web.routes import api_router


def _detect_context_usage(current_content: str, previous_messages: list) -> str:
    """检测 AI 是否使用了上下文信息，并生成上下文提示"""
    if not previous_messages or len(previous_messages) < 3:
        return None

    # 检测关键词，表示使用了上下文（更全面的关键词列表）
    context_keywords = [
        "根据", "基于", "之前", "刚才", "之前提到", "之前说", "之前分析",
        "从之前的", "根据之前的", "基于之前的", "根据对话", "根据历史",
        "从对话中", "从历史", "之前的内容", "之前的分析", "之前的建议",
        "从您", "您之前", "您刚才", "您提到", "您说", "您提到过",
        "现在", "接下来", "继续", "接着", "然后", "基于此",
        "从简历", "简历中", "工作经历", "技能", "项目"
    ]

    content_lower = current_content.lower()
    has_context_keyword = any(keyword in content_lower for keyword in context_keywords)

    # 如果内容很短，可能不是真正的上下文使用
    if len(current_content.strip()) < 20:
        return None

    # 检查是否引用了之前的工具调用结果（通过检查是否有工具相关的关键词）
    tool_related_keywords = ["分析", "优化", "建议", "问题", "亮点", "改进", "简历", "工作经历"]
    has_tool_context = any(keyword in content_lower for keyword in tool_related_keywords)

    # 如果既没有上下文关键词，也没有工具相关关键词，可能不是上下文使用
    if not has_context_keyword and not has_tool_context:
        return None

    # 提取之前的对话关键信息
    context_summary = []

    # 查找最近的用户消息（问题或请求）- 只找非工具调用的用户消息
    # 排除系统提示词相关内容
    system_keywords = ["工具选择", "根据用户输入", "## ", "**重要", "规则", "意图识别"]

    user_requests = []
    for msg in reversed(previous_messages[-20:]):  # 检查最近20条消息
        if msg.role == "user" and msg.content:
            user_content = msg.content.strip()
            # 排除：太短的消息、工具调用、系统提示词
            if len(user_content) > 5 and not user_content.startswith("{"):
                # 检查是否像系统提示词
                is_system_like = any(kw in user_content for kw in system_keywords)
                if not is_system_like and len(user_content) < 200:  # 真正的用户请求通常较短
                    user_requests.append(user_content)
                    if len(user_requests) >= 2:  # 收集最近2条用户消息
                        break

    # 添加最近的用户请求
    if user_requests:
        latest_request = user_requests[0]
        if len(latest_request) > 80:
            latest_request = latest_request[:80] + "..."
        context_summary.append(f"**您的请求**：{latest_request}")

    # 查找最近的 AI 回复（分析或优化建议）- 查找有实际内容的回复
    ai_responses = []
    for msg in reversed(previous_messages[-20:]):
        if msg.role == "assistant" and msg.content and not msg.tool_calls:
            content = msg.content.strip()
            # 查找包含关键信息的回复，且不是思考过程
            if len(content) > 30 and any(keyword in content for keyword in ["分析", "优化", "建议", "问题", "亮点", "改进", "简历"]):
                # 提取关键信息（取前100字符）
                key_info = content[:100].replace('\n', ' ').strip()
                # 清理 Markdown 格式
                key_info = key_info.replace('**', '').replace('*', '').replace('#', '').strip()
                if len(key_info) > 20:
                    if len(key_info) > 100:
                        key_info = key_info[:100] + "..."
                    ai_responses.append(key_info)
                    if len(ai_responses) >= 1:  # 只取最近1条有意义的回复
                        break

    # 添加之前的 AI 分析
    if ai_responses:
        context_summary.append(f"**之前的分析**：{ai_responses[0]}")

    # 如果找到了上下文信息，生成提示
    if context_summary:
        context_text = "\n".join(context_summary)
        return f"根据之前的对话，我了解到：\n\n{context_text}"

    return None

# 定义消息类型
class AgentMessage(BaseModel):
    type: str  # "thought", "tool_call", "tool_result", "answer", "error"
    content: Any
    step: int = 0


app = FastAPI(
    title="OpenManus API",
    description="Resume optimization agent with real-time streaming",
    version="2.0.0",
)

# 允许跨域（方便前端开发）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular routes
app.include_router(api_router, prefix="/api")

# Create stream processor for agent execution
stream_processor = StreamProcessor()

# Create message handler
message_handler = MessageHandler(
    connection_manager=connection_manager,
    session_manager=session_manager,
    stream_processor=stream_processor,
)

# Legacy: Keep active_connections list for backward compatibility
active_connections = []

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/frontend-log")
async def log_frontend_event(event: dict):
    """接收前端日志并保存到文件"""
    try:
        from pathlib import Path
        from datetime import datetime

        # 获取当前日期
        current_date = datetime.now().strftime("%Y%m%d")
        log_dir = Path(__file__).parent.parent.parent / "logs" / "frontend"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{current_date}-frontend.log"

        # 格式化日志条目
        timestamp = event.get("timestamp", datetime.now().isoformat())
        level = event.get("level", "info").upper()
        message = event.get("message", "")
        data = event.get("data")

        # 构建日志行
        log_line = f"{timestamp} | {level} | {message}"
        if data:
            log_line += f" | {str(data)[:200]}"  # 限制数据长度

        # 写入日志文件
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to write frontend log: {e}")
        return {"status": "error", "message": str(e)}


# 全局简历数据存储（用于前后端同步）
_global_resume_data = {}


@app.get("/api/resume")
async def get_resume_data():
    """获取当前加载的简历数据 - 使用 parse_markdown_resume 解析"""
    from app.utils.resume_parser import parse_markdown_resume
    from pathlib import Path

    resume_path = Path("app/docs/韦宇_简历.md")

    if not resume_path.exists():
        return {"data": {}}

    try:
        data = parse_markdown_resume(str(resume_path))
        return {"data": data}
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        return {"data": {}}


def _clean_resume_data(data: dict) -> dict:
    """清理简历数据，确保可以 JSON 序列化

    移除 Pydantic 模型的私有属性
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # 跳过私有属性和特殊属性
        if key.startswith("_") or key in ["__pydantic_private__", "__pydantic_extra__"]:
            continue
        if isinstance(value, dict):
            result[key] = _clean_resume_data(value)
        elif isinstance(value, list):
            result[key] = [_clean_resume_data(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result


@app.post("/api/resume")
async def set_resume_data(data: dict):
    """设置简历数据"""
    global _global_resume_data
    _global_resume_data = data

    # 同步更新到所有需要简历数据的工具
    from app.tool.cv_reader_agent_tool import CVReaderAgentTool
    from app.tool.cv_analyzer_agent_tool import CVAnalyzerAgentTool
    from app.tool.cv_editor_agent_tool import CVEditorAgentTool

    CVReaderAgentTool.set_resume_data(_global_resume_data)
    CVAnalyzerAgentTool.set_resume_data(_global_resume_data)
    CVEditorAgentTool.set_resume_data(_global_resume_data)

    return {"success": True, "message": "Resume data updated"}


# 全局存储 CheckpointSaver 和 ChatHistory 实例
_global_checkpoint_saver = None
_global_chat_history = None


def get_checkpoint_saver():
    """获取全局 CheckpointSaver 实例"""
    global _global_checkpoint_saver
    if _global_checkpoint_saver is None:
        from app.memory import CheckpointSaver
        _global_checkpoint_saver = CheckpointSaver()
    return _global_checkpoint_saver


def get_chat_history_sync():
    """获取全局 ChatHistory 实例 (同步版本)"""
    global _global_chat_history
    if _global_chat_history is None:
        from app.memory import ChatHistoryManager
        _global_chat_history = ChatHistoryManager()
    return _global_chat_history


@app.get("/api/history/chat")
async def get_chat_history_api():
    """获取对话历史"""
    try:
        chat_history = get_chat_history_sync()
        messages = chat_history.get_messages()

        # 转换为前端格式
        history_messages = []
        for msg in messages:
            history_messages.append({
                "role": msg.role.value,  # user | assistant | system
                "content": msg.content or "",
                "timestamp": getattr(msg, 'timestamp', None)
            })

        return {"messages": history_messages}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return {"messages": []}


@app.get("/api/history/checkpoints")
async def get_checkpoint_history():
    """获取 Checkpoint 版本历史"""
    try:
        checkpoint_saver = get_checkpoint_saver()
        versions = checkpoint_saver.list_versions()

        return {"checkpoints": versions}
    except Exception as e:
        logger.error(f"Error getting checkpoint history: {e}")
        return {"checkpoints": []}


@app.post("/api/history/rollback/{version}")
async def rollback_to_version(version: int):
    """回滚到指定版本"""
    try:
        checkpoint_saver = get_checkpoint_saver()
        resume_snapshot = checkpoint_saver.rollback(version)

        if resume_snapshot:
            # 更新全局简历数据
            global _global_resume_data
            _global_resume_data = {
                "raw_content": resume_snapshot.raw_content,
                "sections": resume_snapshot.sections
            }

            return {
                "success": True,
                "version": version,
                "message": f"已回滚到版本 {version}"
            }
        else:
            return {"success": False, "message": "版本不存在"}
    except Exception as e:
        logger.error(f"Error rolling back to version {version}: {e}")
        return {"success": False, "message": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for agent interaction with streaming support.

    This endpoint handles real-time communication with the agent,
    streaming thoughts, tool calls, tool results, and answers.

    Architecture:
    - Uses ConnectionManager for connection lifecycle
    - Uses SessionManager for agent session management
    - Preserves ChatHistory with Tool messages for context
    """
    # Generate unique client ID for this connection
    client_id = str(uuid.uuid4())

    # Accept connection
    await connection_manager.connect(websocket, client_id)
    active_connections.append(websocket)

    # Get global ChatHistory
    global_chat_history = get_chat_history_sync()

    logger.info(f"WebSocket client connected: {client_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type", "prompt")
            prompt = message.get("prompt", "")
            resume_path = message.get("cv_path") or message.get("resume_path")

            # Handle different message types
            if message_type == "prompt":
                if not prompt:
                    await connection_manager.send_to_client(
                        {"type": "error", "content": "Prompt is required"},
                        client_id
                    )
                    continue

                # Get or create session
                session = await session_manager.get_or_create_session(
                    client_id,
                    cv_path=resume_path,
                )

                # Restore ChatHistory messages to agent memory
                existing_messages = global_chat_history.get_messages()
                if existing_messages and len(session.agent.memory.messages) == 0:
                    logger.info(f"📜 恢复 {len(existing_messages)} 条历史消息到 agent")
                    for msg in existing_messages:
                        # 处理 role，可能是枚举或字符串
                        role_value = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                        if role_value == "user":
                            session.agent.memory.add_message(Message.user_message(msg.content))
                            logger.debug(f"  📝 恢复 USER 消息: {len(msg.content or '')} 字符")
                        elif role_value == "assistant":
                            # Assistant 消息可能包含 tool_calls
                            session.agent.memory.add_message(Message(
                                role=Role.ASSISTANT,
                                content=msg.content,
                                tool_calls=msg.tool_calls
                            ))
                            has_tools = bool(msg.tool_calls)
                            logger.debug(f"  🤖 恢复 ASSISTANT 消息: {len(msg.content or '')} 字符, tool_calls={has_tools}")
                        elif role_value == "tool":
                            # 🚨 关键修复：恢复 Tool 消息（包含优化建议 JSON）
                            session.agent.memory.add_message(Message.tool_message(
                                content=msg.content,
                                name=msg.name or "unknown",
                                tool_call_id=msg.tool_call_id or ""
                            ))
                            logger.info(f"  📋 恢复 TOOL 消息: {msg.name}, {len(msg.content or '')} 字符")

                # Update resume path if provided
                if resume_path:
                    session.agent._current_resume_path = resume_path
                    logger.info(f"📄 设置当前简历路径: {resume_path}")

                # Create state machine for this execution
                state_machine = AgentStateMachine(client_id)

                # Add user message to ChatHistory
                global_chat_history.add_message(Message(role=Role.USER, content=prompt))

                # Start streaming execution
                try:
                    session.is_running = True
                    session.reset_stop_event()

                    # Execute with streaming - send events directly
                    async for event in stream_processor.start_stream(
                        session_id=client_id,
                        agent=session.agent,
                        state_machine=state_machine,
                        event_sender=lambda d: None,  # Not used, events are yielded
                        user_message=prompt,
                        chat_history_manager=global_chat_history,
                    ):
                        # Convert event to dict and send
                        event_dict = event.to_dict()

                        # Add context detection for thought messages
                        if event_dict.get("type") == "thought":
                            content = event_dict.get("content", "")
                            context_info = _detect_context_usage(
                                content,
                                session.agent.memory.messages[:-1]
                            )
                            if context_info:
                                await connection_manager.send_to_client({
                                    "type": "context",
                                    "content": context_info
                                }, client_id)

                        await connection_manager.send_to_client(event_dict, client_id)

                except Exception as e:
                    logger.exception(f"[{client_id}] Error in stream processing: {e}")
                    await connection_manager.send_to_client(
                        {"type": "error", "content": str(e)},
                        client_id
                    )
                    session.is_running = False

            elif message_type == "restore_history":
                # Restore chat history from in-memory storage
                try:
                    messages = global_chat_history.get_messages()
                    await connection_manager.send_to_client({
                        "type": "history_restored",
                        "data": {
                            "message_count": len(messages),
                            "messages": [{"role": m.role, "content": m.content} for m in messages],
                        },
                    }, client_id)
                    logger.info(f"[{client_id}] History restored ({len(messages)} messages)")
                except Exception as e:
                    logger.exception(f"[{client_id}] Error restoring history: {e}")
                    await connection_manager.send_to_client(
                        {"type": "error", "content": f"Error restoring history: {e}"},
                        client_id
                    )

            elif message_type == "clear_history":
                # Clear chat history
                try:
                    global_chat_history.clear()
                    await connection_manager.send_to_client({
                        "type": "history_cleared",
                        "data": {"message": "Chat history cleared"},
                    }, client_id)
                    logger.info(f"[{client_id}] History cleared")
                except Exception as e:
                    logger.exception(f"[{client_id}] Error clearing history: {e}")
                    await connection_manager.send_to_client(
                        {"type": "error", "content": f"Error clearing history: {e}"},
                        client_id
                    )

            elif message_type == "stop":
                # Stop current execution
                await stream_processor.stop_stream(client_id)
                await session_manager.stop_session(client_id)
                await connection_manager.send_to_client({
                    "type": "stopped",
                    "data": {"message": "Agent execution stopped"},
                }, client_id)
                logger.info(f"[{client_id}] Agent stopped by user")

            else:
                await connection_manager.send_to_client(
                    {"type": "error", "content": f"Unknown message type: {message_type}"},
                    client_id
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.exception(f"Unexpected error in websocket endpoint for {client_id}: {e}")
    finally:
        # Cleanup
        connection_manager.disconnect(client_id)
        if websocket in active_connections:
            active_connections.remove(websocket)
        await session_manager.remove_session(client_id)

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")

# 挂载前端构建产物
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
    logger.info(f"静态文件已挂载: {FRONTEND_DIST}")
else:
    logger.warning(f"前端构建目录不存在: {FRONTEND_DIST}")
    # 提供一个简单的首页
    @app.get("/")
    async def root():
        return {"message": "OpenManus API 服务已启动", "note": "前端未构建，请先运行 cd frontend && npm run build"}

if __name__ == "__main__":
    import uvicorn
    PORT = 8000
    print("========================================")
    print("  OpenManus Web 服务器")
    print("========================================")
    print(f"前端目录: {FRONTEND_DIST}")
    print(f"前端存在: {os.path.exists(FRONTEND_DIST)}")
    print(f"访问地址: http://localhost:{PORT}")
    print("========================================")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

