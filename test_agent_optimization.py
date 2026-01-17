#!/usr/bin/env python3
"""
Agent 架构优化功能验证脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.memory.conversation_state import ConversationStateManager, Intent
from app.agent.delegation_strategy import AgentDelegationStrategy
from app.agent.utils.path_generator import PathGenerator


def test_intent_detection():
    """测试意图识别"""
    print("\n=== 测试意图识别 ===")

    manager = ConversationStateManager(session_id="test")

    test_cases = [
        ("分析我的简历", Intent.ANALYZE_RESUME, None),
        ("优化工作经历", Intent.OPTIMIZE_SECTION, "工作经历"),
        ("全面优化简历", Intent.FULL_OPTIMIZE, None),
    ]

    all_passed = True
    for text, expected_intent, expected_section in test_cases:
        intent, section = manager._detect_agent_intent(text)
        passed = intent == expected_intent and section == expected_section
        status = "✓" if passed else "✗"
        print(f"{status} '{text}' → intent={intent}, section={section}")
        if not passed:
            print(f"  预期: intent={expected_intent}, section={expected_section}")
            all_passed = False

    return all_passed


def test_delegation_strategy():
    """测试 Agent 委托策略"""
    print("\n=== 测试 Agent 委托策略 ===")

    # 测试 ANALYZE_RESUME
    strategy = AgentDelegationStrategy.resolve(Intent.ANALYZE_RESUME)
    assert strategy is not None, "ANALYZE_RESUME 策略不应为 None"
    assert "analyzers" in strategy, "策略应包含 analyzers"
    assert len(strategy["analyzers"]) == 3, "应包含 3 个分析器"
    assert "work_experience_analyzer" in strategy["analyzers"], "应包含 work_experience_analyzer"
    assert "education_analyzer_agent" in strategy["analyzers"], "应包含 education_analyzer_agent"
    assert "skills_analyzer" in strategy["analyzers"], "应包含 skills_analyzer"
    print("✓ ANALYZE_RESUME 策略正确")

    # 测试 OPTIMIZE_SECTION
    strategy = AgentDelegationStrategy.resolve(Intent.OPTIMIZE_SECTION, section="工作经历")
    assert strategy is not None, "OPTIMIZE_SECTION 策略不应为 None"
    assert "analyzers" in strategy, "策略应包含 analyzers"
    assert len(strategy["analyzers"]) == 1, "应包含 1 个分析器"
    assert strategy["analyzers"][0] == "work_experience_analyzer", "应为 work_experience_analyzer"
    assert "optimizer" in strategy, "策略应包含 optimizer"
    assert strategy["optimizer"] == "resume_optimizer", "应为 resume_optimizer"
    print("✓ OPTIMIZE_SECTION 策略正确")

    # 测试 FULL_OPTIMIZE
    strategy = AgentDelegationStrategy.resolve(Intent.FULL_OPTIMIZE)
    assert strategy is not None, "FULL_OPTIMIZE 策略不应为 None"
    assert "analyzers" in strategy, "策略应包含 analyzers"
    assert "optimizer" in strategy, "策略应包含 optimizer"
    assert strategy["optimizer"] == "resume_optimizer", "应为 resume_optimizer"
    print("✓ FULL_OPTIMIZE 策略正确")

    return True


def test_path_generator():
    """测试 PathGenerator"""
    print("\n=== 测试 PathGenerator ===")

    # 测试工作经历路径生成
    resume_data = {
        "experience": [
            {"company": "公司A", "position": "工程师", "details": "工作内容"},
            {"company": "公司B", "position": "高级工程师", "details": ""},
        ],
        "education": [
            {"school": "大学A", "description": "学习内容"},
        ],
        "skillContent": "Python, Java",
    }

    # 测试 work_experience
    issue = {"id": "work-missing-detail-0"}
    path = PathGenerator.generate_path("work_experience", issue, resume_data)
    assert path == "experience[0].details", f"应为 experience[0].details，实际为 {path}"
    assert PathGenerator.validate_path(path, resume_data), "路径应有效"
    print(f"✓ work_experience 路径生成: {path}")

    # 测试 education
    path = PathGenerator.generate_path("education", {}, resume_data)
    assert path == "education[0].description", f"应为 education[0].description，实际为 {path}"
    assert PathGenerator.validate_path(path, resume_data), "路径应有效"
    print(f"✓ education 路径生成: {path}")

    # 测试 skills
    path = PathGenerator.generate_path("skills", {}, resume_data)
    assert path == "skillContent", f"应为 skillContent，实际为 {path}"
    assert PathGenerator.validate_path(path, resume_data), "路径应有效"
    print(f"✓ skills 路径生成: {path}")

    # 测试无效路径
    invalid_path = "nonexistent.path"
    assert not PathGenerator.validate_path(invalid_path, resume_data), "无效路径应返回 False"
    print("✓ 路径验证正确")

    # 测试空 resume_data
    path = PathGenerator.generate_path("work_experience", {}, {})
    assert path == "experience", f"空数据时应返回基础路径，实际为 {path}"
    print(f"✓ 空数据路径生成: {path}")

    return True


def main():
    """主测试函数"""
    print("=" * 50)
    print("Agent 架构优化功能验证")
    print("=" * 50)

    results = []

    try:
        results.append(("意图识别", test_intent_detection()))
    except Exception as e:
        print(f"✗ 意图识别测试失败: {e}")
        results.append(("意图识别", False))

    try:
        results.append(("Agent 委托策略", test_delegation_strategy()))
    except Exception as e:
        print(f"✗ Agent 委托策略测试失败: {e}")
        results.append(("Agent 委托策略", False))

    try:
        results.append(("PathGenerator", test_path_generator()))
    except Exception as e:
        print(f"✗ PathGenerator 测试失败: {e}")
        results.append(("PathGenerator", False))

    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("✓ 所有单元测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
