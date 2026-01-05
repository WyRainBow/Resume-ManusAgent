"""
Chat History - Simplified from LangChain

This is a simplified implementation of LangChain's chat history,
adapted for OpenManus use case.
"""

from typing import List
from abc import ABC, abstractmethod
from app.memory.langchain.messages import BaseMessage


class BaseChatMessageHistory(ABC):
    """Abstract base class for chat message history."""

    @abstractmethod
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the history."""

    @abstractmethod
    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add multiple messages to the history."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all messages from the history."""

    @property
    @abstractmethod
    def messages(self) -> List[BaseMessage]:
        """Get all messages in the history."""


class InMemoryChatMessageHistory(BaseChatMessageHistory):
    """In-memory implementation of chat message history."""

    def __init__(self) -> None:
        self._messages: List[BaseMessage] = []

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the history."""
        self._messages.append(message)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add multiple messages to the history."""
        self._messages.extend(messages)

    def clear(self) -> None:
        """Clear all messages from the history."""
        self._messages = []

    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages in the history."""
        return self._messages


__all__ = ["BaseChatMessageHistory", "InMemoryChatMessageHistory"]
