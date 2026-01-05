"""
OpenManus Memory System - Based on LangChain design

This module provides a unified memory management system inspired by LangChain's
Memory architecture, adapted for the resume optimization use case.

Components:
- langchain: Simplified LangChain-style message types and chat history
- ChatHistoryManager: Wrapper for managing conversation history
- ConversationStateManager: Manages conversation state and intent recognition
- MessageAdapter: Converts between OpenManus and LangChain message formats
- CheckpointSaver: Version snapshot and rollback mechanism
- EntityMemory: Entity extraction and memory for resume-related entities
"""

# LangChain-style components
from app.memory.langchain import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)

# OpenManus wrappers
from app.memory.chat_history_manager import ChatHistoryManager
from app.memory.conversation_state import (
    ConversationStateManager,
    ConversationState,
    Intent,
    OptimizationContext,
    ConversationContext,
)
from app.memory.message_adapter import MessageAdapter

# New components
from app.memory.checkpoint_saver import (
    CheckpointSaver,
    Checkpoint,
    ResumeSnapshot,
    Operation,
    CheckpointMetadata,
)
from app.memory.entity_memory import (
    EntityMemory,
    Skill,
    Company,
    Project,
    Targets,
    ExtractedEntities,
    Association,
)

__all__ = [
    # LangChain-style components
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "BaseChatMessageHistory",
    "InMemoryChatMessageHistory",
    # OpenManus wrappers
    "ChatHistoryManager",
    "ConversationStateManager",
    "ConversationState",
    "Intent",
    "OptimizationContext",
    "ConversationContext",
    "MessageAdapter",
    # Checkpoint mechanism
    "CheckpointSaver",
    "Checkpoint",
    "ResumeSnapshot",
    "Operation",
    "CheckpointMetadata",
    # Entity memory
    "EntityMemory",
    "Skill",
    "Company",
    "Project",
    "Targets",
    "ExtractedEntities",
    "Association",
]
