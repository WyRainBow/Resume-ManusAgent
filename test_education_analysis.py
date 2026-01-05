"""
测试教育经历分析流程

测试步骤：
1. 创建 Manus agent
2. 发送消息："分析一下教育经历 简历/Users/wy770/Resume_OpenMauns/OpenManus/app/docs/韦宇_简历.md"
3. 验证：
   - 步骤1：调用 cv_reader_agent 读取简历
   - 步骤2：调用 education_analyzer 分析教育经历
   - 输出完整的教育经历分析结果
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.agent.manus import Manus
from app.logger import logger
from app.tool.resume_data_store import ResumeDataStore


async def test_education_analysis():
    """测试教育经历分析流程"""
    print("=" * 80)
    print("开始测试：教育经历分析流程")
    print("=" * 80)

    # 清空之前的简历数据（模拟刷新前端页面）
    ResumeDataStore.set_data(None)
    print("\n[初始化] 已清空之前的简历数据")

    # 创建 Manus agent
    print("\n[步骤 0] 创建 Manus agent...")
    agent = await Manus.create()

    # 测试消息
    test_message = "分析一下教育经历 简历/Users/wy770/Resume_OpenMauns/OpenManus/app/docs/韦宇_简历.md"
    print(f"\n[测试消息] {test_message}")
    print("\n" + "=" * 80)
    print("预期行为：")
    print("  1. 调用 cv_reader_agent 读取简历")
    print("  2. 调用 education_analyzer 分析教育经历")
    print("  3. 输出完整的教育经历分析结果")
    print("=" * 80 + "\n")

    try:
        # 运行 agent 处理消息
        print("[开始执行] Agent 开始处理消息...\n")
        result = await agent.run(test_message)

        print("\n" + "=" * 80)
        print("[执行完成] Agent 处理完成")
        print("=" * 80)
        print(f"\n最终结果:\n{result}")

        # 验证简历数据是否已加载
        resume_data = ResumeDataStore.get_data()
        if resume_data:
            print("\n[验证] ✓ 简历数据已成功加载到 ResumeDataStore")
            education = resume_data.get("education", [])
            if education:
                print(f"      ✓ 教育经历数据存在，共 {len(education)} 条")
            else:
                print("      ⚠ 教育经历数据为空")
        else:
            print("\n[验证] ✗ 简历数据未加载到 ResumeDataStore")

    except Exception as e:
        print(f"\n[错误] 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("\n[清理] 清理 agent 资源...")
        await agent.cleanup()
        print("[完成] 测试结束")


if __name__ == "__main__":
    asyncio.run(test_education_analysis())

