"""
LangChain Conversation Memory Integration

将 LangChain 的 ConversationBufferWindowMemory 集成到 OpenManus
保持 OpenManus 架构不变，只是用 LangChain 管理对话记忆
"""

from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory


class ConversationBufferWindowMemory:
    """Simple memory implementation compatible with newer langchain versions"""
    def __init__(self, k=10, return_messages=True, memory_key="history"):
        self.k = k
        self.return_messages = return_messages
        self.memory_key = memory_key
        self._history = InMemoryChatMessageHistory()

    @property
    def chat_memory(self):
        return self

    @property
    def messages(self):
        """Return messages for compatibility"""
        return self._history.messages

    def add_user_message(self, message):
        self._history.add_message(HumanMessage(content=message))

    def add_ai_message(self, message):
        self._history.add_message(AIMessage(content=message))

    def load_memory_variables(self, inputs):
        messages = self._history.messages
        if self.return_messages:
            return {self.memory_key: messages[-self.k*2:]}
        return {self.memory_key: str(messages[-self.k*2:])}

    def clear(self):
        self._history.clear()

from app.schema import Message, Role
from app.logger import logger


class LangChainMemoryAdapter:
    """
    LangChain Memory 适配器

    将 OpenManus 的 Message 格式转换为 LangChain 格式
    使用 ConversationBufferWindowMemory 管理对话历史
    """

    def __init__(self, k: int = 10, return_messages: bool = True):
        """
        Args:
            k: 保留最近 k 轮对话（默认 10 轮）
            return_messages: 是否返回消息对象（而不是字符串）
        """
        self.memory = ConversationBufferWindowMemory(
            k=k,
            return_messages=return_messages,
            memory_key="history"
        )
        self._conversation_running = False

    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self.memory.chat_memory.add_user_message(content)
        logger.debug(f"📝 LangChain Memory: 添加用户消息 ({len(content)} 字符)")

    def add_ai_message(self, content: str) -> None:
        """添加 AI 消息"""
        self.memory.chat_memory.add_ai_message(content)
        logger.debug(f"🤖 LangChain Memory: 添加 AI 消息 ({len(content)} 字符)")

    def add_message(self, message: Message) -> None:
        """添加 OpenManus Message 到 LangChain Memory"""
        if message.role == Role.USER:
            if message.content:
                self.add_user_message(message.content)
        elif message.role == Role.ASSISTANT:
            if message.content:
                self.add_ai_message(message.content)
        # 忽略 tool 消息（LangChain Memory 不直接支持）

    def add_messages(self, messages: List[Message]) -> None:
        """批量添加消息"""
        for msg in messages:
            self.add_message(msg)

    def get_messages(self) -> List[BaseMessage]:
        """获取 LangChain 格式的消息列表"""
        return self.memory.chat_memory.messages

    def get_memory_variables(self) -> dict:
        """获取记忆变量（用于注入到提示词）"""
        return self.memory.load_memory_variables({})

    def clear(self) -> None:
        """清空记忆"""
        self.memory.clear()
        logger.debug("🧹 LangChain Memory: 已清空")

    def get_conversation_summary(self, max_length: int = 200) -> str:
        """
        获取对话摘要（用于上下文注入）

        Args:
            max_length: 最大长度

        Returns:
            对话摘要字符串
        """
        messages = self.get_messages()
        if not messages:
            return ""

        # 提取最近几轮对话的关键信息
        summary_parts = []
        for msg in messages[-6:]:  # 最近 3 轮（6 条消息）
            if isinstance(msg, HumanMessage):
                content = msg.content[:50] if len(msg.content) > 50 else msg.content
                summary_parts.append(f"用户: {content}")
            elif isinstance(msg, AIMessage):
                # 只提取 AI 的关键回复（不是工具调用）
                content = msg.content[:50] if len(msg.content) > 50 else msg.content
                if content and not content.startswith("调用工具"):
                    summary_parts.append(f"AI: {content}")

        summary = "\n".join(summary_parts)
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary

    def should_wait_for_user(self, last_ai_message: Optional[str] = None) -> bool:
        """
        判断是否应该等待用户输入

        基于最后一条 AI 消息的内容判断：
        - 包含"请回答"、"请告诉我"等 -> 等待
        - 包含"问题"、"?" -> 等待
        - 工具调用完成但没有最终答案 -> 等待

        Args:
            last_ai_message: 最后一条 AI 消息内容

        Returns:
            是否应该等待用户输入
        """
        if not last_ai_message:
            # 如果没有提供消息，从 memory 中获取最后一条
            messages = self.get_messages()
            if messages and isinstance(messages[-1], AIMessage):
                last_ai_message = messages[-1].content

        if not last_ai_message:
            return False

        wait_keywords = [
            "请回答", "请告诉我", "请提供", "请描述",
            "问题", "?", "？",
            "我最建议先回答",
            "等待您的", "需要您",
            "请告诉我您", "请回答", "请提供",
        ]

        message_lower = last_ai_message.lower()
        has_wait_keyword = any(kw in message_lower for kw in wait_keywords)

        # 如果包含等待关键词，且消息长度适中（不是工具调用结果），则等待
        # 长度检查：至少 10 字符（避免太短），最多 500 字符（避免是工具调用结果）
        if has_wait_keyword and 10 <= len(last_ai_message) < 500:
            logger.info(f"⏸️ LangChain Memory: 检测到需要等待用户输入 - {last_ai_message[:50]}...")
            return True

        return False

