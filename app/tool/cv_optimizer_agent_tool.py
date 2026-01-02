"""
CVOptimizer Agent Tool - 简历优化建议工具

直接分析简历并给出优化建议，不需要复杂的 Agent 流程
"""

from typing import Optional
from app.tool.base import BaseTool, ToolResult
from app.tool.resume_data_store import ResumeDataStore


class CVOptimizerAgentTool(BaseTool):
    """CVOptimizer Agent 工具

    分析简历内容并给出具体的优化建议。

    使用场景：
    - 用户说"开始优化"或"帮我优化简历"
    - 用户要求优化某个模块（个人总结、工作经历等）
    - 用户需要帮助生成简历内容
    """

    name: str = "cv_optimizer_agent"
    description: str = """Analyze resume and provide optimization suggestions.

Use this tool when the user wants to:
- Start optimizing their resume (开始优化 / 帮我优化简历)
- Improve a specific section (优化个人总结/工作经历/技能)
- Get help writing resume content (帮我写个人总结/帮我写工作经历)

此工具用于分析简历并给出优化建议。"""

    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "优化动作，可选值：'start_optimization'（开始优化）、'optimize_section'（优化指定模块）"
            },
            "section": {
                "type": "string",
                "description": "要优化的模块，可选值：'工作经历'、'个人总结'、'技能'、'项目经历'"
            },
            "question": {
                "type": "string",
                "description": "具体的优化请求或问题，或者用户对优化问题的回答"
            },
            "answer": {
                "type": "string",
                "description": "用户对优化问题的回答（用于生成优化后的内容）"
            }
        },
        "required": ["action"]
    }

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def set_resume_data(cls, resume_data: dict):
        """设置全局简历数据（兼容旧接口）"""
        ResumeDataStore.set_data(resume_data)

    @classmethod
    def get_resume_data(cls) -> Optional[dict]:
        """获取全局简历数据（兼容旧接口）"""
        return ResumeDataStore.get_data()

    async def execute(self, action: str = "", section: str = "", question: str = "", answer: str = "") -> ToolResult:
        """执行简历优化分析"""
        resume_data = ResumeDataStore.get_data()
        if not resume_data:
            return ToolResult(
                output="No resume data loaded. Please use cv_reader_agent tool first to read resume data."
            )

        try:
            # 根据 action 和 section 生成优化建议
            if action == "start_optimization":
                result = self._suggest_optimization_plan(resume_data)
            elif section == "工作经历":
                # 如果提供了答案，生成优化后的工作经历；否则输出问题
                if answer:
                    result = self._generate_optimized_experience(resume_data, answer, question)
                else:
                    result = self._optimize_experience(resume_data)
            elif section == "个人总结":
                result = self._optimize_summary(resume_data)
            elif section == "技能":
                result = self._optimize_skills(resume_data)
            elif section == "项目经历":
                result = self._optimize_projects(resume_data)
            else:
                # 默认给出整体优化建议
                result = self._suggest_optimization_plan(resume_data)

            return ToolResult(output=result)

        except Exception as e:
            return ToolResult(error=f"CVOptimizer error: {str(e)}")

    def _suggest_optimization_plan(self, resume_data: dict) -> str:
        """生成整体优化计划"""
        basic = resume_data.get("basic", {})
        experience = resume_data.get("experience", [])
        projects = resume_data.get("projects", [])

        suggestions = []

        # 1. 检查个人总结
        if not basic.get("summary") or not basic.get("summary").strip():
            suggestions.append("- **添加个人总结**：简历缺少个人总结，这是HR快速了解您的关键部分")

        # 2. 检查工作经历
        if experience:
            for exp in experience:
                details = exp.get("details", "")
                if not details or len(details) < 50:
                    company = exp.get("company", "")
                    suggestions.append(f"- **丰富工作经历**：{company}的工作描述过于简单，建议使用STAR法则补充量化成果")

        # 3. 检查技能
        skill_content = resume_data.get("skillContent", "")
        if not skill_content or "<" in skill_content:  # HTML 格式
            suggestions.append("- **优化技能描述**：技能部分需要更具体，建议按熟练度分层展示")

        if not suggestions:
            suggestions.append("- 简历内容相对完整，可以进一步优化工作经历的量化描述")

        result = f"""# 简历优化计划

根据您的简历分析，我建议按以下顺序进行优化：

{chr(10).join(suggestions)}

**我建议从【工作经历】开始优化**，因为这是HR最关注的部分。

您可以回复"帮我优化工作经历"开始优化流程。"""

        return result

    def _optimize_experience(self, resume_data: dict) -> str:
        """优化工作经历"""
        experience = resume_data.get("experience", [])

        if not experience:
            return "简历中没有找到工作经历信息。请先添加工作经历。"

        exp = experience[0]
        company = exp.get("company", "")
        position = exp.get("position", "")
        details = exp.get("details", "")

        result = f"""# 工作经历优化建议

## 当前内容分析

**公司**: {company}
**职位**: {position}
**描述**: {details if details else '（空）'}

## 问题诊断

当前工作经历描述存在以下问题：
1. **缺少量化数据**：没有具体的数字来展示工作成果
2. **描述过于笼统**：没有使用STAR法则来结构化描述
3. **没有突出技术栈**：没有明确展示使用的技术和工具

## 优化建议

请回答以下问题，我将帮您生成优化后的工作经历：

**问题1**: 您在{company}主要负责哪些核心工作？（请具体描述2-3项主要职责）

**问题2**: 您取得了哪些可量化的成果？（例如：性能提升X%、用户增长X、成本降低X）

**问题3**: 您使用了哪些关键技术？（例如：React、TypeScript、Node.js等）

**我最建议先回答问题一**，这样我们可以逐步优化您的工作经历描述。"""

        return result

    def _generate_optimized_experience(self, resume_data: dict, answer: str, question: str = "") -> str:
        """基于用户回答生成优化后的工作经历"""
        experience = resume_data.get("experience", [])

        if not experience:
            return "简历中没有找到工作经历信息。"

        exp = experience[0]
        company = exp.get("company", "")
        position = exp.get("position", "")

        # 判断这是哪个问题的回答（优先根据 question 参数，其次根据 answer 内容）
        answer_lower = answer.lower()
        question_lower = question.lower() if question else ""

        # 判断逻辑：优先 question 参数，其次 answer 内容
        is_question1 = (
            "问题1" in question_lower or "主要负责" in question_lower or
            "核心工作" in question_lower or "主要职责" in question_lower or
            ("负责" in answer_lower and ("开发" in answer_lower or "设计" in answer_lower or "优化" in answer_lower) and
             "%" not in answer and "提升" not in answer_lower or "增长" not in answer_lower)
        )

        is_question2 = (
            "问题2" in question_lower or "量化" in question_lower or "成果" in question_lower or
            ("%" in answer or "提升" in answer_lower or "增长" in answer_lower or
             "降低" in answer_lower or "减少" in answer_lower or "万" in answer or "千" in answer)
        )

        is_question3 = (
            "问题3" in question_lower or "技术" in question_lower or "技术栈" in question_lower or
            ("react" in answer_lower or "vue" in answer_lower or "typescript" in answer_lower or
             "python" in answer_lower or "java" in answer_lower or "node" in answer_lower or
             "框架" in answer_lower or "工具" in answer_lower)
        )

        if is_question1:
            # 这是问题1的回答
            result = f"""# 工作经历优化 - 问题一

## 您提供的信息

**问题1的回答**: {answer}

## 优化后的工作经历描述（基于问题一）

基于您提供的主要职责，我为您优化了工作经历描述：

**{company} - {position}**

{self._format_experience_duties(answer)}

## 下一步

现在我们已经优化了主要职责部分。**我建议继续回答问题二**，这样我们可以添加量化成果，让工作经历更有说服力。

**问题2**: 您取得了哪些可量化的成果？（例如：性能提升X%、用户增长X、成本降低X）"""

        elif is_question2:
            # 这是问题2的回答
            result = f"""# 工作经历优化 - 问题二

## 您提供的信息

**问题2的回答**: {answer}

## 优化后的工作经历描述（更新量化成果）

基于您提供的量化成果，我为您更新了工作经历描述：

**{company} - {position}**

（这里会包含之前优化的问题一内容 + 新的量化成果）

{self._format_quantifiable_results(answer)}

## 下一步

很好！我们已经添加了量化成果。**我建议继续回答问题三**，这样我们可以完善技术栈信息。

**问题3**: 您使用了哪些关键技术？（例如：React、TypeScript、Node.js等）"""

        elif is_question3:
            # 这是问题3的回答
            result = f"""# 工作经历优化 - 问题三

## 您提供的信息

**问题3的回答**: {answer}

## 最终优化后的工作经历

基于您提供的所有信息，我为您生成了完整优化后的工作经历：

**{company} - {position}**

{self._format_complete_experience(answer)}

## 优化完成

您的工作经历已经优化完成！现在包含了：
- ✅ 清晰的主要职责描述
- ✅ 量化的成果展示
- ✅ 明确的技术栈信息

您可以将这个优化后的描述更新到简历中。"""

        else:
            # 无法识别是哪个问题的回答，默认按问题1处理
            result = f"""# 工作经历优化

## 您提供的信息

{answer}

## 优化建议

基于您提供的信息，我建议您：

1. 如果这是对"主要职责"的回答，我们可以先优化职责描述
2. 如果这是对"量化成果"的回答，我们可以添加具体数据
3. 如果这是对"技术栈"的回答，我们可以突出技术能力

请告诉我这是对哪个问题的回答，或者直接说"继续优化工作经历"让我帮您完善。"""

        return result

    def _format_experience_duties(self, duties: str) -> str:
        """格式化主要职责描述"""
        # 简单的格式化，将用户输入转换为更专业的描述
        lines = duties.split('\n')
        formatted = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line:
                # 如果行首没有编号，添加编号
                if not line[0].isdigit() and not line.startswith('-') and not line.startswith('•'):
                    formatted.append(f"• {line}")
                else:
                    formatted.append(line)

        return '\n'.join(formatted) if formatted else duties

    def _format_quantifiable_results(self, results: str) -> str:
        """格式化量化成果"""
        lines = results.split('\n')
        formatted = []
        for line in lines:
            line = line.strip()
            if line:
                if not line[0].isdigit() and not line.startswith('-') and not line.startswith('•'):
                    formatted.append(f"• {line}")
                else:
                    formatted.append(line)

        return '\n'.join(formatted) if formatted else results

    def _format_complete_experience(self, tech_stack: str) -> str:
        """格式化完整的工作经历"""
        return f"""• 负责核心业务模块开发，使用 {tech_stack} 等技术栈
• 优化系统性能，提升用户体验
• 参与技术方案设计，推动项目落地"""

    def _optimize_summary(self, resume_data: dict) -> str:
        """优化个人总结"""
        basic = resume_data.get("basic", {})
        current_summary = basic.get("summary", "")
        title = basic.get("title", "")

        result = f"""# 个人总结优化建议

## 当前内容
{current_summary if current_summary else '（空，尚未填写个人总结）'}

## 问题诊断

{'个人总结为空，这会让HR无法快速了解您的核心竞争力。' if not current_summary else '当前个人总结可以进一步优化，更好地突出您的核心价值。'}

## 优化建议

一个好的个人总结应该包含：
1. **目标岗位**：您的职业目标
2. **核心技能**：2-3个最擅长的技术领域
3. **突出成就**：1-2个最有说服力的成就

请回答以下问题：

**问题1**: 您的目标岗位是什么？（例如：{title if title else '高级前端工程师'}）

**问题2**: 您最擅长的2-3项核心技能是什么？

**问题3**: 您最满意的职业成就是什么？

回答后，我将为您生成专业的个人总结。"""

        return result

    def _optimize_skills(self, resume_data: dict) -> str:
        """优化技能描述"""
        skill_content = resume_data.get("skillContent", "")

        result = f"""# 技能描述优化建议

## 当前内容
{skill_content if skill_content and '<' not in skill_content else '（技能描述需要优化）'}

## 问题诊断

当前技能描述存在以下问题：
1. **没有分层展示**：精通、熟练、了解应该分开
2. **缺少具体应用场景**：应说明在什么项目中使用过
3. **结构不清晰**：没有按类别分组（前端/后端/工具等）

## 优化建议

请回答以下问题：

**问题1**: 您精通哪些技术？（能独立解决复杂问题）

**问题2**: 您熟练使用哪些技术？（日常工作常用）

**问题3**: 您了解哪些技术？（有基础，能快速上手）

回答后，我将为您生成结构化的技能描述。"""

        return result

    def _optimize_projects(self, resume_data: dict) -> str:
        """优化项目经历"""
        projects = resume_data.get("projects", [])

        if not projects:
            return "简历中没有找到项目经历信息。请先添加项目经历。"

        proj = projects[0]
        name = proj.get("name", "")
        description = proj.get("description", "")

        result = f"""# 项目经历优化建议

## 当前内容分析

**项目名称**: {name}
**项目描述**: {description if description else '（空）'}

## 问题诊断

当前项目描述存在以下问题：
1. **缺少项目背景**：没有说明为什么要做这个项目
2. **技术方案不明确**：没有详细说明使用的技术栈
3. **成果不突出**：没有量化项目的影响力

## 优化建议

请回答以下问题：

**问题1**: 这个项目要解决什么问题？（项目背景）

**问题2**: 您在项目中负责什么？使用了哪些技术？

**问题3**: 项目取得了什么成果？（用户量、性能指标等）

回答后，我将为您生成专业的项目描述。"""

        return result
