"""
LangChain-style Memory System - Simplified version for OpenManus

This is a simplified implementation inspired by LangChain's Memory design,
with minimal dependencies for the resume optimization use case.
"""

from app.memory.langchain.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from app.memory.langchain.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory

__all__ = [
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    "BaseChatMessageHistory",
    "InMemoryChatMessageHistory",
]
