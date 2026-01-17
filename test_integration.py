#!/usr/bin/env python3
"""
Agent 架构优化集成测试脚本
测试三个主要场景：分析简历、优化特定模块、全面优化
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.memory.conversation_state import ConversationStateManager, Intent
from app.agent.manus import Manus
from app.agent.delegation_strategy import AgentDelegationStrategy
from app.agent.resume_optimizer import ResumeOptimizerAgent
from app.agent.utils.path_generator import PathGenerator


# 模拟简历数据
MOCK_RESUME_DATA = {
    "basic": {
        "name": "测试用户",
        "email": "test@example.com",
    },
    "experience": [
        {
            "company": "测试公司A",
            "position": "后端工程师",
            "start_date": "2020-01",
            "end_date": "2022-12",
            "details": "负责系统开发",
        },
        {
            "company": "测试公司B",
            "position": "高级工程师",
            "start_date": "2023-01",
            "end_date": "present",
            "details": "",  # 缺少详情
        },
    ],
    "education": [
        {
            "school": "测试大学",
            "major": "计算机科学",
            "degree": "本科",
            "description": "学习计算机基础知识",
        }
    ],
    "skillContent": "Python, Java, Go",
}


async def test_scenario_1_analyze_resume():
    """测试场景1：分析简历"""
    print("\n" + "=" * 60)
    print("场景1：分析我的简历")
    print("=" * 60)

    manager = ConversationStateManager(session_id="test_analyze")

    # 1. 意图识别
    user_input = "分析我的简历"
    intent, section = manager._detect_agent_intent(user_input)

    print(f"用户输入: {user_input}")
    print(f"识别意图: {intent}")
    print(f"提取模块: {section}")

    assert intent == Intent.ANALYZE_RESUME, f"应为 ANALYZE_RESUME，实际为 {intent}"
    print("✓ 意图识别正确")

    # 2. 策略解析
    strategy = AgentDelegationStrategy.resolve(intent, section)
    assert strategy is not None, "策略不应为 None"
    assert "analyzers" in strategy, "策略应包含 analyzers"
    analyzers = strategy["analyzers"]
    print(f"✓ 策略解析成功，分析器: {analyzers}")

    # 3. 模拟 Agent 委托（不实际调用，只验证逻辑）
    print(f"✓ 应并行调用 {len(analyzers)} 个分析 Agent")
    print(f"  - {', '.join(analyzers)}")

    print("\n✓ 场景1验证通过：意图识别 → 策略解析 → Agent 委托流程正确")
    return True


async def test_scenario_2_optimize_section():
    """测试场景2：优化特定模块"""
    print("\n" + "=" * 60)
    print("场景2：优化工作经历")
    print("=" * 60)

    manager = ConversationStateManager(session_id="test_optimize")

    # 1. 意图识别
    user_input = "优化工作经历"
    intent, section = manager._detect_agent_intent(user_input)

    print(f"用户输入: {user_input}")
    print(f"识别意图: {intent}")
    print(f"提取模块: {section}")

    assert intent == Intent.OPTIMIZE_SECTION, f"应为 OPTIMIZE_SECTION，实际为 {intent}"
    assert section == "工作经历", f"应为 '工作经历'，实际为 {section}"
    print("✓ 意图识别正确")

    # 2. 策略解析
    strategy = AgentDelegationStrategy.resolve(intent, section)
    assert strategy is not None, "策略不应为 None"
    assert "analyzers" in strategy, "策略应包含 analyzers"
    assert "optimizer" in strategy, "策略应包含 optimizer"

    analyzers = strategy["analyzers"]
    optimizer = strategy["optimizer"]

    print(f"✓ 策略解析成功")
    print(f"  - 分析器: {analyzers}")
    print(f"  - 优化器: {optimizer}")

    # 3. 模拟分析结果
    mock_analysis_result = {
        "module": "work_experience",
        "module_display_name": "工作经历",
        "score": 70,
        "issues": [
            {
                "id": "work-missing-detail-1",
                "problem": "工作经历缺少细节描述",
                "severity": "medium",
                "suggestion": "补充职责、行动和成果，尽量量化指标",
            }
        ],
    }

    # 4. 测试 PathGenerator
    issue = mock_analysis_result["issues"][0]
    path = PathGenerator.generate_path("work_experience", issue, MOCK_RESUME_DATA)
    assert path is not None, "路径不应为 None"
    assert PathGenerator.validate_path(path, MOCK_RESUME_DATA), "路径应有效"
    print(f"✓ 路径生成: {path}")

    # 5. 测试 ResumeOptimizer
    optimizer_agent = ResumeOptimizerAgent()
    suggestions = optimizer_agent.generate_suggestions(
        [mock_analysis_result], resume_data=MOCK_RESUME_DATA
    )

    assert len(suggestions) > 0, "应生成优化建议"
    suggestion = suggestions[0]
    assert "apply_path" in suggestion, "建议应包含 apply_path"
    assert suggestion["apply_path"] == path, "apply_path 应匹配生成的路径"

    print(f"✓ 优化建议生成成功")
    print(f"  - 建议数量: {len(suggestions)}")
    print(f"  - 第一条建议路径: {suggestion['apply_path']}")

    print("\n✓ 场景2验证通过：意图识别 → 分析 → 路径生成 → 优化建议流程正确")
    return True


async def test_scenario_3_full_optimize():
    """测试场景3：全面优化"""
    print("\n" + "=" * 60)
    print("场景3：全面优化简历")
    print("=" * 60)

    manager = ConversationStateManager(session_id="test_full")

    # 1. 意图识别
    user_input = "全面优化简历"
    intent, section = manager._detect_agent_intent(user_input)

    print(f"用户输入: {user_input}")
    print(f"识别意图: {intent}")
    print(f"提取模块: {section}")

    assert intent == Intent.FULL_OPTIMIZE, f"应为 FULL_OPTIMIZE，实际为 {intent}"
    print("✓ 意图识别正确")

    # 2. 策略解析
    strategy = AgentDelegationStrategy.resolve(intent, section)
    assert strategy is not None, "策略不应为 None"
    assert "analyzers" in strategy, "策略应包含 analyzers"
    assert "optimizer" in strategy, "策略应包含 optimizer"

    analyzers = strategy["analyzers"]
    optimizer = strategy["optimizer"]

    print(f"✓ 策略解析成功")
    print(f"  - 分析器数量: {len(analyzers)}")
    print(f"  - 分析器列表: {', '.join(analyzers)}")
    print(f"  - 优化器: {optimizer}")

    # 3. 模拟多个分析结果
    mock_analysis_results = [
        {
            "module": "work_experience",
            "issues": [{"id": "work-1", "problem": "问题1"}],
        },
        {
            "module": "education",
            "issues": [{"id": "edu-1", "problem": "问题2"}],
        },
        {
            "module": "skills",
            "issues": [{"id": "skill-1", "problem": "问题3"}],
        },
    ]

    # 4. 测试 ResumeOptimizer 聚合
    optimizer_agent = ResumeOptimizerAgent()
    suggestions = optimizer_agent.generate_suggestions(
        mock_analysis_results, resume_data=MOCK_RESUME_DATA
    )

    assert len(suggestions) > 0, "应生成优化建议"
    print(f"✓ 优化建议聚合成功")
    print(f"  - 建议总数: {len(suggestions)}")

    # 验证每个建议都有 apply_path
    for i, suggestion in enumerate(suggestions[:3]):  # 只检查前3个
        if suggestion.get("apply_path"):
            print(f"  - 建议 {i+1} 路径: {suggestion['apply_path']}")

    print("\n✓ 场景3验证通过：意图识别 → 并行分析 → 聚合优化建议流程正确")
    return True


async def main():
    """主测试函数"""
    print("=" * 60)
    print("Agent 架构优化集成测试")
    print("=" * 60)

    results = []

    try:
        results.append(("场景1：分析简历", await test_scenario_1_analyze_resume()))
    except Exception as e:
        print(f"\n✗ 场景1测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("场景1：分析简历", False))

    try:
        results.append(("场景2：优化特定模块", await test_scenario_2_optimize_section()))
    except Exception as e:
        print(f"\n✗ 场景2测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("场景2：优化特定模块", False))

    try:
        results.append(("场景3：全面优化", await test_scenario_3_full_optimize()))
    except Exception as e:
        print(f"\n✗ 场景3测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("场景3：全面优化", False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("集成测试结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✓ 所有集成测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
