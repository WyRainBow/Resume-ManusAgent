import asyncio
import json
import os
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent.manus import Manus
from app.llm import LLM
from app.logger import logger
from app.schema import AgentState, Message, Memory

# 简单对话关键词（不需要工具的对话）
SIMPLE_CHAT_KEYWORDS = [
    "你好", "您好", "hi", "hello", "hey", "嗨", "喂",
    "谢谢", "感谢", "thanks", "thank you",
    "再见", "拜拜", "bye", "goodbye",
    "好的", "ok", "okay", "明白", "了解",
    "是什么", "什么是", "介绍一下", "解释一下",
    "你是谁", "你叫什么", "who are you"
]

# 定义消息类型
class AgentMessage(BaseModel):
    type: str  # "thought", "tool_call", "tool_result", "answer", "error"
    content: Any
    step: int = 0


app = FastAPI()

# 允许跨域（方便前端开发）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储活跃连接
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
    """获取当前加载的简历数据

    优先从 ResumeDataStore 获取，确保数据是最新的
    """
    from app.tool.resume_data_store import ResumeDataStore

    # 从 ResumeDataStore 获取最新数据
    tool_data = ResumeDataStore.get_data()
    if tool_data and isinstance(tool_data, dict) and tool_data.get("basic"):
        # 转换为纯字典，移除任何 Pydantic 特殊属性
        return {"data": _clean_resume_data(tool_data)}

    # 如果没有数据，返回全局变量（兜底）
    return {"data": _global_resume_data}


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

    # 同步更新到 ResumeDataStore
    from app.tool.resume_data_store import ResumeDataStore
    ResumeDataStore.set_data(_global_resume_data)

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
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # 为每个连接创建一个 Manus 智能体
        agent = await Manus.create()

        # 跟踪上次发送的 context，避免重复发送
        last_sent_context = None

        # 获取全局 ChatHistory 并同步给 agent
        global_chat_history = get_chat_history_sync()
        agent._chat_history = global_chat_history

        # 如果 ChatHistory 有消息，恢复到 agent.memory
        existing_messages = global_chat_history.get_messages()
        if existing_messages:
            logger.info(f"📜 恢复 {len(existing_messages)} 条历史消息到 agent")
            for msg in existing_messages:
                # msg.role 是字符串类型 (ROLE_TYPE)，不是枚举
                if msg.role == "user":
                    agent.memory.add_message(Message.user_message(msg.content))
                elif msg.role == "assistant":
                    agent.memory.add_message(Message.assistant_message(msg.content))

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            prompt = message.get("prompt", "")
            resume_path = message.get("resume_path")  # 当前简历文件路径

            # 处理前端发来的历史消息恢复请求
            if message.get("type") == "restore_history":
                history_messages = message.get("messages", [])
                if history_messages:
                    logger.info(f"📜 从前端恢复 {len(history_messages)} 条历史消息")
                    for msg in history_messages:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role == "user":
                            global_chat_history.add_message(Message.user_message(content))
                            agent.memory.add_message(Message.user_message(content))
                        elif role == "assistant":
                            global_chat_history.add_message(Message.assistant_message(content))
                            agent.memory.add_message(Message.assistant_message(content))
                continue

            # 处理清除历史请求
            if message.get("type") == "clear_history":
                logger.info("🧹 收到清除历史请求，正在清除 Agent 状态...")
                # 清除 Agent 的 memory
                agent.memory.messages.clear()
                # 重置对话状态
                agent._conversation_state.reset()
                # 清除简历数据
                from app.tool.resume_data_store import ResumeDataStore
                ResumeDataStore.clear_data()
                logger.info("🧹 Agent 状态已清除")
                await websocket.send_json({
                    "type": "status",
                    "content": "ready"
                })
                continue

            # 处理停止请求
            if message.get("type") == "stop":
                logger.info("🛑 收到停止请求，正在停止 agent 执行...")
                agent.state = AgentState.FINISHED
                agent.current_step = 0
                await websocket.send_json({
                    "type": "status",
                    "content": "stopped",
                    "message": "已停止执行"
                })
                await websocket.send_json({
                    "type": "answer",
                    "content": "⏹️ 执行已停止"
                })
                continue

            if not prompt:
                continue

            # 更新当前简历路径
            if resume_path:
                agent._current_resume_path = resume_path
                logger.info(f"📄 设置当前简历路径: {resume_path}")

            try:
                # 所有请求都使用 Manus 智能体处理
                await websocket.send_json({
                    "type": "status",
                    "content": "processing",
                    "message": "收到任务，正在分析..."
                })

                # 确保智能体处于 IDLE 状态
                if agent.state != AgentState.IDLE:
                    agent.state = AgentState.IDLE
                    agent.current_step = 0

                # 不再清空记忆，保持对话上下文
                # agent.memory.messages.clear()  # 已移除：支持多轮对话

                # 清理不完整的消息序列，避免 OpenAI API 报错
                agent.memory.cleanup_incomplete_sequences()

                # 添加用户消息到 ChatHistory
                from app.schema import Role
                global_chat_history.add_message(Message(role=Role.USER, content=prompt))

                # 添加用户消息
                agent.memory.add_message(Message.user_message(prompt))

                # 同步到 LangChain Memory
                if hasattr(agent, '_langchain_memory') and agent._langchain_memory:
                    agent._langchain_memory.add_user_message(prompt)

                # 重置 context 跟踪，让新请求可以发送新的 context
                last_sent_context = None
                last_sent_thought = None  # 跟踪最近发送的思考内容，避免重复

                # 手动执行步骤循环，实现实时输出
                # 根据任务类型动态调整最大步数
                # 分析类任务需要更多步骤
                if any(keyword in prompt.lower() for keyword in ["分析", "analyze", "深入", "详细"]):
                    max_steps = 10
                else:
                    max_steps = 5
                results = []

                async with agent.state_context(AgentState.RUNNING):
                    while agent.current_step < max_steps and agent.state != AgentState.FINISHED:
                            agent.current_step += 1

                            # 发送当前步骤
                            await websocket.send_json({
                                "type": "step",
                                "step": agent.current_step,
                                "content": f"执行步骤 {agent.current_step}/{max_steps}"
                            })

                            # 记录执行前的消息数量
                            msg_count_before = len(agent.memory.messages)

                            # 执行一步
                            step_result = await agent.step()
                            results.append(step_result)

                            # 实时发送新增的消息（在检查等待之前，确保工具结果被发送）
                            new_messages = agent.memory.messages[msg_count_before:]

                            # 检查之前的消息中是否有分析工具结果（不仅是本次 step）
                            has_recent_analysis_result = False
                            for msg in reversed(agent.memory.messages[-10:]):
                                if msg.role == "tool" and msg.name in ['education_analyzer', 'cv_analyzer_agent']:
                                    has_recent_analysis_result = True
                                    break

                            for msg in new_messages:
                                if msg.role == "assistant":
                                    if msg.content:
                                        # 判断是否是分析结果回复：
                                        # 检查内容是否包含分析结果的特征标记
                                        analysis_result_markers = [
                                            "📊 分析结果摘要",
                                            "💡 优化建议",
                                            "🎯 我最推荐的优化",
                                            "是否要应用这个优化",
                                            "是否要优化",
                                            "是否要优化这段教育经历",
                                            "综合评分"
                                        ]
                                        contains_analysis_result = any(marker in msg.content for marker in analysis_result_markers)

                                        # 如果包含分析结果特征，标记为 answer
                                        is_final_answer = has_recent_analysis_result and contains_analysis_result

                                        if is_final_answer:
                                            # 这是分析结果回复，标记为 answer
                                            logger.info(f"[分析结果回复] {msg.content[:200]}...")  # 记录前200字符
                                            await websocket.send_json({
                                                "type": "answer",
                                                "content": msg.content
                                            })
                                            # 标记已发送 answer，避免循环结束后重复发送
                                            last_sent_thought = msg.content  # 使用这个标记避免重复
                                        else:
                                            # 这是思考过程，标记为 thought
                                            logger.info(f"[思考过程] {msg.content[:200]}...")  # 记录前200字符
                                            # 避免发送重复的思考内容
                                            if msg.content != last_sent_thought:
                                                await websocket.send_json({
                                                    "type": "thought",
                                                    "content": msg.content
                                                })
                                                last_sent_thought = msg.content
                                    if msg.tool_calls:
                                        for tool_call in msg.tool_calls:
                                            tool_name = tool_call.function.name
                                            tool_args = tool_call.function.arguments
                                            # 记录工具调用到日志
                                            logger.info(f"[工具调用] {tool_name} | 参数: {str(tool_args)[:100]}...")
                                            await websocket.send_json({
                                                "type": "tool_call",
                                                "tool": tool_call.function.name,
                                                "args": tool_call.function.arguments
                                            })
                                elif msg.role == "tool":
                                    content = msg.content

                                    # 清理 "Observed output of cmd..." 前缀，让内容更友好
                                    if content.startswith("Observed output of cmd `"):
                                        # 提取实际内容（去掉前缀）
                                        import re
                                        prefix_pattern = r"Observed output of cmd `[^`]+` executed:\n"
                                        content = re.sub(prefix_pattern, "", content, count=1)
                                    elif content.startswith("Cmd `"):
                                        # 处理 "Cmd `xxx` completed with no output" 的情况
                                        content = "工具执行完成，无输出内容"

                                    # 增加显示长度到5000字符，超过则截断
                                    if len(content) > 5000:
                                        content = content[:5000] + f"\n...(内容已截断，共{len(msg.content)}字符)"
                                    # 记录工具结果到日志
                                    logger.info(f"[工具结果] {msg.name or 'unknown'} | 长度: {len(msg.content)} 字符")
                                    await websocket.send_json({
                                        "type": "tool_result",
                                        "tool": msg.name or "unknown",
                                        "result": content
                                    })

                            # 检查是否陷入循环
                            if agent.is_stuck():
                                logger.info("⚠️ Agent 检测到循环，终止执行")
                                break

                            # 检查分析任务是否完成：分析工具返回结果 + assistant 输出结果后应该停止
                            if has_recent_analysis_result:
                                # 检查最后一条 assistant 消息是否包含分析结果
                                for msg in reversed(agent.memory.messages[-5:]):
                                    if msg.role == "assistant" and msg.content:
                                        contains_result = any(marker in msg.content for marker in analysis_result_markers)
                                        # 不包含 tool_calls 表示已经输出了结果，应该停止
                                        if contains_result and (not msg.tool_calls or len(msg.tool_calls) == 0):
                                            logger.info(f"✅ 分析任务完成，终止循环")
                                            agent.state = AgentState.FINISHED
                                            break
                                if agent.state == AgentState.FINISHED:
                                    break

                    # 重置步骤计数
                    agent.current_step = 0
                    agent.state = AgentState.IDLE

                    # 检查是否已经在 step 循环中发送过 answer（分析工具完成后发送的 answer）
                    # 通过检查最后的消息序列：分析工具结果 -> 没有 tool_calls 的 assistant 消息
                    answer_already_sent_in_loop = False
                    has_analysis_tool_result = False
                    for msg in reversed(agent.memory.messages[-10:]):
                        if msg.role == "tool" and msg.name in ['education_analyzer', 'cv_analyzer_agent']:
                            has_analysis_tool_result = True
                        elif msg.role == "assistant" and msg.content and has_analysis_tool_result:
                            # 在分析工具结果之后，如果有没有 tool_calls 的 assistant 消息，说明可能在循环中已经作为 answer 发送
                            if not msg.tool_calls or len(msg.tool_calls) == 0:
                                answer_already_sent_in_loop = True
                            break

                    # 只有在循环中没有发送过 answer 的情况下，才发送最终答案
                    if not answer_already_sent_in_loop:
                        # 发送最终答案（取最后一条有内容的 assistant 消息）
                        final_answer = "任务已完成！"
                        for msg in reversed(agent.memory.messages):
                            if msg.role == "assistant" and msg.content:
                                final_answer = msg.content
                                break

                        await websocket.send_json({
                            "type": "answer",
                            "content": final_answer
                        })

                    # 添加 assistant 回复到 ChatHistory（无论是否在循环中发送过）
                    final_answer = "任务已完成！"
                    for msg in reversed(agent.memory.messages):
                        if msg.role == "assistant" and msg.content:
                            final_answer = msg.content
                            break
                    global_chat_history.add_message(Message(role=Role.ASSISTANT, content=final_answer))
                    logger.info(f"📜 已保存对话到 ChatHistory: 用户消息 + AI 回复")

            except WebSocketDisconnect:
                # 客户端主动断开连接，正常情况，不需要记录错误
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await websocket.send_json({"type": "error", "content": str(e)})
                except Exception:
                    # 连接已关闭，无法发送错误消息
                    pass
                # 重置状态以便继续使用
                agent.state = AgentState.IDLE
                agent.current_step = 0

    except WebSocketDisconnect:
        # 客户端断开连接，正常清理
        if websocket in active_connections:
            active_connections.remove(websocket)
        await agent.cleanup()
    except Exception as e:
        # 捕获其他未预期的异常
        logger.error(f"Unexpected error in websocket endpoint: {e}")
        import traceback
        traceback.print_exc()
        if websocket in active_connections:
            active_connections.remove(websocket)
        try:
            await agent.cleanup()
        except Exception:
            pass

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

