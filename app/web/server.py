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
from app.schema import AgentState, Message

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


# 全局简历数据存储（用于前后端同步）
_global_resume_data = {}


@app.get("/api/resume")
async def get_resume_data():
    """获取当前加载的简历数据

    优先从工具获取，确保数据是最新的
    """
    from app.tool.cv_reader_agent_tool import CVReaderAgentTool

    # 从工具获取最新数据
    tool_data = CVReaderAgentTool.get_resume_data()
    if tool_data and isinstance(tool_data, dict) and tool_data.get("basic"):
        # 转换为纯字典，移除任何 Pydantic 特殊属性
        return {"data": _clean_resume_data(tool_data)}

    # 如果工具没有数据，返回全局变量（兜底）
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

    # 同步更新到 CVReaderAgentTool
    from app.tool.cv_reader_agent_tool import CVReaderAgentTool
    CVReaderAgentTool.set_resume_data(_global_resume_data)

    # 同步更新到 CVEditorAgentTool
    from app.tool.cv_editor_agent_tool import CVEditorAgentTool
    CVEditorAgentTool.set_resume_data(_global_resume_data)

    return {"success": True, "message": "Resume data updated"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # 为每个连接创建一个 Manus 智能体
        agent = await Manus.create()

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            prompt = message.get("prompt", "")

            if not prompt:
                continue

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

                # 清空之前的记忆
                agent.memory.messages.clear()

                # 添加用户消息
                agent.memory.add_message(Message.user_message(prompt))

                # 手动执行步骤循环，实现实时输出（限制最多5步，避免过度探索）
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

                            # 实时发送新增的消息
                            for msg in agent.memory.messages[msg_count_before:]:
                                if msg.role == "assistant":
                                    if msg.content:
                                        await websocket.send_json({
                                            "type": "thought",
                                            "content": msg.content
                                        })
                                    if msg.tool_calls:
                                        for tool_call in msg.tool_calls:
                                            await websocket.send_json({
                                                "type": "tool_call",
                                                "tool": tool_call.function.name,
                                                "args": tool_call.function.arguments
                                            })
                                elif msg.role == "tool":
                                    content = msg.content
                                    # 增加显示长度到5000字符，超过则截断
                                    if len(content) > 5000:
                                        content = content[:5000] + f"\n...(内容已截断，共{len(msg.content)}字符)"
                                    await websocket.send_json({
                                        "type": "tool_result",
                                        "tool": msg.name or "unknown",
                                        "result": content
                                    })

                            # 检查是否陷入循环
                            if agent.is_stuck():
                                break

                    # 重置步骤计数
                    agent.current_step = 0
                    agent.state = AgentState.IDLE

                    # 发送最终答案（取最后一条 assistant 内容）
                    final_answer = "任务已完成！"
                    for msg in reversed(agent.memory.messages):
                        if msg.role == "assistant" and msg.content and not msg.tool_calls:
                            final_answer = msg.content
                            break

                    await websocket.send_json({
                        "type": "answer",
                        "content": final_answer
                    })

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
    PORT = 8080
    print("========================================")
    print("  OpenManus Web 服务器")
    print("========================================")
    print(f"前端目录: {FRONTEND_DIST}")
    print(f"前端存在: {os.path.exists(FRONTEND_DIST)}")
    print(f"访问地址: http://localhost:{PORT}")
    print("========================================")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

