"""Streaming module for agent execution events.

This module provides:
- Event types and data models for streaming
- Agent execution state management
- State machine for agent lifecycle
- Stream output handler
"""

from app.web.streaming.events import (
    EventType,
    StreamEvent,
    ThoughtEvent,
    ToolCallEvent,
    ToolResultEvent,
    AnswerEvent,
    AgentStartEvent,
    AgentEndEvent,
    AgentErrorEvent,
    SystemEvent,
)
from app.web.streaming.agent_state import (
    AgentState,
    StateInfo,
    StateTransitionError,
)
from app.web.streaming.state_machine import AgentStateMachine
from app.web.streaming.agent_stream import AgentStream, StreamProcessor, EventSender

__all__ = [
    # Events
    "EventType",
    "StreamEvent",
    "ThoughtEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "AnswerEvent",
    "AgentStartEvent",
    "AgentEndEvent",
    "AgentErrorEvent",
    "SystemEvent",
    # State
    "AgentState",
    "StateInfo",
    "StateTransitionError",
    "AgentStateMachine",
    # Streaming
    "AgentStream",
    "StreamProcessor",
    "EventSender",
]
