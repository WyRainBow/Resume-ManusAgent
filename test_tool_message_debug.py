#!/usr/bin/env python3
"""
测试工具调用结果传递问题
复现问题：加载简历后，询问"我是哪个大学的"无法获取到工具调用结果
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent.manus import Manus
from app.llm import LLM
from app.schema import Message
from app.logger import define_log_level

# 设置日志级别为 DEBUG（使用 loguru）
logger = define_log_level(print_level="DEBUG", logfile_level="DEBUG")

async def test_tool_message_flow():
    """测试工具调用结果传递"""
    print("=" * 80)
    print("测试工具调用结果传递")
    print("=" * 80)

    # 创建 agent
    agent = await Manus.create()

    try:
        # 步骤1: 问候
        print("\n[步骤1] 用户: 你好")
        agent.memory.add_message(Message.user_message("你好"))
        await agent.step()
        print(f"✅ 步骤1完成，memory.messages 数量: {len(agent.memory.messages)}")

        # 打印当前消息
        print("\n当前消息列表:")
        for i, msg in enumerate(agent.memory.messages):
            print(f"  [{i}] {msg.role}: {msg.content[:100] if msg.content else ''}...")

        # 步骤2: 加载简历
        print("\n[步骤2] 用户: 加载简历")
        resume_path = "/Users/wy770/Resume_OpenMauns/OpenManus/app/docs/韦宇_简历.md"
        agent.memory.add_message(Message.user_message(f"加载简历{resume_path}"))

        # 执行多步直到完成
        max_steps = 10
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")
            result = await agent.step()
            print(f"Step result: {result[:200] if result else 'None'}...")

            # 检查是否完成
            if agent.state.value == "FINISHED":
                print("✅ Agent 完成")
                break

        print(f"\n✅ 步骤2完成，memory.messages 数量: {len(agent.memory.messages)}")

        # 打印当前消息（包括 tool 消息）
        print("\n当前消息列表（包括 tool 消息）:")
        for i, msg in enumerate(agent.memory.messages):
            role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            content_preview = (msg.content[:100] if msg.content else '')
            tool_calls_info = f" [tool_calls: {len(msg.tool_calls)}]" if msg.tool_calls else ""
            tool_call_id_info = f" [tool_call_id: {msg.tool_call_id}]" if msg.tool_call_id else ""
            print(f"  [{i}] {role}{tool_calls_info}{tool_call_id_info}: {content_preview}...")

        # 检查 tool 消息
        tool_messages = []
        for msg in agent.memory.messages:
            role_val = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            if role_val == 'tool':
                tool_messages.append(msg)
        print(f"\n🔍 Tool 消息数量: {len(tool_messages)}")
        for tm in tool_messages:
            print(f"  - tool_call_id: {tm.tool_call_id}, name: {tm.name}, content长度: {len(tm.content) if tm.content else 0}")

        # 步骤3: 询问"我是哪个大学的"
        print("\n[步骤3] 用户: 我是哪个大学的")
        agent.memory.add_message(Message.user_message("我是哪个大学的"))

        # 重置 agent 状态以便继续执行
        from app.schema import AgentState
        agent.state = AgentState.RUNNING

        # 执行多步直到完成
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")
            result = await agent.step()
            print(f"Step result: {result[:200] if result else 'None'}...")

            # 检查是否完成
            if agent.state.value == "FINISHED":
                print("✅ Agent 完成")
                break

        print(f"\n✅ 步骤3完成，memory.messages 数量: {len(agent.memory.messages)}")

        # 打印最终消息
        print("\n最终消息列表:")
        for i, msg in enumerate(agent.memory.messages):
            role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            content_preview = (msg.content[:100] if msg.content else '')
            tool_calls_info = f" [tool_calls: {len(msg.tool_calls)}]" if msg.tool_calls else ""
            tool_call_id_info = f" [tool_call_id: {msg.tool_call_id}]" if msg.tool_call_id else ""
            print(f"  [{i}] {role}{tool_calls_info}{tool_call_id_info}: {content_preview}...")

        # 检查最后一条 assistant 消息是否包含答案
        last_assistant = None
        for msg in reversed(agent.memory.messages):
            role_val = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            if role_val == 'assistant':
                last_assistant = msg
                break

        if last_assistant and last_assistant.content:
            if "大学" in last_assistant.content or "教育" in last_assistant.content:
                print("\n✅ 成功：最后一条 assistant 消息包含大学信息")
                print(f"内容: {last_assistant.content[:500]}")
            else:
                print("\n❌ 失败：最后一条 assistant 消息不包含大学信息")
                print(f"内容: {last_assistant.content[:500]}")
        else:
            print("\n❌ 失败：没有找到最后一条 assistant 消息")

    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_tool_message_flow())

