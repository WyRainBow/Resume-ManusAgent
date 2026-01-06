#!/usr/bin/env python3
"""
Agent 场景测试
测试各种对话场景，验证自动终止和上下文传递机制
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent.manus import Manus
from app.schema import Message, AgentState
from app.logger import define_log_level

logger = define_log_level(print_level="INFO", logfile_level="DEBUG")


async def run_scenario(agent: Manus, scenario_name: str, user_input: str, expected_keywords: list = None):
    """运行单个场景并验证结果"""
    print(f"\n{'=' * 60}")
    print(f"【场景】{scenario_name}")
    print(f"【输入】{user_input}")
    print(f"{'=' * 60}")

    # 添加用户消息
    agent.memory.add_message(Message.user_message(user_input))

    # 重置状态
    agent.state = AgentState.RUNNING

    # 执行 step
    max_steps = 5
    steps_taken = 0

    for step in range(max_steps):
        steps_taken += 1
        result = await agent.step()
        print(f"  Step {step + 1}: {result[:100] if result else 'No output'}...")

        if agent.state.value == "FINISHED":
            break

    # 获取最后一条 assistant 消息
    last_assistant = None
    for msg in reversed(agent.memory.messages):
        role_val = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
        if role_val == 'assistant' and msg.content:
            last_assistant = msg.content
            break

    # 验证结果
    success = True
    if expected_keywords:
        for keyword in expected_keywords:
            if keyword not in (last_assistant or ""):
                print(f"  ❌ 未找到关键词: {keyword}")
                success = False

    print(f"\n【结果】步数: {steps_taken}, 消息数: {len(agent.memory.messages)}")
    if last_assistant:
        print(f"【回答】{last_assistant[:200]}...")

    if success and steps_taken <= 2:
        print(f"✅ 场景通过！")
    else:
        print(f"⚠️ 场景需要关注")

    return {
        "scenario": scenario_name,
        "steps": steps_taken,
        "messages": len(agent.memory.messages),
        "success": success,
        "response": last_assistant[:200] if last_assistant else None
    }


async def main():
    """运行所有测试场景"""
    print("=" * 80)
    print("Agent 场景测试")
    print("=" * 80)

    agent = await Manus.create()
    resume_path = "/Users/wy770/Resume_OpenMauns/OpenManus/app/docs/韦宇_简历.md"

    results = []

    try:
        # 场景1: 加载简历
        result = await run_scenario(
            agent,
            "加载简历",
            f"请加载简历 {resume_path}",
            ["简历", "加载"]
        )
        results.append(result)

        # 场景2: 基于简历的问答
        result = await run_scenario(
            agent,
            "询问个人信息",
            "我叫什么名字？",
            ["韦宇"]
        )
        results.append(result)

        # 场景3: 通用知识问答
        result = await run_scenario(
            agent,
            "通用知识问答",
            "Python 是什么语言？",
            ["Python"]
        )
        results.append(result)

        # 场景4: 简历相关问答
        result = await run_scenario(
            agent,
            "技能询问",
            "我的简历中有哪些技能？",
            []  # 不强制要求关键词
        )
        results.append(result)

        # 场景5: 问候
        result = await run_scenario(
            agent,
            "问候",
            "你好！",
            ["你好", "OpenManus"]
        )
        results.append(result)

        # 总结
        print("\n" + "=" * 80)
        print("【测试总结】")
        print("=" * 80)

        total_steps = sum(r["steps"] for r in results)
        total_messages = results[-1]["messages"]  # 最终消息数
        all_passed = all(r["success"] and r["steps"] <= 2 for r in results)

        for r in results:
            status = "✅" if r["success"] and r["steps"] <= 2 else "⚠️"
            print(f"  {status} {r['scenario']}: {r['steps']}步, {r['messages']}消息")

        print(f"\n总步数: {total_steps}")
        print(f"最终消息数: {total_messages}")
        print(f"整体结果: {'✅ 全部通过' if all_passed else '⚠️ 需要优化'}")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

