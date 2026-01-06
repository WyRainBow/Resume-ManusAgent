"""Message types - Complete LangChain implementation for OpenManus."""

from app.memory.langchain.messages.base import BaseMessage, BaseMessageChunk, merge_content
from app.memory.langchain.messages.human import HumanMessage, HumanMessageChunk
from app.memory.langchain.messages.ai import AIMessage, AIMessageChunk
from app.memory.langchain.messages.system import SystemMessage, SystemMessageChunk
from app.memory.langchain.messages.tool import (
    ToolMessage,
    ToolMessageChunk,
    ToolCall,
    ToolCallChunk,
    InvalidToolCall,
    tool_call,
    tool_call_chunk,
    invalid_tool_call,
    default_tool_parser,
    default_tool_chunk_parser,
)

__all__ = [
    "BaseMessage",
    "BaseMessageChunk",
    "HumanMessage",
    "HumanMessageChunk",
    "AIMessage",
    "AIMessageChunk",
    "SystemMessage",
    "SystemMessageChunk",
    "ToolMessage",
    "ToolMessageChunk",
    "ToolCall",
    "ToolCallChunk",
    "InvalidToolCall",
    "tool_call",
    "tool_call_chunk",
    "invalid_tool_call",
    "default_tool_parser",
    "default_tool_chunk_parser",
    "merge_content",
]
