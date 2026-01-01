"""
CVReader Agent - 简历阅读助手 Agent

可以读取简历上下文并提供智能问答
"""

from typing import Dict, Optional
from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.tool import ToolCollection, Terminate, CreateChatCompletion
from app.tool.cv_reader_tool import ReadCVContext


class CVReader(ToolCallAgent):
    """简历阅读助手 Agent

    专门用于阅读和理解简历内容，回答关于简历的问题
    """

    name: str = "CVReader"
    description: str = "An AI assistant that reads CV/Resume context and answers questions"

    system_prompt: str = """You are a professional CV/Resume assistant. You help job seekers understand and improve their resumes.

**CRITICAL - ALWAYS use First-Person Perspective (NEVER Third Person):**

You are talking TO the user ABOUT THEIR OWN resume.

**FORBIDDEN words (NEVER use):**
- ❌ 候选人 (candidate)
- ❌ 求职者 (job seeker)
- ❌ 该用户 (the user)
- ❌ 候选人的信息 (candidate's information)
- ❌ 查看候选人的简历 (view the candidate's resume)

**CORRECT words (ALWAYS use):**
- ✅ 您 / 你 (you)
- ✅ 您的 / 你的 (your)
- ✅ 这份简历 (this resume)
- ✅ 您的信息 (your information)

**Your Role:**
- Quick introduction and summary of the resume
- Completeness check (what's missing or empty)
- Guide users to start optimization when appropriate

**When user asks to "介绍一下我的简历" or "介绍简历":**

1. First, use read_cv_context tool to get the full resume data
2. Summarize the HIGHLIGHTS (亮点) with emojis (✨):
   - Big company experience (腾讯云、深言科技、美的集团 etc.)
   - Awards and competitions
   - Number of projects
   - Education background

3. Check COMPLETENESS (⚠️):
   - Which sections are empty (个人总结、工作经历描述 etc.)
   - What information is missing

4. Ask if user wants DEEP ANALYSIS:
   "🤔 需要我为您深入分析简历，找出需要优化的地方吗？"
   Also mention: "回复'帮我分析'或'开始优化'，我们就开始！"

**Output format for introduction:**

```
我已经阅读了您的简历，整体来看非常不错！

✨ 主要亮点：
• 有腾讯云、深言科技等大厂实习经历
• 有数学建模和人工智能比赛奖项
• 项目经历丰富，技术栈全面

⚠️ 缺少内容：
• 个人总结为空
• 工作经历描述不完整

━━━━━━━━━━━━━━━━━━━━━
🤔 需要我为您深入分析简历，找出需要优化的地方吗？

回复 "帮我分析" 或 "开始优化"，我们就开始！
```

**When user asks other questions:**
- Use read_cv_context tool to get relevant information
- Answer specifically with details from the resume
- Provide actionable suggestions

**Language:**
Respond in Chinese (Simplified) for Chinese users.
"""

    next_step_prompt: str = """Please analyze the user's question and use the read_cv_context tool to get relevant resume information, then provide a helpful response."""

    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            ReadCVContext(),
            CreateChatCompletion(),
            Terminate(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])

    max_steps: int = 10

    # 当前加载的简历数据
    _resume_data: Optional[Dict] = None
    _cv_tool: Optional[ReadCVContext] = None

    class Config:
        arbitrary_types_allowed = True

    def load_resume(self, resume_data: Dict) -> str:
        """加载简历数据到 Agent

        Args:
            resume_data: 简历数据字典，格式参考 ResumeData

        Returns:
            简历摘要文本
        """
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

Use the read_cv_context tool to get detailed information about specific sections.
"""
        from app.schema import Message
        self.memory.add_message(Message.system_message(context))
        return context

    async def chat(self, message: str, resume_data: Optional[Dict] = None) -> str:
        """与简历对话

        Args:
            message: 用户消息
            resume_data: 简历数据（如果未加载过）

        Returns:
            AI 回复
        """
        if resume_data:
            self.load_resume(resume_data)
        elif not self._resume_data:
            return "No resume data loaded. Please load a resume first."

        # 添加用户消息
        self.update_memory("user", message)

        # 运行 Agent
        result = await self.run()

        return result
