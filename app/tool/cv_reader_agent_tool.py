"""
CVReader Agent Tool - 将 CVReader Agent 包装成 Manus 可调用的工具

参考 MCPAgent 的集成方式，这个工具内部使用 CVReader Agent 来处理简历相关任务。
这样 CVReader 可以保持自己的 Agent 能力（多步思考、工具调用），同时 Manus 可以委托任务给它。
"""

from typing import Optional
from app.tool.base import BaseTool, ToolResult


class CVReaderAgentTool(BaseTool):
    """CVReader Agent 工具

    这是一个特殊的工具，它内部使用 CVReader Agent 来处理简历相关任务。
    Manus 可以委托简历任务给这个工具，CVReader 会以 Agent 的方式处理。

    使用场景：
    - 用户要求查看/了解当前简历内容
    - 用户要求介绍简历情况
    - 用户要求查看某个模块的内容
    """

    name: str = "cv_reader_agent"
    description: str = """Delegate CV/Resume queries to the CVReader Agent.

Use this tool when the user asks to view or understand their resume, such as:
- "看看我的简历"
- "我的工作经历有哪些"
- "介绍一下我的简历"
- "简历里写了什么"
- "我目前的技能是什么"

The CVReader Agent will read the resume and provide detailed information.
"""

    parameters: dict = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to ask about the resume"
            }
        },
        "required": ["question"]
    }

    # 全局简历数据
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
        """执行简历分析

        内部创建 CVReader Agent 并运行它来处理问题
        """
        if not CVReaderAgentTool._global_resume_data:
            return ToolResult(
                output="No resume data loaded. Please use load_resume_data tool first."
            )

        try:
            # 延迟导入避免循环依赖
            from app.agent.cv_reader import CVReader

            # 创建 CVReader Agent 实例
            cv_reader = CVReader()

            # 加载简历数据
            cv_reader.load_resume(CVReaderAgentTool._global_resume_data)

            # 运行 CVReader Agent 处理问题
            # CVReader 会以 Agent 的方式工作：思考、调用工具、多步推理
            result = await cv_reader.chat(question)

            return ToolResult(output=result)

        except Exception as e:
            return ToolResult(error=f"CVReader Agent error: {str(e)}")


class LoadResumeData(BaseTool):
    """加载简历数据的工具

    当用户想要开始创建简历或查看简历模板时使用此工具
    """

    name: str = "load_resume_data"
    description: str = """Load a resume template for the user to start creating/editing their resume.

Use this tool when:
- User wants to start creating their resume (开始写简历)
- User wants to see the resume template (看看简历模板)
- User wants to load a sample resume as reference (加载示例简历)
- Before any cv_editor_agent or cv_reader_agent tool call if no resume is loaded

此工具用于为求职者加载简历模板，方便后续编辑和生成。"""

    parameters: dict = {
        "type": "object",
        "properties": {
            "resume_source": {
                "type": "string",
                "description": "The source of the resume. Use 'sample' to load the sample resume.",
                "enum": ["sample"],
                "default": "sample"
            }
        }
    }

    async def execute(self, resume_source: str = "sample") -> ToolResult:
        """加载简历数据"""
        if resume_source == "sample":
            # 示例简历数据
            sample_resume = {
                "id": "sample-001",
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
                "menuSections": [
                    {"id": "basic", "title": "基本信息", "icon": "", "enabled": True, "order": 0},
                    {"id": "skills", "title": "专业技能", "icon": "", "enabled": True, "order": 1},
                    {"id": "experience", "title": "工作经历", "icon": "", "enabled": True, "order": 2},
                    {"id": "projects", "title": "项目经历", "icon": "", "enabled": True, "order": 3},
                    {"id": "openSource", "title": "开源经历", "icon": "", "enabled": True, "order": 4},
                    {"id": "awards", "title": "荣誉奖项", "icon": "", "enabled": True, "order": 5},
                    {"id": "education", "title": "教育经历", "icon": "", "enabled": True, "order": 6},
                ],
                "draggingProjectId": None,
                "globalSettings": {},
                "activeSection": "basic"
            }

            # 先设置到 CVReaderAgentTool
            CVReaderAgentTool.set_resume_data(sample_resume)

            # 然后让 CVEditorAgentTool 使用同一个引用
            # 这样 CVEditor 的修改会直接影响到 CVReader 的数据
            from app.tool.cv_editor_agent_tool import CVEditorAgentTool
            CVEditorAgentTool.set_resume_data(CVReaderAgentTool._global_resume_data)

            basic = sample_resume["basic"]
            return ToolResult(
                output=f"""Successfully loaded resume!

**Candidate:** {basic['name']}
**Position:** {basic['title']}
**Email:** {basic['email']}
**Phone:** {basic['phone']}
**Location:** {basic['location']}

You can now use the cv_reader_agent tool to ask questions about this resume."""
            )

        return ToolResult(error="Unknown resume source.")
