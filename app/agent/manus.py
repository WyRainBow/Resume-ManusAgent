from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator, PrivateAttr

from app.agent.browser import BrowserContextHelper
from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT, GREETING_TEMPLATE
from app.tool import BrowserUseTool, CVAnalyzerAgentTool, CVEditorAgentTool, CVReaderAgentTool, EducationAnalyzerTool, GetResumeStructure, Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.memory import (
    ChatHistoryManager,
    ConversationStateManager,
    ConversationState,
    Intent,
)
from app.schema import Message, Role


class Manus(ToolCallAgent):
    """A versatile general-purpose agent with support for both local and MCP tools.

    集成 LangChain 风格的 Memory 系统提供智能对话管理：
    - ChatHistoryManager: 管理对话历史
    - ConversationStateManager: 意图识别和状态管理
    """

    name: str = "Manus"
    description: str = "A versatile agent that can solve various tasks using multiple tools including MCP-based tools"

    # 使用动态系统提示词
    system_prompt: str = ""
    next_step_prompt: str = ""

    max_observe: int = 10000
    max_steps: int = 20

    # MCP clients for remote tool access
    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    # Add general-purpose tools to the tool collection
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            BrowserUseTool(),
            StrReplaceEditor(),
            AskHuman(),
            Terminate(),
            CVReaderAgentTool(),
            CVAnalyzerAgentTool(),
            CVEditorAgentTool(),
            GetResumeStructure(),
            EducationAnalyzerTool(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
    browser_context_helper: Optional[BrowserContextHelper] = None

    # Track connected MCP servers
    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )  # server_id -> url/command
    _initialized: bool = False

    # Memory components - 使用 PrivateAttr 避免 pydantic 验证
    _conversation_state: ConversationStateManager = PrivateAttr(default=None)
    _chat_history: ChatHistoryManager = PrivateAttr(default=None)
    _last_intent: Intent = PrivateAttr(default=None)
    _last_intent_info: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _current_resume_path: Optional[str] = PrivateAttr(default=None)

    @model_validator(mode="after")
    def initialize_helper(self) -> "Manus":
        """Initialize basic components synchronously."""
        self.browser_context_helper = BrowserContextHelper(self)
        # 初始化对话状态管理器（LLM 会在 base.py 的 initialize_agent 中初始化）
        self._conversation_state = ConversationStateManager(llm=None)
        # 初始化聊天历史管理器
        self._chat_history = ChatHistoryManager(k=10)
        return self

    def _ensure_conversation_state_llm(self):
        """确保 ConversationStateManager 有 LLM 实例"""
        if self._conversation_state and not self._conversation_state.llm and self.llm:
            self._conversation_state.llm = self.llm

    @classmethod
    async def create(cls, **kwargs) -> "Manus":
        """Factory method to create and properly initialize a Manus instance."""
        instance = cls(**kwargs)
        await instance.initialize_mcp_servers()
        instance._initialized = True
        return instance

    async def initialize_mcp_servers(self) -> None:
        """Initialize connections to configured MCP servers."""
        for server_id, server_config in config.mcp_config.servers.items():
            try:
                if server_config.type == "sse":
                    if server_config.url:
                        await self.connect_mcp_server(server_config.url, server_id)
                        logger.info(
                            f"Connected to MCP server {server_id} at {server_config.url}"
                        )
                elif server_config.type == "stdio":
                    if server_config.command:
                        await self.connect_mcp_server(
                            server_config.command,
                            server_id,
                            use_stdio=True,
                            stdio_args=server_config.args,
                        )
                        logger.info(
                            f"Connected to MCP server {server_id} using command {server_config.command}"
                        )
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {server_id}: {e}")

    async def connect_mcp_server(
        self,
        server_url: str,
        server_id: str = "",
        use_stdio: bool = False,
        stdio_args: List[str] = None,
    ) -> None:
        """Connect to an MCP server and add its tools."""
        if use_stdio:
            await self.mcp_clients.connect_stdio(
                server_url, stdio_args or [], server_id
            )
            self.connected_servers[server_id or server_url] = server_url
        else:
            await self.mcp_clients.connect_sse(server_url, server_id)
            self.connected_servers[server_id or server_url] = server_url

        # Update available tools with only the new tools from this server
        new_tools = [
            tool for tool in self.mcp_clients.tools if tool.server_id == server_id
        ]
        self.available_tools.add_tools(*new_tools)

    async def disconnect_mcp_server(self, server_id: str = "") -> None:
        """Disconnect from an MCP server and remove its tools."""
        await self.mcp_clients.disconnect(server_id)
        if server_id:
            self.connected_servers.pop(server_id, None)
        else:
            self.connected_servers.clear()

        # Rebuild available tools without the disconnected server's tools
        base_tools = [
            tool
            for tool in self.available_tools.tools
            if not isinstance(tool, MCPClientTool)
        ]
        self.available_tools = ToolCollection(*base_tools)
        self.available_tools.add_tools(*self.mcp_clients.tools)

    async def cleanup(self):
        """Clean up Manus agent resources."""
        if self.browser_context_helper:
            await self.browser_context_helper.cleanup_browser()
        # Disconnect from all MCP servers only if we were initialized
        if self._initialized:
            await self.disconnect_mcp_server()
            self._initialized = False

    def _get_last_user_input(self) -> str:
        """获取最后一条真正的用户输入（过滤系统提示词）"""
        # 系统提示词的特征
        system_patterns = [
            "## ",  # Markdown 标题
            "**重要",  # 重要提示
            "工具选择",  # 工具选择规则
            "根据用户输入",  # 系统指令
            "意图识别",  # 系统指令
            "cv_reader_agent",  # 工具名
            "cv_analyzer_agent",
            "cv_editor_agent",
        ]

        for msg in reversed(self.memory.messages):
            if msg.role == "user" and msg.content:
                content = msg.content.strip()
                # 检查是否是系统提示词
                is_system = any(pattern in content for pattern in system_patterns)
                # 真正的用户输入通常较短
                if not is_system and len(content) < 500:
                    return content
        return ""

    async def _generate_dynamic_prompts(self, user_input: str) -> tuple:
        """
        根据用户输入和对话状态动态生成提示词

        简化版：让 LLM 自主理解意图并决定工具调用

        返回: (system_prompt, next_step_prompt)
        """
        logger.info(f"🔍 获取到的用户输入: {user_input[:100] if user_input else '(空)'}")
        # 生成简单的上下文描述
        context_parts = []
        if self._conversation_state.context.resume_loaded:
            context_parts.append("✅ 简历已加载")
        else:
            context_parts.append("⚠️ 简历未加载，建议先加载简历")

        # 如果有当前简历路径，添加到上下文
        if self._current_resume_path:
            context_parts.append(f"📄 当前简历文件: {self._current_resume_path}")
            context_parts.append("💡 当用户说'读取我的简历'或'看看我的简历'时，应该读取这个文件")

        # 如果有正在优化的模块，简单提示
        if self._conversation_state.context.optimization.section:
            opt = self._conversation_state.context.optimization
            context_parts.append(f"正在优化: {opt.section}")
            if opt.current_question > 0:
                context_parts.append(f"当前问题: 问题{opt.current_question}")

        # 检查最近的工具调用结果，判断简历是否刚被加载
        recent_cv_loaded = False
        for msg in reversed(self.memory.messages[-5:]):
            if hasattr(msg, 'content') and msg.content:
                if "CV/Resume Context" in msg.content or "Basic Information" in msg.content:
                    recent_cv_loaded = True
                    break

        # 如果最近调用了 cv_reader_agent 并成功，强制更新状态
        if recent_cv_loaded and not self._conversation_state.context.resume_loaded:
            self._conversation_state.update_resume_loaded(True)
            context_parts = ["✅ 简历已加载（刚刚加载成功）"]
            logger.info("📋 检测到简历已加载，更新状态")

        context = "\n".join(context_parts) if context_parts else "初始状态"

        # 生成系统提示词（简化版，包含工具列表）
        system_prompt = SYSTEM_PROMPT.format(
            directory=config.workspace_root,
            context=context
        )

        # 检查用户输入是否包含教育分析请求
        user_wants_education = False
        if user_input:
            user_lower = user_input.lower()
            if "教育" in user_lower or "学历" in user_lower or "专业" in user_lower:
                user_wants_education = True

        # 生成下一步提示词，加入当前状态提示
        if self._conversation_state.context.resume_loaded:
            # 检查是否已经调用了分析工具
            recent_analysis = False
            for msg in reversed(self.memory.messages[-3:]):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc.function.name in ['education_analyzer', 'cv_analyzer_agent']:
                            recent_analysis = True
                            break
                    if recent_analysis:
                        break

            if recent_analysis:
                # 分析已完成，检查是否有分析结果返回（检查 tool message）
                analysis_result_returned = False
                analysis_tool_name = None
                for msg in reversed(self.memory.messages[-5:]):
                    # 检查是否是 tool message（工具返回结果）
                    if hasattr(msg, 'role') and msg.role == "tool":
                        if hasattr(msg, 'name') and msg.name in ['education_analyzer', 'cv_analyzer_agent']:
                            analysis_result_returned = True
                            analysis_tool_name = msg.name
                            break
                    # 也检查 content 中是否包含分析结果的关键字
                    elif hasattr(msg, 'content') and msg.content:
                        if "教育经历分析" in msg.content or "优化建议示例" in msg.content or "分析结果" in msg.content:
                            analysis_result_returned = True
                            if "教育" in msg.content:
                                analysis_tool_name = "education_analyzer"
                            break

                if analysis_result_returned:
                    # 分析结果已返回，获取分析结果内容
                    analysis_content = ""
                    for msg in reversed(self.memory.messages[-10:]):
                        if msg.role == "tool" and msg.name in ['education_analyzer', 'cv_analyzer_agent']:
                            analysis_content = msg.content[:5000]  # 限制长度，但要包含优化建议
                            break

                    tool_display_name = "教育经历" if analysis_tool_name == "education_analyzer" else "简历"
                    next_step = f"""## 🚨🚨🚨 CRITICAL: ANALYSIS COMPLETED! OUTPUT RESULTS NOW! 🚨🚨🚨

⛔ **STOP! DO NOT CALL ANY TOOLS!** ⛔
⛔ **NO cv_editor_agent!** ⛔
⛔ **NO get_resume_structure!** ⛔
⛔ **NO terminate!** ⛔

The analysis tool ({analysis_tool_name}) has returned the following result. You MUST present this to the user:

---
{analysis_content}
---

## YOUR TASK (OUTPUT TEXT ONLY, NO TOOL CALLS):

用中文输出以下内容：

### 1. 📊 分析结果摘要
- 综合评分（从上面的结果中提取）
- 优势列表
- 问题列表

### 2. 💡 优化建议对比
找到上面结果中的"优化建议示例"部分，逐条展示：

| 优化项 | 当前内容 | 优化后内容 |
|--------|----------|------------|
| 建议1标题 | ❌ current内容 | ✅ optimized内容 |
| 建议2标题 | ❌ current内容 | ✅ optimized内容 |

### 3. 🎯 我最推荐的优化
选择最重要的一条，告诉用户：
"💡 我最推荐优先优化：**【标题】**，因为..."

### 4. 询问用户
最后问：**"是否要应用这个优化？回复'优化'我将帮您修改，回复'不需要'则结束。"**

---

⚠️ **REMEMBER**:
- This step = OUTPUT TEXT ONLY
- Next step (after user replies "优化") = Call cv_editor_agent()
- DO NOT SKIP AHEAD!"""
            else:
                # 简历已加载，提示 LLM 进行分析
                # user_wants_education 已在上面计算
                user_wants_full_analysis = False
                if user_input and not user_wants_education:
                    user_lower = user_input.lower()
                    if "简历" in user_lower and "分析" in user_lower:
                        user_wants_full_analysis = True

                if user_wants_education:
                    # 检查是否已经调用了 education_analyzer
                    already_called_education_analyzer = False
                    for msg in reversed(self.memory.messages[-10:]):
                        if msg.role == "tool" and msg.name == "education_analyzer":
                            already_called_education_analyzer = True
                            break
                        elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                if tc.function.name == "education_analyzer":
                                    already_called_education_analyzer = True
                                    break
                            if already_called_education_analyzer:
                                break

                    if not already_called_education_analyzer:
                        next_step = f"""## 🚨🚨🚨 CRITICAL: USER WANTS EDUCATION ANALYSIS! 🚨🚨🚨

**CURRENT STATE**: ✅ Resume is LOADED!

**USER'S CURRENT REQUEST**: "{user_input}"

**YOUR ACTION**: Call education_analyzer() NOW!

⛔ DO NOT:
- Call cv_reader_agent (resume already loaded)
- Assume user said "优化" (they did NOT say that - the user only said "{user_input}")
- Output text (just call the tool)

✅ DO THIS:
- Call education_analyzer() with empty arguments: {{}}
- Wait for the tool result
- Then output the analysis results

Make the tool call NOW!"""
                    else:
                        # 已经调用了，使用分析结果返回的逻辑
                        next_step = f"""## ANALYSIS COMPLETED - OUTPUT RESULTS NOW!

The education_analyzer() has been called. Output the analysis results to the user.

DO NOT call any tools. Just output the results."""
                elif user_wants_full_analysis:
                    next_step = f"""## CURRENT STATE: ✅ Resume is LOADED!

**DO NOT call cv_reader_agent again!** The resume is already loaded.

**USER REQUEST DETECTED: 分析简历**

⚡ YOUR NEXT ACTION: Call cv_analyzer_agent() NOW!

{NEXT_STEP_PROMPT}"""
                else:
                    next_step = f"""## CURRENT STATE: ✅ Resume is LOADED!

**DO NOT call cv_reader_agent again!** The resume is already loaded.

Now proceed with analysis based on user's request:
- If user mentioned education/学历/专业 → Call education_analyzer() NOW
- If user mentioned resume analysis → Call cv_analyzer_agent() NOW

{NEXT_STEP_PROMPT}"""
        else:
            # 简历未加载
            if user_wants_education and self._current_resume_path:
                next_step = f"""## 🚨 USER WANTS EDUCATION ANALYSIS - LOAD RESUME FIRST! 🚨

**CURRENT STATE**: ⚠️ Resume NOT loaded yet

**USER'S REQUEST**: "{user_input}"
**RESUME PATH**: {self._current_resume_path}

**YOUR ACTION**: Call cv_reader_agent(file_path="{self._current_resume_path}") NOW!

After the resume is loaded, you will call education_analyzer() in the next step.

Make the tool call NOW!"""
            else:
                next_step = NEXT_STEP_PROMPT

        logger.info(f"💭 提示词已生成，当前状态: {context}")

        return system_prompt, next_step

    def _generate_intent_hint(self, result: Dict[str, Any]) -> str:
        """根据意图识别结果生成提示"""
        intent = result["intent"]
        tool = result.get("tool")
        tool_args = result.get("tool_args", {})

        hints = []

        if intent == Intent.GREETING:
            hints.append("用户在打招呼，请友好回应并介绍你的能力。")

        elif intent == Intent.VIEW_RESUME:
            hints.append(f"用户想查看简历，请使用 {tool} 工具。")

        elif intent == Intent.ANALYZE:
            hints.append(f"用户想分析简历，请使用 {tool} 工具进行深入分析。")

        elif intent == Intent.OPTIMIZE:
            hints.append(f"用户想优化简历，请使用 {tool} 工具。")
            if tool_args:
                hints.append(f"参数: {tool_args}")

        elif intent == Intent.OPTIMIZE_SECTION:
            section = tool_args.get("section", "工作经历")
            hints.append(f"用户想优化 [{section}] 模块。")
            hints.append(f"请调用: {tool}(action='optimize_section', section='{section}')")

        elif intent == Intent.ANSWER_QUESTION:
            question = tool_args.get("question", "问题1")
            section = tool_args.get("section", "工作经历")
            answer = tool_args.get("answer", "")
            hints.append(f"用户正在回答 {question}。")
            hints.append(f"请调用: {tool}(action='optimize_section', section='{section}', answer='{answer[:50]}...', question='{question}')")
            hints.append("**重要**: 直接调用工具处理回答，不要重新分析简历！")

        elif intent == Intent.CONFIRM:
            if tool:
                hints.append(f"用户确认了操作，请使用 {tool} 工具继续。")
            else:
                hints.append("用户确认了操作，请根据之前的建议继续。")

        else:
            hints.append("无法确定用户意图，请根据对话上下文理解用户需求。")
            context_state = self._conversation_state.context.state
            hints.append(f"当前状态: {context_state.value}")

        return "\n".join(hints)

    async def think(self) -> bool:
        """Process current state and decide next actions with intelligent context management."""
        if not self._initialized:
            await self.initialize_mcp_servers()
            self._initialized = True

        # 确保 ConversationStateManager 有 LLM 实例
        self._ensure_conversation_state_llm()

        # 获取最后的用户输入
        user_input = self._get_last_user_input()

        # 动态生成提示词（异步）
        self.system_prompt, self.next_step_prompt = await self._generate_dynamic_prompts(user_input)

        # 检查是否需要浏览器上下文
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.name == BrowserUseTool().name
            for msg in recent_messages
            if msg.tool_calls
            for tc in msg.tool_calls
        )

        if browser_in_use:
            browser_prompt = await self.browser_context_helper.format_next_step_prompt()
            self.next_step_prompt = f"{self.next_step_prompt}\n\n{browser_prompt}"

        # 调用父类的 think 方法
        result = await super().think()

        return result

    async def act(self) -> str:
        """Execute tool calls and update conversation state."""
        result = await super().act()

        # 更新对话状态管理器
        if self.tool_calls:
            for tool_call in self.tool_calls:
                tool_name = tool_call.function.name
                self._conversation_state.update_after_tool(tool_name, result)

                # 特殊处理：加载简历后更新状态
                if "load_resume" in tool_name.lower() or "cv_reader" in tool_name.lower():
                    # 检测简历是否成功加载（更宽松的条件）
                    if result and ("CV/Resume Context" in result or "Basic Information" in result or "Education" in result or "成功" in result):
                        self._conversation_state.update_resume_loaded(True)
                        logger.info("📋 简历已成功加载，状态已更新")

        # 同步消息到 ChatHistory
        if self._chat_history:
            # 添加最近的 assistant 消息
            for msg in reversed(self.memory.messages[-5:]):
                if msg.role == Role.ASSISTANT and msg.content:
                    # 检查是否已经添加过（避免重复）
                    history_messages = self._chat_history.get_messages()
                    if not history_messages or history_messages[-1].content != msg.content:
                        self._chat_history.add_message(msg)
                    break

        # 检查是否应该等待用户输入
        if self._chat_history:
            # 检查工具返回的结果
            tool_result = result if result else None

            # 检查最后的 AI 消息（用于调试）
            last_ai_msg = None
            for msg in reversed(self.memory.messages[-3:]):
                if msg.role == Role.ASSISTANT and msg.content:
                    last_ai_msg = msg.content
                    break

        return result
