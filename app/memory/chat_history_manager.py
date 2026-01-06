"""
Chat History Manager - Wrapper around LangChain-style InMemoryChatMessageHistory

Provides OpenManus-compatible interface for managing conversation history.
Implements LangChain-compatible sliding window mechanism.
"""

from typing import List, Optional

from app.memory.langchain.chat_history import InMemoryChatMessageHistory
from app.memory.langchain.messages.utils import trim_messages
from app.schema import Message
from app.memory.message_adapter import MessageAdapter
from app.logger import logger


class ChatHistoryManager:
    """
    Chat history manager based on LangChain-style InMemoryChatMessageHistory.

    Features:
    - Sliding window (keep only last k messages) - LangChain compatible
    - Message format conversion (OpenManus <-> LangChain)
    - Context retrieval for LLM prompting
    - Automatic trimming when messages exceed k limit
    """

    def __init__(self, k: int = 10, include_system: bool = True):
        """
        Initialize the chat history manager.

        Args:
            k: Maximum number of messages to keep (default: 10).
                Note: This is the total number of messages, not conversation turns.
                A turn typically consists of 2+ messages (user + assistant + tool).
            include_system: Whether to preserve SystemMessage at index 0
                outside of the k limit (default: True).
        """
        self.k = k
        self.include_system = include_system
        self._history = InMemoryChatMessageHistory()

    def _trim_history(self) -> None:
        """
        Apply sliding window to trim messages exceeding k limit.

        Uses LangChain's trim_messages with strategy='last' to keep
        the most recent messages while preserving SystemMessage if configured.
        """
        if len(self._history.messages) > self.k:
            trimmed = trim_messages(
                self._history.messages,
                max_messages=self.k,
                strategy="last",
                include_system=self.include_system,
            )
            # Update the internal messages list
            self._history._messages = trimmed
            logger.debug(f"✂️ ChatHistory: Trimmed to {len(trimmed)} messages (k={self.k})")

    def add_message(self, message: Message) -> None:
        """Add an OpenManus Message to the history.

        After adding, automatically trims history if it exceeds k messages.
        """
        lc_message = MessageAdapter.to_langchain(message)
        self._history.add_message(lc_message)
        logger.debug(f"📝 ChatHistory: Added {message.role} message ({len(message.content or '')} chars)")

        # Apply sliding window
        self._trim_history()

    def add_messages(self, messages: List[Message]) -> None:
        """Add multiple OpenManus Messages to the history.

        After adding, automatically trims history if it exceeds k messages.
        """
        lc_messages = MessageAdapter.batch_to_langchain(messages)
        self._history.add_messages(lc_messages)
        logger.debug(f"📝 ChatHistory: Added {len(messages)} messages")

        # Apply sliding window
        self._trim_history()

    def get_messages(self, max_messages: Optional[int] = None) -> List[Message]:
        """
        Get messages from the history.

        Args:
            max_messages: Optional maximum number of messages to return.
                If None, returns all messages (already trimmed by k).
                Uses trim_messages for consistent behavior.

        Returns:
            List of OpenManus Messages
        """
        lc_messages = self._history.messages

        # If max_messages specified, use trim_messages for consistent trimming
        if max_messages is not None:
            lc_messages = trim_messages(
                lc_messages,
                max_messages=max_messages,
                strategy="last",
                include_system=self.include_system,
            )

        return MessageAdapter.batch_from_langchain(lc_messages)

    def get_recent_context(self, max_turns: int = 5) -> str:
        """
        Get recent conversation context as a string.

        Args:
            max_turns: Maximum number of turns to include (default: 5)
                A turn typically consists of 2 messages (user + assistant).

        Returns:
            Formatted conversation context string
        """
        # Use trim_messages for consistent behavior
        messages = self.get_messages(max_messages=max_turns * 2)
        if not messages:
            return ""

        context_parts = []
        for msg in messages:
            role_name = "用户" if msg.role == "user" else "AI"
            content = msg.content or ""
            if content:
                content = content[:100] + "..." if len(content) > 100 else content
                context_parts.append(f"{role_name}: {content}")

        return "\n".join(context_parts)

    def clear(self) -> None:
        """Clear all messages from the history."""
        self._history.clear()
        logger.debug("🧹 ChatHistory: Cleared all messages")

    @property
    def message_count(self) -> int:
        """Get the total number of messages in the history."""
        return len(self._history.messages)

