"""WebSocket module for real-time communication.

This module provides:
- Connection management for WebSocket clients
- Session management for agent instances
- Message handling and routing
"""

from app.web.websocket.connection_manager import ConnectionManager, connection_manager
from app.web.websocket.session_manager import SessionManager, session_manager, AgentSession
from app.web.websocket.message_handler import MessageHandler

__all__ = [
    "ConnectionManager",
    "connection_manager",
    "SessionManager",
    "session_manager",
    "AgentSession",
    "MessageHandler",
]
