"""
CVOptimizer Agent - 简历优化建议助手 Agent

引导用户通过交互式流程优化简历
注意：只负责建议，不直接修改数据
"""

from typing import Dict, Optional
from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.tool import ToolCollection, Terminate, CreateChatCompletion
from app.tool.cv_reader_tool import ReadCVContext


class CVOptimizer(ToolCallAgent):
    """简历优化建议助手 Agent

    引导用户通过交互式流程优化简历
    注意：只负责建议，不直接修改数据
    """

    name: str = "CVOptimizer"
    description: str = "An AI assistant that guides users through resume optimization"

    system_prompt: str = """You are a professional resume optimization coach. You guide users through improving their resumes step by step.

**CRITICAL - ALWAYS use First-Person Perspective (NEVER Third Person):**

You are talking TO the user ABOUT THEIR OWN resume.

**FORBIDDEN words (NEVER use):**
- ❌ 候选人 (candidate)
- ❌ 求职者 (job seeker)
- ❌ 该用户 (the user)
- ❌ 候选人的信息 (candidate's information)

**CORRECT words (ALWAYS use):**
- ✅ 您 / 你 (you)
- ✅ 您的 / 你的 (your)
- ✅ 这份简历 (this resume)
- ✅ 您的信息 (your information)

**Your role is to SUGGEST and GUIDE, NOT to directly modify the resume.**

**Your workflow:**

1. **Suggest Starting Point** (when user says "start optimization" / "开始优化")
   - Analyze current resume state using read_cv_context tool
   - Suggest the most impactful section to optimize first
   - Explain why this section is important
   - Ask for user confirmation

2. **Collect Information** (one question at a time)
   - Ask structured questions with examples
   - Wait for user response before asking the next
   - Be encouraging and supportive
   - Keep questions focused and specific

3. **Generate Content** (after confirmation)
   - Summarize what you learned from the user
   - Ask for confirmation before generating
   - Generate polished, professional content
   - Present it clearly and ask if they want to apply it

4. **Important: Do NOT directly modify the resume**
   - Present the generated content to the user
   - Ask if they want to apply it (回复"可以"或"好的"我将更新到简历)
   - Let Manus handle the actual update via cv_editor_agent tool
   - Once confirmed, remind Manus to use cv_editor_agent with the exact content

**Question templates for different sections:**

For 个人总结 (Personal Summary):
1. 目标岗位：您的目标岗位是？（例如：大模型应用工程师、高级后端开发工程师）
2. 核心技能：您最擅长的技能是？（请列举2-3个核心技能）
3. 成就亮点：您最满意的成就是？（1-2个亮点，可以是工作/项目经历中提炼的）

For 工作经历 (Work Experience):
1. 职位角色：您在{company}担任什么职位？
2. 主要职责：您主要负责哪些工作？
3. 具体成果：您取得了哪些成果？（尽量提供量化数据）

**Output Style:**
- Use emojis for visual clarity (✨📋⚠️✅🔴🟡)
- Keep messages concise and actionable
- Always explain the "why" behind suggestions
- Be supportive and encouraging

**Language:**
Respond in Chinese (Simplified) for Chinese users.

**Success feedback pattern:**
When content is generated and user confirms:
```
根据您的确认，我将使用 cv_editor_agent 更新简历：
path='basic.summary', action='update', value='[生成的总结内容]'
```

Let Manus handle the actual tool call.
"""

    next_step_prompt: str = """Please guide the user through optimizing their resume. Start by suggesting which section to optimize first, then collect information one question at a time."""

    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            ReadCVContext(),           # 读取简历
            CreateChatCompletion(),    # 生成内容
            Terminate(),               # 结束
            # 注意：不包含 CVEditorAgentTool
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])

    max_steps: int = 15  # 优化流程可能需要更多步骤

    # 当前加载的简历数据
    _resume_data: Optional[Dict] = None
    _cv_tool: Optional[ReadCVContext] = None

    # 优化状态
    _current_section: Optional[str] = None
    _collected_info: Dict = None
    _current_question_index: int = 0

    class Config:
        arbitrary_types_allowed = True

    def load_resume(self, resume_data: Dict) -> str:
        """加载简历数据到 Agent"""
        self._resume_data = resume_data

        # 获取 ReadCVContext 工具并设置简历数据
        for tool in self.available_tools.tools:
            if isinstance(tool, ReadCVContext):
                tool.set_resume_data(resume_data)
                self._cv_tool = tool
                break

        # 将简历基本信息添加到上下文
        basic = resume_data.get("basic", {})
        context = f"""Current Resume Loaded:

Name: {basic.get('name', 'N/A')}
Target Position: {basic.get('title', 'N/A')}

Use the read_cv_context tool to get detailed information for optimization guidance.
"""
        from app.schema import Message
        self.memory.add_message(Message.system_message(context))
        return context

    async def chat(self, message: str, resume_data: Optional[Dict] = None) -> str:
        """与简历对话"""
        if resume_data:
            self.load_resume(resume_data)
        elif not self._resume_data:
            return "No resume data loaded. Please load a resume first."

        # 添加用户消息
        self.update_memory("user", message)

        # 运行 Agent
        result = await self.run()

        return result

    def suggest_next_section(self, resume_data: Dict) -> Dict:
        """建议下一个优化模块"""
        # 检查优先级
        basic = resume_data.get("basic", {})

        # 1. 个人总结最优先
        if not basic.get("summary") or not basic.get("summary").strip():
            return {
                "section": "个人总结",
                "reason": "让HR对您有一个初步的深刻印象",
                "priority": "high"
            }

        # 2. 工作经历
        experience = resume_data.get("experience", [])
        if experience:
            for i, exp in enumerate(experience):
                if not exp.get("details") or not exp.get("details").strip():
                    return {
                        "section": "工作经历",
                        "specific": f"experience[{i}]",
                        "reason": "HR最关注的部分，需要详细描述",
                        "priority": "high"
                    }

        # 3. 项目经历
        projects = resume_data.get("projects", [])
        if projects:
            for i, proj in enumerate(projects):
                if not proj.get("description") or not proj.get("description").strip():
                    return {
                        "section": "项目经历",
                        "specific": f"projects[{i}]",
                        "reason": "展示实际能力和技术栈",
                        "priority": "medium"
                    }

        # 4. 技能描述
        skill_content = resume_data.get("skillContent", "")
        if not skill_content or not skill_content.strip():
            return {
                "section": "技能描述",
                "reason": "突出核心竞争力",
                "priority": "medium"
            }

        # 如果都有内容，建议优化技能描述
        return {
            "section": "技能描述",
            "reason": "进一步突出核心竞争力",
            "priority": "low"
        }

    def get_questions_for_section(self, section: str, context: Dict = None) -> list:
        """获取指定模块的问题列表"""
        questions = {
            "个人总结": [
                {
                    "key": "target_position",
                    "question": "1️⃣ 您的目标岗位是？",
                    "example": "例如：大模型应用工程师、高级后端开发工程师",
                },
                {
                    "key": "core_skills",
                    "question": "2️⃣ 您最擅长的技能是？",
                    "example": "请列举2-3个核心技能",
                },
                {
                    "key": "proud_achievement",
                    "question": "3️⃣ 您最满意的成就是？",
                    "example": "1-2个亮点，可以是工作/项目经历中提炼的",
                }
            ],
            "工作经历": [
                {
                    "key": "company_role",
                    "question": "1️⃣ 您在{company}担任什么职位？",
                    "example": "具体职位名称",
                },
                {
                    "key": "responsibilities",
                    "question": "2️⃣ 您主要负责哪些工作？",
                    "example": "具体职责和任务",
                },
                {
                    "key": "achievements",
                    "question": "3️⃣ 您取得了哪些成果？",
                    "example": "尽量提供量化数据，如提升性能X%、节省Y小时",
                }
            ],
            "项目经历": [
                {
                    "key": "project_role",
                    "question": "1️⃣ 您在这个项目中担任什么角色？",
                    "example": "核心开发者/负责人/参与者",
                },
                {
                    "key": "project_tech",
                    "question": "2️⃣ 使用了哪些技术栈？",
                    "example": "例如：React、Node.js、Python",
                },
                {
                    "key": "project_result",
                    "question": "3️⃣ 项目取得了什么成果？",
                    "example": "用户量、性能提升、上线情况等",
                }
            ],
            "技能描述": [
                {
                    "key": "tech_stack",
                    "question": "1️⃣ 您掌握哪些技术栈？",
                    "example": "按熟练度分类列举",
                },
                {
                    "key": "skill_level",
                    "question": "2️⃣ 每项技能的熟练程度如何？",
                    "example": "例如：精通X，熟练使用Y，了解Z",
                }
            ]
        }

        # 如果有上下文（如公司名），填充到问题中
        section_questions = questions.get(section, [])
        if context and section == "工作经历":
            company = context.get("company", "该公司")
            section_questions[0]["question"] = section_questions[0]["question"].format(company=company)

        return section_questions

    def format_generated_summary(self, user_input: Dict) -> str:
        """根据用户输入生成个人总结"""
        target = user_input.get("target_position", "")
        skills = user_input.get("core_skills", "")
        achievement = user_input.get("proud_achievement", "")

        summary = f"""{target}，{skills}。{achievement}。

具备良好的系统设计、问题解决和团队协作能力，致力于在实际业务场景中创造价值。"""

        return summary

    def format_generated_experience(self, user_input: Dict, context: Dict) -> str:
        """根据用户输入生成工作经历描述"""
        company = context.get("company", "")
        position = user_input.get("company_role", "")
        responsibilities = user_input.get("responsibilities", "")
        achievements = user_input.get("achievements", "")

        details = f"""在{company}担任{position}期间：

主要职责：
{responsibilities}

工作成果：
{achievements}"""

        return details
