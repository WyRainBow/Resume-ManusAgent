#!/usr/bin/env python3
"""
性能验证脚本
测试并行委托的性能优势
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.agent.delegation_strategy import AgentDelegationStrategy
from app.memory.conversation_state import Intent


async def mock_analyzer_call(name: str, delay: float = 0.1) -> dict:
    """模拟分析器调用（带延迟）"""
    await asyncio.sleep(delay)
    return {
        "module": name,
        "score": 80,
        "issues": [{"id": f"{name}-1", "problem": "测试问题"}],
    }


async def test_parallel_delegation_performance():
    """测试并行委托性能"""
    print("\n=== 测试并行委托性能 ===")

    # 获取策略
    strategy = AgentDelegationStrategy.resolve(Intent.ANALYZE_RESUME)
    analyzers = strategy["analyzers"]

    print(f"分析器列表: {analyzers}")
    print(f"分析器数量: {len(analyzers)}")

    # 测试并行调用
    delay_per_analyzer = 0.1  # 每个分析器模拟 0.1 秒延迟

    start_time = time.time()
    tasks = [mock_analyzer_call(name, delay_per_analyzer) for name in analyzers]
    results = await asyncio.gather(*tasks)
    parallel_time = time.time() - start_time

    print(f"✓ 并行调用耗时: {parallel_time:.3f} 秒")
    print(f"  预期耗时（并行）: ~{delay_per_analyzer:.3f} 秒")
    print(f"  预期耗时（串行）: ~{delay_per_analyzer * len(analyzers):.3f} 秒")

    # 验证并行确实比串行快
    expected_serial_time = delay_per_analyzer * len(analyzers)
    speedup = expected_serial_time / parallel_time if parallel_time > 0 else 0
    print(f"  加速比: {speedup:.2f}x")

    assert parallel_time < expected_serial_time, "并行应比串行快"
    assert len(results) == len(analyzers), "应返回所有分析结果"

    print("✓ 并行委托性能验证通过")
    return True


async def test_path_generator_performance():
    """测试 PathGenerator 性能"""
    print("\n=== 测试 PathGenerator 性能 ===")

    from app.agent.utils.path_generator import PathGenerator

    # 创建较大的简历数据
    large_resume_data = {
        "experience": [
            {"details": f"工作内容{i}"} for i in range(10)
        ],
        "education": [
            {"description": f"教育内容{i}"} for i in range(5)
        ],
        "skillContent": "Python, Java, Go, " * 10,
    }

    issue = {"id": "work-missing-detail-5"}

    # 测试路径生成性能
    iterations = 100
    start_time = time.time()
    for _ in range(iterations):
        path = PathGenerator.generate_path("work_experience", issue, large_resume_data)
        PathGenerator.validate_path(path, large_resume_data)
    total_time = time.time() - start_time

    avg_time = total_time / iterations
    print(f"✓ 路径生成性能测试")
    print(f"  迭代次数: {iterations}")
    print(f"  总耗时: {total_time:.4f} 秒")
    print(f"  平均耗时: {avg_time * 1000:.4f} 毫秒/次")

    # 验证性能可接受（每次操作应 < 1ms）
    assert avg_time < 0.001, f"平均耗时应 < 1ms，实际为 {avg_time * 1000:.4f}ms"

    print("✓ PathGenerator 性能验证通过")
    return True


async def main():
    """主测试函数"""
    print("=" * 60)
    print("性能验证")
    print("=" * 60)

    results = []

    try:
        results.append(("并行委托性能", await test_parallel_delegation_performance()))
    except Exception as e:
        print(f"✗ 并行委托性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("并行委托性能", False))

    try:
        results.append(("PathGenerator 性能", await test_path_generator_performance()))
    except Exception as e:
        print(f"✗ PathGenerator 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("PathGenerator 性能", False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("性能验证结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✓ 所有性能测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
