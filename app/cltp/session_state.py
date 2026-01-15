"""
CLTP Session State Management
会话状态管理（内存中，无需 Redis）
"""

from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionState:
    """会话状态（内存中）"""
    conversation_id: str
    span_stack: List[str] = field(default_factory=list)  # 当前打开的 span ID 栈
    message_sequence: Dict[str, int] = field(default_factory=dict)  # channel -> sequence
    current_run_span_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


# 全局会话状态存储（内存中）
_active_sessions: Dict[str, SessionState] = {}


def get_or_create_session(conversation_id: str) -> SessionState:
    """获取或创建会话状态"""
    if conversation_id not in _active_sessions:
        _active_sessions[conversation_id] = SessionState(conversation_id=conversation_id)
    return _active_sessions[conversation_id]


def cleanup_session(conversation_id: str) -> None:
    """清理会话状态"""
    _active_sessions.pop(conversation_id, None)
