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

# 简单对话关键词（不需要工具的对话）
SIMPLE_CHAT_KEYWORDS = [
    "你好", "您好", "hi", "hello", "hey", "嗨", "喂",
    "谢谢", "感谢", "thanks", "thank you",
    "再见", "拜拜", "bye", "goodbye",
    "好的", "ok", "okay", "明白", "了解",
    "是什么", "什么是", "介绍一下", "解释一下",
    "你是谁", "你叫什么", "who are you"
]

def is_simple_chat(prompt: str) -> bool:
    """判断是否是简单对话（不需要工具调用）"""
    prompt_lower = prompt.lower().strip()
    # 如果消息很短且包含问候关键词
    if len(prompt) < 50:
        for keyword in SIMPLE_CHAT_KEYWORDS:
            if keyword in prompt_lower:
                return True
    return False

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
                # 判断是否是简单对话
                if is_simple_chat(prompt):
                    # 简单对话：直接用 LLM 回复，不调用工具
                    await websocket.send_json({
                        "type": "status",
                        "content": "processing",
                        "message": "正在回复..."
                    })

                    llm = LLM()
                    response = await llm.ask(
                        messages=[
                            {"role": "system", "content": "你是 OpenManus，一个友好的 AI 助手。请用简洁友好的方式回复用户。"},
                            {"role": "user", "content": prompt}
                        ]
                    )

                    await websocket.send_json({
                        "type": "answer",
                        "content": response
                    })
                else:
                    # 复杂任务：使用 Manus 智能体，实时流式输出
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

            except Exception as e:
                logger.error(f"Error: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({"type": "error", "content": str(e)})
                # 重置状态以便继续使用
                agent.state = AgentState.IDLE
                agent.current_step = 0

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        await agent.cleanup()

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

