#!/usr/bin/env python3
"""
错误处理验证脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.agent.utils.path_generator import PathGenerator
from app.agent.delegation_strategy import AgentDelegationStrategy
from app.memory.conversation_state import Intent


def test_path_generator_error_handling():
    """测试 PathGenerator 错误处理"""
    print("\n=== 测试 PathGenerator 错误处理 ===")

    # 测试无效模块名称
    path = PathGenerator.generate_path("invalid_module", {}, {})
    assert path is None, "无效模块应返回 None"
    print("✓ 无效模块名称处理正确")

    # 测试空 resume_data
    path = PathGenerator.generate_path("work_experience", {"id": "test"}, {})
    assert path == "experience", "空数据时应返回基础路径"
    print("✓ 空 resume_data 处理正确")

    # 测试无效路径验证
    resume_data = {"experience": []}
    invalid_paths = [
        "nonexistent.path",
        "experience[999].details",  # 索引越界
        "experience.invalid",  # 无效字段
    ]

    for invalid_path in invalid_paths:
        is_valid = PathGenerator.validate_path(invalid_path, resume_data)
        assert not is_valid, f"无效路径 {invalid_path} 应返回 False"
    print("✓ 无效路径验证正确")

    return True


def test_delegation_strategy_error_handling():
    """测试 AgentDelegationStrategy 错误处理"""
    print("\n=== 测试 AgentDelegationStrategy 错误处理 ===")

    # 测试无效意图
    strategy = AgentDelegationStrategy.resolve(Intent.UNKNOWN)
    assert strategy is None, "无效意图应返回 None"
    print("✓ 无效意图处理正确")

    # 测试无效 section
    strategy = AgentDelegationStrategy.resolve(Intent.OPTIMIZE_SECTION, section="无效模块")
    assert strategy is not None, "策略不应为 None（即使 section 无效）"
    # section 无效时，analyzers 应为空列表或模板字符串
    print("✓ 无效 section 处理正确")

    return True


def test_resume_optimizer_error_handling():
    """测试 ResumeOptimizer 错误处理"""
    print("\n=== 测试 ResumeOptimizer 错误处理 ===")

    from app.agent.resume_optimizer import ResumeOptimizerAgent

    optimizer = ResumeOptimizerAgent()

    # 测试空分析结果
    suggestions = optimizer.generate_suggestions([], resume_data={})
    assert len(suggestions) == 0, "空分析结果应返回空列表"
    print("✓ 空分析结果处理正确")

    # 测试 None resume_data
    mock_result = {
        "module": "work_experience",
        "issues": [{"id": "test", "problem": "测试问题"}],
    }
    suggestions = optimizer.generate_suggestions([mock_result], resume_data=None)
    assert len(suggestions) > 0, "即使 resume_data 为 None，也应生成建议"
    # 但 apply_path 可能为 None
    if suggestions:
        print(f"✓ None resume_data 处理正确（生成了 {len(suggestions)} 条建议）")

    # 测试缺少 apply_path 的情况
    mock_result_no_path = {
        "module": "work_experience",
        "issues": [{"id": "test", "problem": "测试问题"}],  # 没有 apply_path
    }
    resume_data = {"experience": [{"details": ""}]}
    suggestions = optimizer.generate_suggestions([mock_result_no_path], resume_data=resume_data)
    assert len(suggestions) > 0, "应生成建议"
    # PathGenerator 应该能够生成路径
    if suggestions and suggestions[0].get("apply_path"):
        print(f"✓ 缺少 apply_path 时自动生成路径: {suggestions[0]['apply_path']}")

    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("错误处理验证")
    print("=" * 60)

    results = []

    try:
        results.append(("PathGenerator 错误处理", test_path_generator_error_handling()))
    except Exception as e:
        print(f"✗ PathGenerator 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("PathGenerator 错误处理", False))

    try:
        results.append(("AgentDelegationStrategy 错误处理", test_delegation_strategy_error_handling()))
    except Exception as e:
        print(f"✗ AgentDelegationStrategy 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("AgentDelegationStrategy 错误处理", False))

    try:
        results.append(("ResumeOptimizer 错误处理", test_resume_optimizer_error_handling()))
    except Exception as e:
        print(f"✗ ResumeOptimizer 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("ResumeOptimizer 错误处理", False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("错误处理验证结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✓ 所有错误处理测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
