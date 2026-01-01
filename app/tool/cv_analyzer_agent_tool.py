"""
CVAnalyzer Agent Tool - 将 CVAnalyzer Agent 包装成 Manus 可调用的工具

参考 CVReaderAgentTool 的集成方式，这个工具内部使用 CVAnalyzer Agent 来处理简历深度分析任务。
"""

from typing import Optional
from app.tool.base import BaseTool, ToolResult


class CVAnalyzerAgentTool(BaseTool):
    """CVAnalyzer Agent 工具

    这是一个特殊的工具，它内部使用 CVAnalyzer Agent 来处理简历深度分析任务。
    Manus 可以委托简历分析任务给这个工具，CVAnalyzer 会以 Agent 的方式处理。

    使用场景：
    - 用户要求分析简历质量（深度分析）
    - 用户要求找出简历需要优化的地方
    - 用户要求使用 STAR 法则分析经历
    """

    name: str = "cv_analyzer_agent"
    description: str = """Delegate CV/Resume deep analysis to the CVAnalyzer Agent.

Use this tool when the user asks to:
- "分析我的简历" (analyze my resume)
- "帮我分析一下简历" (help me analyze my resume)
- "找出简历需要优化的地方" (find areas that need improvement)
- "深度分析简历" (deeply analyze the resume)

The CVAnalyzer Agent will:
1. Check completeness (empty/missing fields)
2. Analyze content quality using STAR methodology
3. Identify skills that need better description
4. Provide structured optimization suggestions

此工具用于深度分析求职者的简历内容质量。"""

    parameters: dict = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The analysis question or request"
            }
        },
        "required": ["question"]
    }

    # 全局简历数据（与 CVReaderAgentTool 共享）
    _global_resume_data: Optional[dict] = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def set_resume_data(cls, resume_data: dict):
        """设置全局简历数据"""
        cls._global_resume_data = resume_data

    @classmethod
    def get_resume_data(cls) -> Optional[dict]:
        """获取全局简历数据"""
        return cls._global_resume_data

    async def execute(self, question: str) -> ToolResult:
        """执行简历深度分析

        内部创建 CVAnalyzer Agent 并运行它来处理分析任务
        """
        if not CVAnalyzerAgentTool._global_resume_data:
            return ToolResult(
                output="No resume data loaded. Please use load_resume_data tool first."
            )

        try:
            # 延迟导入避免循环依赖
            from app.agent.cv_analyzer import CVAnalyzer

            # 创建 CVAnalyzer Agent 实例
            cv_analyzer = CVAnalyzer()

            # 加载简历数据
            cv_analyzer.load_resume(CVAnalyzerAgentTool._global_resume_data)

            # 运行 CVAnalyzer Agent 处理问题
            result = await cv_analyzer.chat(question)

            # 强制追加固定的引导语（确保无论AI输出什么，都有正确的引导）
            guidance = self._generate_guidance(CVAnalyzerAgentTool._global_resume_data)

            # 如果AI的输出中没有包含引导语，则追加
            if "我建议先从【" not in result:
                result = result + "\n\n" + guidance

            return ToolResult(output=result)

        except Exception as e:
            return ToolResult(error=f"CVAnalyzer Agent error: {str(e)}")

    def _generate_guidance(self, resume_data: dict) -> str:
        """根据简历状态生成优化引导

        Returns:
            固定格式的引导语
        """
        basic = resume_data.get("basic", {})
        summary = basic.get("summary", "")

        # 检查个人总结
        if not summary or not summary.strip():
            return """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

不过，从HR的角度来看，您的简历还有一些可以优化的地方：

个人总结为空 - 这会让HR无法快速了解您的核心优势

我建议先从【个人总结】开始，让HR对您有一个初步的深刻印象。可以吗？"""

        # 检查工作经历
        experience = resume_data.get("experience", [])
        if experience:
            for exp in experience:
                details = exp.get("details", "")
                if not details or not details.strip():
                    return """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

不过，从HR的角度来看，您的简历还有一些可以优化的地方：

工作经历描述不完整 - 您有大厂经历，但没有展示具体成果

我建议先从【工作经历】开始，这是HR最关注的部分。可以吗？"""

        # 检查技能
        skill_content = resume_data.get("skillContent", "")
        if skill_content and ("熟悉" in skill_content or "了解" in skill_content):
            return """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

不过，从HR的角度来看，您的简历还有一些可以优化的地方：

技能描述用"熟悉"、"了解"太笼统 - HR无法判断您的实际水平

我建议先从【技能描述】开始，突出您的核心竞争力。可以吗？"""

        # 默认建议
        return """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

不过，从HR的角度来看，您的简历还有一些可以优化的地方：

我建议先从【个人总结】开始，让HR对您有一个初步的深刻印象。可以吗？"""
