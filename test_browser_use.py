"""
测试 browser-use 工具：导航到百度并进行基本操作
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.tool.browser_use_tool import BrowserUseTool


async def test_baidu_navigation():
    """测试导航到百度并进行基本操作"""
    print("=" * 60)
    print("开始测试 browser-use 工具")
    print("=" * 60)

    # 创建浏览器工具实例
    browser_tool = BrowserUseTool()

    try:
        # 1. 导航到百度
        print("\n[步骤 1] 导航到百度...")
        result = await browser_tool.execute(action="go_to_url", url="https://www.baidu.com")
        print(f"结果: {result.output if result.output else result.error}")

        if result.error:
            print(f"错误: {result.error}")
            return

        # 等待页面加载
        print("\n[步骤 2] 等待页面加载...")
        await browser_tool.execute(action="wait", seconds=2)

        # 3. 获取当前页面状态（包含可交互元素）
        print("\n[步骤 3] 获取页面状态...")
        state_result = await browser_tool.get_current_state()

        if state_result.error:
            print(f"获取状态错误: {state_result.error}")
        else:
            state_info = json.loads(state_result.output)
            print(f"当前URL: {state_info.get('url')}")
            print(f"页面标题: {state_info.get('title')}")
            print(f"\n可交互元素预览（前500字符）:")
            elements = state_info.get('interactive_elements', '')
            print(elements[:500] if elements else "无元素信息")

        # 4. 尝试在搜索框中输入文本（需要先获取元素索引）
        # 注意：实际使用时需要根据 get_current_state 返回的元素索引来操作
        print("\n[步骤 4] 尝试输入搜索关键词...")
        print("提示: 要输入文本，需要先查看页面的交互元素列表，找到搜索框的索引")
        print("然后使用: browser_tool.execute(action='input_text', index=索引, text='搜索内容')")

        # 5. 等待一段时间以便观察浏览器窗口
        print("\n[步骤 5] 等待5秒，您可以在浏览器窗口中查看页面...")
        await browser_tool.execute(action="wait", seconds=5)

        print("\n测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("\n清理浏览器资源...")
        await browser_tool.cleanup()
        print("清理完成")


async def test_baidu_search():
    """测试在百度搜索（需要手动指定元素索引）"""
    print("=" * 60)
    print("开始测试百度搜索功能")
    print("=" * 60)

    browser_tool = BrowserUseTool()

    try:
        # 1. 导航到百度
        print("\n[步骤 1] 导航到百度...")
        result = await browser_tool.execute(action="go_to_url", url="https://www.baidu.com")
        print(f"结果: {result.output}")

        await browser_tool.execute(action="wait", seconds=2)

        # 2. 获取页面状态，找到搜索框的索引
        print("\n[步骤 2] 获取页面状态，查找搜索框...")
        state_result = await browser_tool.get_current_state()

        if state_result.error:
            print(f"错误: {state_result.error}")
            return

        state_info = json.loads(state_result.output)
        interactive_elements = state_info.get('interactive_elements', '')

        print("\n完整的交互元素列表:")
        print(interactive_elements)
        print("\n请根据上面的列表，找到搜索输入框的索引号")
        print("然后可以使用以下代码进行搜索：")
        print("  # 输入搜索关键词")
        print("  await browser_tool.execute(action='input_text', index=搜索框索引, text='Python')")
        print("  # 点击搜索按钮")
        print("  await browser_tool.execute(action='click_element', index=搜索按钮索引)")

        # 等待以便查看
        await browser_tool.execute(action="wait", seconds=10)

    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_tool.cleanup()


if __name__ == "__main__":
    # 运行基本导航测试
    asyncio.run(test_baidu_navigation())

    # 如果需要测试搜索功能，取消下面的注释
    # asyncio.run(test_baidu_search())

