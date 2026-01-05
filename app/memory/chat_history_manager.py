"""
Chat History Manager - Wrapper around LangChain-style InMemoryChatMessageHistory

Provides OpenManus-compatible interface for managing conversation history.
"""

from typing import List, Optional

from app.memory.langchain.chat_history import InMemoryChatMessageHistory
from app.memory.langchain.messages import BaseMessage, AIMessage
from app.schema import Message
from app.memory.message_adapter import MessageAdapter
from app.logger import logger


class ChatHistoryManager:
    """
    Chat history manager based on LangChain-style InMemoryChatMessageHistory.

    Features:
    - Sliding window (keep only last k messages)
    - Message format conversion (OpenManus <-> LangChain)
    - Context retrieval for LLM prompting
    """

    def __init__(self, k: int = 10):
        """
        Initialize the chat history manager.

        Args:
            k: Maximum number of conversation turns to keep (default: 10)
        """
        self.k = k
        self._history = InMemoryChatMessageHistory()

    def add_message(self, message: Message) -> None:
        """Add an OpenManus Message to the history."""
        lc_message = MessageAdapter.to_langchain(message)
        self._history.add_message(lc_message)
        logger.debug(f"📝 ChatHistory: Added {message.role} message ({len(message.content or '')} chars)")

    def add_messages(self, messages: List[Message]) -> None:
        """Add multiple OpenManus Messages to the history."""
        lc_messages = MessageAdapter.batch_to_langchain(messages)
        self._history.add_messages(lc_messages)
        logger.debug(f"📝 ChatHistory: Added {len(messages)} messages")

    def get_messages(self, window: Optional[int] = None) -> List[Message]:
        """
        Get messages from the history.

        Args:
            window: Optional window size (default: use self.k)

        Returns:
            List of OpenManus Messages
        """
        lc_messages = self._history.messages
        if window:
            lc_messages = lc_messages[-window:]

        return MessageAdapter.batch_from_langchain(lc_messages)

    def get_recent_context(self, max_turns: int = 5) -> str:
        """
        Get recent conversation context as a string.

        Args:
            max_turns: Maximum number of turns to include (default: 5)

        Returns:
            Formatted conversation context string
        """
        messages = self.get_messages(window=max_turns * 2)
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

    def should_wait_for_user(self, last_ai_message: Optional[str] = None) -> bool:
        """
        Determine if the AI should wait for user input.

        Args:
            last_ai_message: Optional last AI message content

        Returns:
            True if should wait for user input
        """
        if not last_ai_message:
            messages = self._history.messages
            if messages and isinstance(messages[-1], AIMessage):
                last_ai_message = messages[-1].content

        if not last_ai_message:
            return False

        wait_keywords = [
            "请回答", "请告诉我", "请提供",
            "问题", "?", "？",
            "我最建议先回答",
            "等待您的", "需要您",
        ]

        message_lower = last_ai_message.lower()
        has_wait_keyword = any(kw in message_lower for kw in wait_keywords)

        # Check if message length is reasonable (not a tool call result)
        if has_wait_keyword and 10 <= len(last_ai_message) < 500:
            logger.info(f"⏸️ ChatHistory: Detected wait for user input")
            return True

        return False
