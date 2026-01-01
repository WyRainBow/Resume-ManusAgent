"""
CVReader Agent 测试脚本

测试简历阅读功能
"""
import asyncio
from app.agent.cv_reader import CVReader


# 测试用的简历数据
SAMPLE_RESUME = {
    "id": "test-001",
    "title": "前端工程师简历",
    "basic": {
        "name": "张三",
        "title": "高级前端工程师",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "location": "北京",
        "employementStatus": "在职，看机会"
    },
    "education": [
        {
            "id": "edu-1",
            "school": "北京大学",
            "degree": "学士",
            "major": "计算机科学与技术",
            "startDate": "2018-09",
            "endDate": "2022-06",
            "gpa": "3.8/4.0",
            "description": "<p>主修课程：数据结构、算法、计算机网络、操作系统</p>"
        }
    ],
    "experience": [
        {
            "id": "exp-1",
            "company": "阿里巴巴",
            "position": "前端工程师",
            "date": "2022-07 - 至今",
            "details": "<p>负责淘宝前端页面开发，使用 React 和 TypeScript</p><p>优化页面性能，提升用户体验</p>"
        }
    ],
    "projects": [
        {
            "id": "proj-1",
            "name": "开源组件库",
            "role": "核心开发者",
            "date": "2023-01 - 2023-12",
            "description": "<p>开发了一套 React 组件库，已在 GitHub 获得 1000+ stars</p>",
            "link": "https://github.com/example/ui-lib"
        }
    ],
    "openSource": [
        {
            "id": "os-1",
            "name": "Vue.js",
            "role": "贡献者",
            "description": "<p>修复了多个 bug，参与了新功能开发</p>",
            "repo": "https://github.com/vuejs/core"
        }
    ],
    "awards": [
        {
            "id": "award-1",
            "title": "优秀员工",
            "issuer": "阿里巴巴",
            "date": "2023-12"
        }
    ],
    "skillContent": "<p><strong>前端技能：</strong>React, Vue, TypeScript, HTML/CSS</p><p><strong>后端技能：</strong>Node.js, Python</p>",
    "customData": {},
    "menuSections": [],
    "draggingProjectId": None,
    "globalSettings": {},
    "activeSection": "basic"
}


async def test_cv_reader():
    """测试 CVReader Agent"""
    print("=" * 60)
    print("CVReader Agent 测试")
    print("=" * 60)

    # 创建 Agent
    agent = CVReader()

    # 加载简历
    print("\n1. 加载简历数据...")
    summary = agent.load_resume(SAMPLE_RESUME)
    print(summary)

    # 测试工具直接调用
    print("\n2. 测试 ReadCVContext 工具...")
    for tool in agent.available_tools.tools:
        if tool.__class__.__name__ == "ReadCVContext":
            tool.set_resume_data(SAMPLE_RESUME)
            result = await tool.execute(section="all")
            print(result[:500] + "..." if len(result) > 500 else result)
            break

    print("\n3. 测试对话功能...")
    print("问: 这位候选人的工作经历是什么?")
    # 注意：实际对话需要配置 LLM API
    # response = await agent.chat("这位候选人的工作经历是什么?")
    # print(f"答: {response}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_cv_reader())
