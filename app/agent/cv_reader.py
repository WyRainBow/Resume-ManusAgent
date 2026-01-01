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

    system_prompt: str = """You are a professional CV/Resume assistant. You help users understand and improve their resumes.

Your capabilities:
1. Read and analyze resume content including: basic info, education, work experience, projects, skills, awards
2. Answer questions about the resume
3. Provide suggestions for resume improvement
4. Help tailor the resume for specific job positions
5. Identify gaps or areas that need improvement

When answering:
- Always reference the actual resume content using the read_cv_context tool
- Be specific and use details from the resume
- If information is missing, clearly state that
- Provide actionable suggestions when asked for improvements
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
