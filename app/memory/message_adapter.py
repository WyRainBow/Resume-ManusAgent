"""
Message Adapter - Convert between OpenManus and LangChain message formats
"""

from typing import List, Optional

from app.memory.langchain.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.schema import Message, Role


class MessageAdapter:
    """Adapter for converting between OpenManus Message and LangChain Message formats."""

    @staticmethod
    def to_langchain(message: Message) -> BaseMessage:
        """
        Convert OpenManus Message to LangChain Message.

        Args:
            message: OpenManus Message object

        Returns:
            LangChain BaseMessage (HumanMessage, AIMessage, or SystemMessage)
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
        else:
            # For tool messages, convert to AIMessage
            return AIMessage(content=content)

    @staticmethod
    def from_langchain(lc_message: BaseMessage) -> Message:
        """
        Convert LangChain Message to OpenManus Message.

        Args:
            lc_message: LangChain BaseMessage object

        Returns:
            OpenManus Message object
        """
        if isinstance(lc_message, HumanMessage):
            role = Role.USER
        elif isinstance(lc_message, AIMessage):
            role = Role.ASSISTANT
        elif isinstance(lc_message, SystemMessage):
            role = Role.SYSTEM
        else:
            role = Role.ASSISTANT

        return Message(
            role=role,
            content=lc_message.content,
        )

    @staticmethod
    def batch_to_langchain(messages: List[Message]) -> List[BaseMessage]:
        """Batch convert OpenManus Messages to LangChain Messages."""
        return [MessageAdapter.to_langchain(msg) for msg in messages]

    @staticmethod
    def batch_from_langchain(lc_messages: List[BaseMessage]) -> List[Message]:
        """Batch convert LangChain Messages to OpenManus Messages."""
        return [MessageAdapter.from_langchain(msg) for msg in lc_messages]
