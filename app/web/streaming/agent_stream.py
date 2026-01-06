"""Agent stream output handler.

Handles streaming agent execution results to WebSocket clients.
使用与原始 server.py 相同的手动步骤循环逻辑。
"""

import asyncio
import json
import logging
import re
from typing import Any, AsyncIterator, Callable, Optional
from datetime import datetime

from app.agent.manus import Manus
from app.schema import AgentState as SchemaAgentState, Message, Role
from app.web.streaming.events import (
    EventType,
    StreamEvent,
    ThoughtEvent,
    ToolCallEvent,
    ToolResultEvent,
    AnswerEvent,
    AgentStartEvent,
    AgentEndEvent,
    AgentErrorEvent,
    SystemEvent,
)
from app.web.streaming.agent_state import AgentState, StateInfo
from app.web.streaming.state_machine import AgentStateMachine

logger = logging.getLogger(__name__)


EventSender = Callable[[dict[str, Any]], asyncio.Task]

# 分析结果标记
ANALYSIS_RESULT_MARKERS = [
    "📊 分析结果摘要",
    "💡 优化建议",
    "🎯 我最推荐的优化",
    "是否要应用这个优化",
    "是否要优化",
    "是否要优化这段教育经历",
    "综合评分"
]


class AgentStream:
    """Handles streaming agent execution to WebSocket.

    使用与原始 server.py 相同的执行逻辑：
    - 手动步骤循环
    - 调用 agent.step()
    - 发送 step, thought, tool_call, tool_result, answer 事件
    - 去重：防止发送重复内容
    """

    def __init__(
        self,
        agent: Manus,
        session_id: str,
        state_machine: AgentStateMachine,
        event_sender: EventSender,
        chat_history_manager: Optional[Any] = None,
    ) -> None:
        """Initialize the agent stream.

        Args:
            agent: The Manus agent instance
            session_id: Unique session identifier
            state_machine: The state machine for tracking execution
            event_sender: Async function to send events
            chat_history_manager: Optional chat history manager
        """
        self.agent = agent
        self._session_id = session_id
        self._state_machine = state_machine
        self._send_event = event_sender
        self._chat_history_manager = chat_history_manager

        # 🚨 去重：跟踪已发送的内容
        self._sent_thoughts: set[str] = set()
        self._sent_tools: set[str] = set()
        self._last_answer_content: str = ""
        self._answer_sent_in_loop: bool = False  # 🚨 跟踪循环中是否已发送过 answer

    async def execute(self, user_message: str) -> AsyncIterator[StreamEvent]:
        """Execute agent with streaming events.

        使用手动步骤循环，与原始 server.py 逻辑相同。

        Args:
            user_message: The user's input message

        Yields:
            StreamEvent instances during execution
        """
        try:
            # Start state
            await self._state_machine.transition_to(
                AgentState.STARTING,
                message="Starting agent execution",
                data={"user_message": user_message},
            )
            yield AgentStartEvent(
                agent_name="Manus",
                task=user_message,
                session_id=self._session_id,
            )

            # Running state
            await self._state_machine.transition_to(AgentState.RUNNING)

            # 确保智能体处于 IDLE 状态
            if self.agent.state != SchemaAgentState.IDLE:
                self.agent.state = SchemaAgentState.IDLE
                self.agent.current_step = 0

            # 清理不完整的消息序列
            self.agent.memory.cleanup_incomplete_sequences()

            # 添加用户消息到 memory
            self.agent.memory.add_message(Message.user_message(user_message))

            # 同步到 LangChain Memory
            if hasattr(self.agent, '_langchain_memory') and self.agent._langchain_memory:
                self.agent._langchain_memory.add_user_message(user_message)

            # 重置 answer 发送标志
            self._answer_sent_in_loop = False

            # 根据任务类型动态调整最大步数
            if any(keyword in user_message.lower() for keyword in ["分析", "analyze", "深入", "详细"]):
                max_steps = 10
            else:
                max_steps = 5

            # 记录最后发送的思考内容
            last_sent_thought = None

            # 手动执行步骤循环
            async with self.agent.state_context(SchemaAgentState.RUNNING):
                while self.agent.current_step < max_steps and self.agent.state != SchemaAgentState.FINISHED:
                    if self._state_machine.stop_requested:
                        await self._state_machine.transition_to(AgentState.STOPPED)
                        yield SystemEvent(
                            message="Execution stopped by user",
                            level="info",
                            session_id=self._session_id,
                        )
                        return

                    self.agent.current_step += 1

                    # 发送步骤事件
                    yield SystemEvent(
                        message=f"执行步骤 {self.agent.current_step}/{max_steps}",
                        level="info",
                        session_id=self._session_id,
                    )

                    # 记录执行前的消息数量
                    msg_count_before = len(self.agent.memory.messages)

                    # 执行一步
                    step_result = await self.agent.step()

                    # 实时发送新增的消息
                    new_messages = self.agent.memory.messages[msg_count_before:]

                    # 检查是否有分析工具结果
                    has_recent_analysis_result = False
                    for msg in reversed(self.agent.memory.messages[-10:]):
                        if msg.role == "tool" and msg.name in ['education_analyzer', 'cv_analyzer_agent']:
                            has_recent_analysis_result = True
                            break

                    # 处理新消息
                    for msg in new_messages:
                        if msg.role == "assistant":
                            # 先处理 tool_calls（assistant 消息可以同时有 content 和 tool_calls）
                            if msg.tool_calls:
                                await self._state_machine.transition_to(AgentState.TOOL_EXECUTING)
                                for tool_call in msg.tool_calls:
                                    tool_name = tool_call.function.name
                                    tool_call_id = tool_call.id  # ✅ 获取 tool_call_id

                                    # 🚨 去重：使用 tool_call_id 而不是 step 作为键
                                    if tool_call_id in self._sent_tools:
                                        logger.info(f"[跳过重复工具] {tool_name} (ID: {tool_call_id[:8]}...)")
                                        continue
                                    self._sent_tools.add(tool_call_id)

                                    tool_args = tool_call.function.arguments
                                    logger.info(f"[工具调用] {tool_name} | ID: {tool_call_id} | 参数: {str(tool_args)[:100]}...")
                                    yield ToolCallEvent(
                                        tool_name=tool_name,
                                        tool_args=tool_args if isinstance(tool_args, (dict, str)) else {},
                                        session_id=self._session_id,
                                        tool_call_id=tool_call_id,  # ✅ 传递 tool_call_id
                                    )

                            # 再处理 content（如果有）
                            if msg.content:
                                # 🚨 去重：跳过已发送过的相同内容
                                content_hash = hash(msg.content[:200])  # 用前200字符作为指纹
                                if content_hash in self._sent_thoughts:
                                    logger.debug(f"[跳过重复内容] {msg.content[:50]}...")
                                    continue
                                self._sent_thoughts.add(content_hash)

                                # 判断是否是分析结果回复
                                contains_analysis_result = any(
                                    marker in msg.content for marker in ANALYSIS_RESULT_MARKERS
                                )
                                is_final_answer = has_recent_analysis_result and contains_analysis_result

                                if is_final_answer:
                                    # 分析结果回复 - 标记为 answer
                                    logger.info(f"[分析结果回复] {msg.content[:200]}...")
                                    self._answer_sent_in_loop = True  # 🚨 标记已发送 answer
                                    yield AnswerEvent(
                                        content=msg.content,
                                        is_complete=True,
                                        session_id=self._session_id,
                                    )
                                else:
                                    # 思考过程 - 标记为 thought
                                    logger.debug(f"[思考过程] {msg.content[:100]}...")
                                    yield ThoughtEvent(
                                        thought=msg.content,
                                        session_id=self._session_id,
                                    )

                        elif msg.tool_calls:
                            # 非 assistant 消息的 tool_calls（fallback）
                            await self._state_machine.transition_to(AgentState.TOOL_EXECUTING)
                            for tool_call in msg.tool_calls:
                                tool_name = tool_call.function.name
                                tool_call_id = tool_call.id  # ✅ 获取 tool_call_id
                                # 🚨 去重：使用 tool_call_id 而不是 step 作为键
                                if tool_call_id in self._sent_tools:
                                    logger.info(f"[跳过重复工具] {tool_name} (ID: {tool_call_id[:8]}...)")
                                    continue
                                self._sent_tools.add(tool_call_id)

                                tool_args = tool_call.function.arguments
                                logger.info(f"[工具调用] {tool_name} | ID: {tool_call_id} | 参数: {str(tool_args)[:100]}...")
                                yield ToolCallEvent(
                                    tool_name=tool_name,
                                    tool_args=tool_args if isinstance(tool_args, (dict, str)) else {},
                                    session_id=self._session_id,
                                    tool_call_id=tool_call_id,  # ✅ 传递 tool_call_id
                                )

                        elif msg.role == "tool":
                            # Only transition if not already in THINKING state
                            if self._state_machine.current_state != AgentState.THINKING:
                                await self._state_machine.transition_to(AgentState.THINKING)
                            content = msg.content
                            tool_call_id = msg.tool_call_id  # ✅ 获取 tool_call_id

                            # 清理前缀
                            if content.startswith("Observed output of cmd `"):
                                prefix_pattern = r"Observed output of cmd `[^`]+` executed:\n"
                                content = re.sub(prefix_pattern, "", content, count=1)
                            elif content.startswith("Cmd `"):
                                content = "工具执行完成，无输出内容"

                            # 限制显示长度
                            if len(content) > 5000:
                                content = content[:5000] + f"\n...(内容已截断，共{len(msg.content)}字符)"

                            logger.info(f"[工具结果] {msg.name or 'unknown'} | ID: {tool_call_id} | 长度: {len(msg.content)} 字符")
                            yield ToolResultEvent(
                                tool_name=msg.name or "unknown",
                                result=content,
                                is_error=False,
                                session_id=self._session_id,
                                tool_call_id=tool_call_id,  # ✅ 传递 tool_call_id
                            )

                    # 检查是否陷入循环
                    if self.agent.is_stuck():
                        logger.info("⚠️ Agent 检测到循环，终止执行")
                        break

                    # 检查分析任务是否完成
                    if has_recent_analysis_result:
                        has_analysis_output = False
                        for msg in reversed(self.agent.memory.messages[-10:]):
                            if msg.role == "assistant" and msg.content:
                                contains_result = any(
                                    marker in msg.content for marker in ANALYSIS_RESULT_MARKERS
                                )
                                has_content = len(msg.content) > 100
                                no_more_tools = not msg.tool_calls or len(msg.tool_calls) == 0
                                if contains_result and has_content and no_more_tools:
                                    has_analysis_output = True
                                    logger.info(f"✅ 分析结果已输出: {msg.content[:100]}...")
                                    break

                        if has_analysis_output:
                            logger.info("✅ 分析任务完成，终止循环")
                            self.agent.state = SchemaAgentState.FINISHED
                            break

            # 重置步骤计数
            self.agent.current_step = 0
            self.agent.state = SchemaAgentState.IDLE

            # 只有在循环中没有发送过 answer 的情况下，才发送最终答案
            if not self._answer_sent_in_loop:
                final_answer = "任务已完成！"
                for msg in reversed(self.agent.memory.messages):
                    if msg.role == "assistant" and msg.content:
                        final_answer = msg.content
                        break

                yield AnswerEvent(
                    content=final_answer,
                    is_complete=True,
                    session_id=self._session_id,
                )

            # 保存到历史记录 - 保存所有类型的消息（包括 Tool 消息）
            if self._chat_history_manager:
                # 找到本次执行开始前的消息数量（user_message 已经在开头添加过了）
                # 这里我们保存所有在执行过程中产生的消息
                user_msg = Message(role=Role.USER, content=user_message)
                self._chat_history_manager.add_message(user_msg)

                # 保存所有 agent 生成的消息（包括 assistant with tool_calls, tool 结果, 最终答案）
                for msg in self.agent.memory.messages:
                    # 跳过用户消息（已经添加过）
                    if msg.role == Role.USER:
                        continue

                    # 保存 assistant 消息（可能包含 tool_calls）
                    if msg.role == Role.ASSISTANT:
                        self._chat_history_manager.add_message(Message(
                            role=Role.ASSISTANT,
                            content=msg.content,
                            tool_calls=msg.tool_calls
                        ))
                    # 保存 tool 消息（关键：包含 optimization_suggestions JSON）
                    elif msg.role == Role.TOOL:
                        self._chat_history_manager.add_message(Message(
                            role=Role.TOOL,
                            content=msg.content,
                            name=msg.name,
                            tool_call_id=msg.tool_call_id
                        ))
                        logger.debug(f"  💾 保存 Tool 消息: {msg.name}, 长度: {len(msg.content or '')}")

                logger.info(f"📜 已保存对话到 ChatHistory ({len(self.agent.memory.messages)} 条消息)")

            # Completed state
            await self._state_machine.transition_to(
                AgentState.COMPLETED,
                message="Agent execution completed",
            )

            yield AgentEndEvent(
                agent_name="Manus",
                success=True,
                session_id=self._session_id,
            )

        except Exception as e:
            logger.exception(f"Error during agent execution: {e}")
            await self._state_machine.handle_error(e)
            yield AgentErrorEvent(
                error_message=str(e),
                error_type=type(e).__name__,
                session_id=self._session_id,
            )

    async def send_event(self, event: StreamEvent) -> None:
        """Send an event to the client.

        Args:
            event: The event to send
        """
        try:
            task = self._send_event(event.to_dict())
            await asyncio.gather(task, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error sending event: {e}")


class StreamProcessor:
    """Processes streaming agent output for multiple clients.

    Features:
    - Manage multiple active streams
    - Route events to correct clients
    - Handle stream lifecycle
    """

    def __init__(self) -> None:
        """Initialize the stream processor."""
        self._active_streams: dict[str, AgentStream] = {}
        self._lock = asyncio.Lock()

    async def start_stream(
        self,
        session_id: str,
        agent: Manus,
        state_machine: AgentStateMachine,
        event_sender: EventSender,
        user_message: str,
        chat_history_manager: Optional[Any] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Start a new agent stream.

        Args:
            session_id: Unique session identifier
            agent: The Manus agent instance
            state_machine: The state machine for tracking
            event_sender: Function to send events
            user_message: The user's input
            chat_history_manager: Optional chat history manager

        Yields:
            StreamEvent instances during execution
        """
        stream = AgentStream(agent, session_id, state_machine, event_sender, chat_history_manager)

        async with self._lock:
            self._active_streams[session_id] = stream

        # Execute stream and yield events
        try:
            async for event in stream.execute(user_message):
                yield event
        finally:
            await self.remove_stream(session_id)

    async def remove_stream(self, session_id: str) -> None:
        """Remove a completed stream.

        Args:
            session_id: The session ID whose stream to remove
        """
        async with self._lock:
            self._active_streams.pop(session_id, None)

    def has_active_stream(self, session_id: str) -> bool:
        """Check if a session has an active stream.

        Args:
            session_id: The session ID to check

        Returns:
            True if stream is active
        """
        return session_id in self._active_streams

    def get_stream(self, session_id: str) -> Optional[AgentStream]:
        """Get an active stream.

        Args:
            session_id: The session ID

        Returns:
            The AgentStream if active, None otherwise
        """
        return self._active_streams.get(session_id)

    async def stop_stream(self, session_id: str) -> bool:
        """Request a stream to stop.

        Args:
            session_id: The session ID whose stream to stop

        Returns:
            True if stream was found and stop requested
        """
        stream = self.get_stream(session_id)
        if stream:
            stream._state_machine.request_stop()
            return True
        return False
