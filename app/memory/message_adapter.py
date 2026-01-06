"""
Message Adapter - Convert between OpenManus and LangChain message formats
"""

from typing import List, Optional

from app.memory.langchain.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from app.schema import Message, Role


class MessageAdapter:
    """Adapter for converting between OpenManus Message and LangChain Message formats.

    Critical: Tool messages are now properly preserved to enable the optimization workflow:
    - Analysis results (education_analyzer, cv_analyzer_agent) contain optimization_suggestions JSON
    - These tool results must be preserved across conversation turns
    - When user says "优化", the agent needs to retrieve previous tool results
    """

    @staticmethod
    def to_langchain(message: Message) -> BaseMessage:
        """
        Convert OpenManus Message to LangChain Message.

        Args:
            message: OpenManus Message object

        Returns:
            LangChain BaseMessage (HumanMessage, AIMessage, SystemMessage, or ToolMessage)
        """
        content = message.content or ""

        if message.role == Role.USER:
            return HumanMessage(content=content)
        elif message.role == Role.ASSISTANT:
            return AIMessage(
                content=content,
                tool_calls=message.tool_calls or []
            )
        elif message.role == Role.SYSTEM:
            return SystemMessage(content=content)
        elif message.role == Role.TOOL:
            # Preserve tool messages with their metadata
            return ToolMessage(
                content=content,
                tool_call_id=message.tool_call_id or "",
                name=message.name or ""
            )
        else:
            # Fallback
            return AIMessage(content=content)

    @staticmethod
    def from_langchain(lc_message: BaseMessage) -> Message:
        """
        Convert LangChain Message to OpenManus Message.

        Args:
            lc_message: LangChain BaseMessage object

        Returns:
            OpenManus Message object with all metadata preserved
        """
        if isinstance(lc_message, HumanMessage):
            role = Role.USER
            return Message(role=role, content=lc_message.content)
        elif isinstance(lc_message, AIMessage):
            role = Role.ASSISTANT
            return Message(
                role=role,
                content=lc_message.content,
                tool_calls=lc_message.tool_calls or None
            )
        elif isinstance(lc_message, SystemMessage):
            role = Role.SYSTEM
            return Message(role=role, content=lc_message.content)
        elif isinstance(lc_message, ToolMessage):
            role = Role.TOOL
            return Message(
                role=role,
                content=lc_message.content,
                tool_call_id=lc_message.tool_call_id or None,
                name=lc_message.name or None
            )
        else:
            # Fallback
            return Message(role=Role.ASSISTANT, content=lc_message.content)

    @staticmethod
    def batch_to_langchain(messages: List[Message]) -> List[BaseMessage]:
        """Batch convert OpenManus Messages to LangChain Messages."""
        return [MessageAdapter.to_langchain(msg) for msg in messages]

    @staticmethod
    def batch_from_langchain(lc_messages: List[BaseMessage]) -> List[Message]:
        """Batch convert LangChain Messages to OpenManus Messages."""
        return [MessageAdapter.from_langchain(msg) for msg in lc_messages]
