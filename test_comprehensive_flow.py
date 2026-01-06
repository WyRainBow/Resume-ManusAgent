#!/usr/bin/env python3
"""
综合测试：工具调用结果传递
测试场景：
1. 加载简历
2. 问"我是哪个大学的"
3. 问"介绍一下广东工业大学"
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent.manus import Manus
from app.llm import LLM
from app.schema import Message, AgentState
from app.logger import define_log_level

# 设置日志级别为 DEBUG（使用 loguru）
logger = define_log_level(print_level="INFO", logfile_level="DEBUG")

async def test_comprehensive_flow():
    """综合测试工具调用结果传递"""
    print("=" * 80)
    print("综合测试：工具调用结果传递")
    print("=" * 80)

    # 创建 agent
    agent = await Manus.create()
    resume_path = "/Users/wy770/Resume_OpenMauns/OpenManus/app/docs/韦宇_简历.md"

    try:
        # ========== 场景1: 加载简历 ==========
        print("\n" + "=" * 80)
        print("【场景1】加载简历")
        print("=" * 80)
        agent.memory.add_message(Message.user_message(f"加载简历{resume_path}"))

        # 重置 agent 状态
        agent.state = AgentState.RUNNING

        # 执行多步直到完成
        max_steps = 10
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")
            result = await agent.step()
            print(f"结果: {result[:150] if result else 'None'}...")

            if agent.state.value == "FINISHED":
                print("✅ Agent 完成")
                break

        # 检查 tool 消息
        tool_messages = [msg for msg in agent.memory.messages
                        if (hasattr(msg, 'role') and hasattr(msg.role, 'value') and msg.role.value == 'tool')
                        or (hasattr(msg, 'role') and str(msg.role) == 'tool')]
        cv_reader_tools = [tm for tm in tool_messages if tm.name == 'cv_reader_agent']

        print(f"\n✅ 场景1完成，memory.messages 数量: {len(agent.memory.messages)}")
        print(f"✅ Tool 消息数量: {len(tool_messages)}")
        print(f"✅ cv_reader_agent 工具消息数量: {len(cv_reader_tools)}")

        if cv_reader_tools:
            last_cv_tool = cv_reader_tools[-1]
            content_preview = last_cv_tool.content[:200] if last_cv_tool.content else ''
            print(f"✅ 最后一条 cv_reader_agent 消息内容预览: {content_preview}...")
            if "CV/Resume Context" in (last_cv_tool.content or ""):
                print("✅ ✅ 简历数据已成功加载！")
            else:
                print("❌ 简历数据未成功加载")

        # ========== 场景2: 问"我是哪个大学的" ==========
        print("\n" + "=" * 80)
        print("【场景2】问：我是哪个大学的")
        print("=" * 80)
        agent.memory.add_message(Message.user_message("我是哪个大学的"))

        # 重置 agent 状态
        agent.state = AgentState.RUNNING

        # 执行多步直到完成
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")
            result = await agent.step()
            print(f"结果: {result[:150] if result else 'None'}...")

            if agent.state.value == "FINISHED":
                print("✅ Agent 完成")
                break

        # 检查最后一条 assistant 消息
        last_assistant = None
        for msg in reversed(agent.memory.messages):
            role_val = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            if role_val == 'assistant' and msg.content:
                last_assistant = msg
                break

        print(f"\n✅ 场景2完成，memory.messages 数量: {len(agent.memory.messages)}")
        if last_assistant:
            print(f"✅ 最后一条 assistant 消息: {last_assistant.content[:300]}")
            if "大学" in last_assistant.content or "中山大学" in last_assistant.content:
                print("✅ ✅ 成功回答了大学信息！")
            else:
                print("❌ 未回答大学信息")

        # ========== 场景3: 问"介绍一下广东工业大学" ==========
        print("\n" + "=" * 80)
        print("【场景3】问：介绍一下广东工业大学")
        print("=" * 80)
        agent.memory.add_message(Message.user_message("介绍一下广东工业大学"))

        # 重置 agent 状态
        agent.state = AgentState.RUNNING

        # 执行多步直到完成
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")
            result = await agent.step()
            print(f"结果: {result[:150] if result else 'None'}...")

            if agent.state.value == "FINISHED":
                print("✅ Agent 完成")
                break

        # 检查最后一条 assistant 消息
        last_assistant = None
        for msg in reversed(agent.memory.messages):
            role_val = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            if role_val == 'assistant' and msg.content:
                last_assistant = msg
                break

        print(f"\n✅ 场景3完成，memory.messages 数量: {len(agent.memory.messages)}")
        if last_assistant:
            print(f"✅ 最后一条 assistant 消息: {last_assistant.content[:300]}")
            if "广东工业大学" in last_assistant.content or "广工" in last_assistant.content:
                print("✅ ✅ 成功介绍了广东工业大学！")
            else:
                print("❌ 未介绍广东工业大学")

        # ========== 最终总结 ==========
        print("\n" + "=" * 80)
        print("【最终总结】")
        print("=" * 80)

        # 统计所有消息
        user_msgs = [msg for msg in agent.memory.messages
                     if (hasattr(msg, 'role') and hasattr(msg.role, 'value') and msg.role.value == 'user')
                     or (hasattr(msg, 'role') and str(msg.role) == 'user')]
        assistant_msgs = [msg for msg in agent.memory.messages
                         if (hasattr(msg, 'role') and hasattr(msg.role, 'value') and msg.role.value == 'assistant')
                         or (hasattr(msg, 'role') and str(msg.role) == 'assistant')]
        tool_msgs = [msg for msg in agent.memory.messages
                    if (hasattr(msg, 'role') and hasattr(msg.role, 'value') and msg.role.value == 'tool')
                    or (hasattr(msg, 'role') and str(msg.role) == 'tool')]

        print(f"总消息数: {len(agent.memory.messages)}")
        print(f"  - User 消息: {len(user_msgs)}")
        print(f"  - Assistant 消息: {len(assistant_msgs)}")
        print(f"  - Tool 消息: {len(tool_msgs)}")

        # 检查 tool 消息的 tool_call_id 匹配
        assistant_with_tool_calls = [msg for msg in assistant_msgs if msg.tool_calls]
        print(f"\nAssistant with tool_calls: {len(assistant_with_tool_calls)}")

        matched_count = 0
        for asst_msg in assistant_with_tool_calls:
            for tc in asst_msg.tool_calls:
                tc_id = tc.id if hasattr(tc, 'id') else ''
                matching_tool = [tm for tm in tool_msgs if tm.tool_call_id == tc_id]
                if matching_tool:
                    matched_count += 1

        print(f"Tool call ID 匹配: {matched_count}/{sum(len(msg.tool_calls) for msg in assistant_with_tool_calls)}")

        print("\n✅ 测试完成！")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_flow())

