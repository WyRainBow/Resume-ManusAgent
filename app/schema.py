from enum import Enum
from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Message role options"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


ROLE_VALUES = tuple(role.value for role in Role)
ROLE_TYPE = Literal[ROLE_VALUES]  # type: ignore


class ToolChoice(str, Enum):
    """Tool choice options"""

    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"


TOOL_CHOICE_VALUES = tuple(choice.value for choice in ToolChoice)
TOOL_CHOICE_TYPE = Literal[TOOL_CHOICE_VALUES]  # type: ignore


class AgentState(str, Enum):
    """Agent execution states"""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class Function(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    """Represents a tool/function call in a message"""

    id: str
    type: str = "function"
    function: Function


class Message(BaseModel):
    """Represents a chat message in the conversation"""

    role: ROLE_TYPE = Field(...)  # type: ignore
    content: Optional[str] = Field(default=None)
    tool_calls: Optional[List[ToolCall]] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)

    def __add__(self, other) -> List["Message"]:
        """支持 Message + list 或 Message + Message 的操作"""
        if isinstance(other, list):
            return [self] + other
        elif isinstance(other, Message):
            return [self, other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )

    def __radd__(self, other) -> List["Message"]:
        """支持 list + Message 的操作"""
        if isinstance(other, list):
            return other + [self]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(other).__name__}' and '{type(self).__name__}'"
            )

    def to_dict(self) -> dict:
        """Convert message to dictionary format"""
        message = {"role": self.role}
        if self.content is not None:
            message["content"] = self.content
        if self.tool_calls is not None:
            message["tool_calls"] = [tool_call.dict() for tool_call in self.tool_calls]
        if self.name is not None:
            message["name"] = self.name
        if self.tool_call_id is not None:
            message["tool_call_id"] = self.tool_call_id
        if self.base64_image is not None:
            message["base64_image"] = self.base64_image
        return message

    @classmethod
    def user_message(
        cls, content: str, base64_image: Optional[str] = None
    ) -> "Message":
        """Create a user message"""
        return cls(role=Role.USER, content=content, base64_image=base64_image)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """Create a system message"""
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def assistant_message(
        cls, content: Optional[str] = None, base64_image: Optional[str] = None
    ) -> "Message":
        """Create an assistant message"""
        return cls(role=Role.ASSISTANT, content=content, base64_image=base64_image)

    @classmethod
    def tool_message(
        cls, content: str, name, tool_call_id: str, base64_image: Optional[str] = None
    ) -> "Message":
        """Create a tool message"""
        return cls(
            role=Role.TOOL,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            base64_image=base64_image,
        )

    @classmethod
    def from_tool_calls(
        cls,
        tool_calls: List[Any],
        content: Union[str, List[str]] = "",
        base64_image: Optional[str] = None,
        **kwargs,
    ):
        """Create ToolCallsMessage from raw tool calls.

        Args:
            tool_calls: Raw tool calls from LLM
            content: Optional message content
            base64_image: Optional base64 encoded image
        """
        formatted_calls = [
            {"id": call.id, "function": call.function.model_dump(), "type": "function"}
            for call in tool_calls
        ]
        return cls(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=formatted_calls,
            base64_image=base64_image,
            **kwargs,
        )


class Memory(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    max_messages: int = Field(default=25)  # 从100调整为25，支持20-30轮对话，自动管理Token预算

    def add_message(self, message: Message) -> None:
        """Add a message to memory"""
        self.messages.append(message)
        # Optional: Implement message limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def add_messages(self, messages: List[Message]) -> None:
        """Add multiple messages to memory"""
        self.messages.extend(messages)
        # Optional: Implement message limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()

    def cleanup_incomplete_sequences(self) -> None:
        """
        清理不完整的消息序列，确保符合 OpenAI API 要求：
        1. tool_calls 必须有对应的 tool 消息（通过 tool_call_id 匹配）
        2. tool 消息必须有对应的 tool_calls

        复刻 LangChain 的消息完整性检查逻辑。
        """
        if not self.messages:
            return

        # 收集所有 tool_call_id 和 tool 消息的 tool_call_id
        tool_call_ids_from_assistant = set()
        tool_call_ids_from_tool_msgs = set()

        for msg in self.messages:
            if msg.role == "assistant" and msg.tool_calls:
                for tc in msg.tool_calls:
                    if hasattr(tc, 'id'):
                        tool_call_ids_from_assistant.add(tc.id)
            elif msg.role == "tool" and msg.tool_call_id:
                tool_call_ids_from_tool_msgs.add(msg.tool_call_id)

        # 只保留完整的消息对：
        # - assistant 消息总是保留（即使有未完成的 tool_calls）
        # - tool 消息只保留有对应 tool_calls 的
        cleaned = []
        for msg in self.messages:
            if msg.role != "tool":
                # 非 tool 消息总是保留
                cleaned.append(msg)
            elif msg.tool_call_id in tool_call_ids_from_assistant:
                # tool 消息有对应的 tool_calls，保留
                cleaned.append(msg)
            # else: tool 消息没有对应的 tool_calls，跳过（不完整）

        self.messages = cleaned

    def get_recent_messages(self, n: int) -> List[Message]:
        """Get n most recent messages"""
        return self.messages[-n:]

    def to_dict_list(self) -> List[dict]:
        """Convert messages to list of dicts"""
        return [msg.to_dict() for msg in self.messages]


# ============================================================================
# LangChain 风格的工具调用上下文处理函数
# ============================================================================

def fetch_last_ai_and_tool_messages(messages: List[Message]) -> tuple[Optional[Message], List[Message]]:
    """
    获取最后的 AI 消息和对应的工具消息。

    复刻 LangChain 的 _fetch_last_ai_and_tool_messages 函数。

    Args:
        messages: 消息列表

    Returns:
        tuple: (最后的 AI 消息, 其后的工具消息列表)

    Examples:
        >>> msgs = [user_msg, ai_msg, tool_msg1, tool_msg2]
        >>> ai_msg, tool_msgs = fetch_last_ai_and_tool_messages(msgs)
        >>> # ai_msg 是 ai_msg
        >>> # tool_msgs 是 [tool_msg1, tool_msg2]
    """
    last_ai_message = None
    last_ai_index = -1

    # 从后往前找最后的 AI 消息
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        role_val = msg.role if isinstance(msg.role, str) else msg.role.value
        if role_val == "assistant":
            last_ai_message = msg
            last_ai_index = i
            break

    if last_ai_message is None:
        return None, []

    # 收集该 AI 消息之后的所有 tool 消息
    tool_messages = []
    for msg in messages[last_ai_index + 1:]:
        role_val = msg.role if isinstance(msg.role, str) else msg.role.value
        if role_val == "tool":
            tool_messages.append(msg)

    return last_ai_message, tool_messages


def get_pending_tool_calls(messages: List[Message]) -> List[dict]:
    """
    获取待处理的工具调用（没有对应 tool 消息的 tool_calls）。

    复刻 LangChain 的 pending_tool_calls 检查逻辑。

    Args:
        messages: 消息列表

    Returns:
        List[dict]: 待处理的工具调用列表

    Examples:
        >>> msgs = [user_msg, ai_msg_with_tool_calls, tool_msg1]
        >>> pending = get_pending_tool_calls(msgs)
        >>> # 返回 ai_msg_with_tool_calls 中没有对应 tool 消息的 tool_calls
    """
    last_ai_message, tool_messages = fetch_last_ai_and_tool_messages(messages)

    if not last_ai_message or not last_ai_message.tool_calls:
        return []

    # 收集已执行的 tool_call_id
    executed_tool_call_ids = set()
    for msg in tool_messages:
        if msg.tool_call_id:
            executed_tool_call_ids.add(msg.tool_call_id)

    # 找出未执行的 tool_calls
    pending_calls = []
    for tc in last_ai_message.tool_calls:
        tc_id = tc.id if hasattr(tc, 'id') else tc.get('id') if isinstance(tc, dict) else None
        if tc_id and tc_id not in executed_tool_call_ids:
            pending_calls.append(tc if isinstance(tc, dict) else tc.dict())

    return pending_calls


def are_all_tool_calls_completed(messages: List[Message]) -> bool:
    """
    检查最后的 AI 消息的所有 tool_calls 是否都有对应的 tool 消息。

    Args:
        messages: 消息列表

    Returns:
        bool: 如果所有 tool_calls 都已完成返回 True，否则返回 False
    """
    return len(get_pending_tool_calls(messages)) == 0
