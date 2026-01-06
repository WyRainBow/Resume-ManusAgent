"""
Message types - Simplified from LangChain

This is a simplified implementation of LangChain's message types,
adapted for OpenManus use case.
"""

from typing import List, Sequence, Any, Dict, Optional
from pydantic import BaseModel, Field


class BaseMessage(BaseModel):
    """Base message class"""

    content: str
    additional_kwargs: dict = Field(default_factory=dict)

    def __str__(self) -> str:
        return self.content


class HumanMessage(BaseMessage):
    """Message from a human"""

    type: str = "human"


class AIMessage(BaseMessage):
    """Message from an AI"""

    type: str = "ai"
    tool_calls: List[Any] = Field(default_factory=list)


class SystemMessage(BaseMessage):
    """System message"""

    type: str = "system"


class ToolMessage(BaseMessage):
    """Message representing the result of a tool execution.

    This is critical for preserving tool results (like optimization suggestions)
    across WebSocket reconnections and conversation turns.
    """

    type: str = "tool"
    tool_call_id: str = ""
    name: str = ""

    def __init__(self, content: str, tool_call_id: str = "", name: str = "", **kwargs):
        super().__init__(content=content, tool_call_id=tool_call_id, name=name, **kwargs)


__all__ = ["BaseMessage", "HumanMessage", "AIMessage", "SystemMessage", "ToolMessage"]
