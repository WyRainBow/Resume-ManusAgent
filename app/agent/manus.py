from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator, PrivateAttr

from app.agent.browser import BrowserContextHelper
from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT, GREETING_TEMPLATE
from app.tool import BrowserUseTool, CVAnalyzerAgentTool, CVEditorAgentTool, CVOptimizerAgentTool, CVReaderAgentTool, GetResumeStructure, Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.memory.conversation_manager import ConversationManager, Intent, ConversationState
from app.memory.langchain_memory import LangChainMemoryAdapter
from app.schema import Message, Role


class Manus(ToolCallAgent):
    """A versatile general-purpose agent with support for both local and MCP tools.

    集成 LangChain ConversationManager 提供智能对话管理：
    - 自动意图识别
    - 上下文追踪
    - 状态管理
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
            CVOptimizerAgentTool(),
            CVEditorAgentTool(),
            GetResumeStructure(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
    browser_context_helper: Optional[BrowserContextHelper] = None

    # Track connected MCP servers
    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )  # server_id -> url/command
    _initialized: bool = False

    # ConversationManager - 使用 PrivateAttr 避免 pydantic 验证
    _conversation_manager: ConversationManager = PrivateAttr(default=None)
    _langchain_memory: LangChainMemoryAdapter = PrivateAttr(default=None)
    _last_intent: Intent = PrivateAttr(default=None)
    _last_intent_info: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _should_wait_user: bool = PrivateAttr(default=False)  # 是否应该等待用户输入
    _current_resume_path: Optional[str] = PrivateAttr(default=None)  # 当前简历文件路径

    @model_validator(mode="after")
    def initialize_helper(self) -> "Manus":
        """Initialize basic components synchronously."""
        self.browser_context_helper = BrowserContextHelper(self)
        # 初始化对话管理器（LLM 会在 base.py 的 initialize_agent 中初始化）
        # 注意：此时 self.llm 可能还没初始化，所以先设为 None，后续会更新
        self._conversation_manager = ConversationManager(llm=None)
        # 初始化 LangChain Memory
        self._langchain_memory = LangChainMemoryAdapter(k=10, return_messages=True)
        return self

    def _ensure_conversation_manager_llm(self):
        """确保 ConversationManager 有 LLM 实例"""
        if self._conversation_manager and not self._conversation_manager.llm and self.llm:
            self._conversation_manager.llm = self.llm

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
            "cv_optimizer_agent",
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
        # 生成简单的上下文描述
        context_parts = []
        if self._conversation_manager.context.resume_loaded:
            context_parts.append("✅ 简历已加载")
        else:
            context_parts.append("⚠️ 简历未加载，建议先加载简历")

        # 如果有当前简历路径，添加到上下文
        if self._current_resume_path:
            context_parts.append(f"📄 当前简历文件: {self._current_resume_path}")
            context_parts.append("💡 当用户说'读取我的简历'或'看看我的简历'时，应该读取这个文件")

        # 如果有正在优化的模块，简单提示
        if self._conversation_manager.context.optimization.section:
            opt = self._conversation_manager.context.optimization
            context_parts.append(f"正在优化: {opt.section}")
            if opt.current_question > 0:
                context_parts.append(f"当前问题: 问题{opt.current_question}")

        context = "\n".join(context_parts) if context_parts else "初始状态"

        # 生成系统提示词（简化版，包含工具列表）
        system_prompt = SYSTEM_PROMPT.format(
            directory=config.workspace_root,
            context=context
        )

        # 生成下一步提示词（让 LLM 自主决定）
        next_step = NEXT_STEP_PROMPT

        logger.info(f"💭 提示词已生成，让 LLM 自主理解和决策")

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
            context_state = self._conversation_manager.context.state
            hints.append(f"当前状态: {context_state.value}")

        return "\n".join(hints)

    async def think(self) -> bool:
        """Process current state and decide next actions with intelligent context management."""
        if not self._initialized:
            await self.initialize_mcp_servers()
            self._initialized = True

        # 确保 ConversationManager 有 LLM 实例
        self._ensure_conversation_manager_llm()

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

        # 更新对话管理器状态
        if self.tool_calls:
            for tool_call in self.tool_calls:
                tool_name = tool_call.function.name
                self._conversation_manager.update_after_tool(tool_name, result)

                # 特殊处理：加载简历后更新状态
                if "load_resume" in tool_name.lower() or "cv_reader" in tool_name.lower():
                    if "成功" in result or "加载" in result:
                        self._conversation_manager.update_resume_loaded(True)

        # 同步消息到 LangChain Memory
        if self._langchain_memory:
            # 添加最近的 assistant 消息
            for msg in reversed(self.memory.messages[-5:]):
                if msg.role == Role.ASSISTANT and msg.content:
                    # 检查是否已经添加过（避免重复）
                    langchain_messages = self._langchain_memory.get_messages()
                    if not langchain_messages or langchain_messages[-1].content != msg.content:
                        self._langchain_memory.add_message(msg)
                    break

        # 检查是否应该等待用户输入
        # 优先检查工具返回的结果（因为工具可能返回问题）
        if self._langchain_memory:
            # 检查工具返回的结果（result 是格式化后的，包含 "Observed output of cmd..."）
            tool_result = result if result else None

            # 如果工具返回包含问题关键词，直接标记为需要等待
            if tool_result:
                wait_keywords = [
                    "问题1", "问题2", "问题3", "问题一", "问题二", "问题三",
                    "请回答", "我建议先回答", "继续回答", "我最建议先回答"
                ]
                has_wait_keyword = any(kw in tool_result for kw in wait_keywords)

                # 检查是否是真正的等待提示（不是错误信息，长度合理）
                if has_wait_keyword and 50 < len(tool_result) < 2000:
                    # 确保不是错误信息
                    if "error" not in tool_result.lower() and "失败" not in tool_result:
                        self._should_wait_user = True
                        logger.info(f"⏸️ Manus: 工具返回包含问题，需要等待用户输入 - {tool_result[:100]}...")
                        return result

            # 否则检查最后的 AI 消息
            last_ai_msg = None
            for msg in reversed(self.memory.messages[-3:]):
                if msg.role == Role.ASSISTANT and msg.content:
                    last_ai_msg = msg.content
                    break

            self._should_wait_user = self._langchain_memory.should_wait_for_user(last_ai_msg)
            if self._should_wait_user:
                logger.info("⏸️ Manus: 检测到需要等待用户输入，将暂停执行")

        return result

    def should_wait_for_user(self) -> bool:
        """检查是否应该等待用户输入"""
        return self._should_wait_user
