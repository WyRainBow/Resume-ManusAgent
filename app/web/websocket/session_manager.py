"""Session manager for agent instances.

Manages agent sessions, state, and lifecycle per client.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from app.agent.manus import Manus
from app.memory.chat_history_manager import ChatHistoryManager

logger = logging.getLogger(__name__)


class AgentSession:
    """Represents a single agent session for a client.

    Attributes:
        client_id: Unique identifier for the client
        agent: The Manus agent instance
        history_manager: Chat history manager
        created_at: When the session was created
        last_active: Last activity timestamp
        is_running: Whether agent is currently executing
    """

    def __init__(
        self,
        client_id: str,
        agent: Manus,
        history_manager: ChatHistoryManager,
    ) -> None:
        """Initialize the agent session.

        Args:
            client_id: Unique identifier for the client
            agent: The Manus agent instance
            history_manager: Chat history manager
        """
        self.client_id = client_id
        self.agent = agent
        self.history_manager = history_manager
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.is_running = False
        self._stop_event = asyncio.Event()

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_active = datetime.now()

    async def stop(self) -> None:
        """Signal the agent to stop execution."""
        self._stop_event.set()
        self.is_running = False
        logger.info(f"Session stopped for client: {self.client_id}")

    def should_stop(self) -> bool:
        """Check if execution should stop."""
        return self._stop_event.is_set()

    def reset_stop_event(self) -> None:
        """Reset the stop event for new execution."""
        self._stop_event.clear()


class SessionManager:
    """Manages agent sessions for connected clients.

    Features:
    - Create and destroy sessions per client
    - Track session state and activity
    - Handle session lifecycle
    - Clean up inactive sessions
    """

    def __init__(self) -> None:
        """Initialize the session manager."""
        self._sessions: Dict[str, AgentSession] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_session(
        self,
        client_id: str,
        cv_path: str | None = None,
    ) -> AgentSession:
        """Get existing session or create a new one.

        Args:
            client_id: Unique identifier for the client
            cv_path: Optional path to CV file for context

        Returns:
            The AgentSession instance
        """
        async with self._lock:
            if client_id in self._sessions:
                session = self._sessions[client_id]
                session.update_activity()
                return session

            # Create new session
            return await self._create_session(client_id, cv_path)

    async def _create_session(
        self,
        client_id: str,
        cv_path: str | None = None,
    ) -> AgentSession:
        """Create a new agent session.

        Args:
            client_id: Unique identifier for the client
            cv_path: Optional path to CV file

        Returns:
            The new AgentSession instance
        """
        # Create agent instance
        agent = Manus(
            cv_path=cv_path,
            client_id=client_id,
        )

        # Create history manager (k=30 for sliding window)
        history_manager = ChatHistoryManager(k=30)

        # Create session
        session = AgentSession(
            client_id=client_id,
            agent=agent,
            history_manager=history_manager,
        )

        self._sessions[client_id] = session
        logger.info(f"Created new session for client: {client_id}")
        return session

    async def remove_session(self, client_id: str) -> None:
        """Remove a session.

        Args:
            client_id: The client ID whose session to remove
        """
        async with self._lock:
            if client_id in self._sessions:
                session = self._sessions[client_id]
                await session.stop()
                del self._sessions[client_id]
                logger.info(f"Removed session for client: {client_id}")

    async def stop_session(self, client_id: str) -> bool:
        """Signal a session to stop without removing it.

        Args:
            client_id: The client ID whose session to stop

        Returns:
            True if session was stopped, False if not found
        """
        async with self._lock:
            session = self._sessions.get(client_id)
            if session:
                await session.stop()
                return True
            return False

    def get_session(self, client_id: str) -> Optional[AgentSession]:
        """Get a session without creating if not exists.

        Args:
            client_id: The client ID

        Returns:
            The AgentSession if exists, None otherwise
        """
        return self._sessions.get(client_id)

    def has_session(self, client_id: str) -> bool:
        """Check if a session exists for a client.

        Args:
            client_id: The client ID

        Returns:
            True if session exists, False otherwise
        """
        return client_id in self._sessions

    @property
    def active_sessions(self) -> set[str]:
        """Get set of active session IDs."""
        return set(self._sessions.keys())

    @property
    def session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self._sessions)

    async def cleanup_inactive_sessions(
        self,
        max_idle_seconds: int = 3600,
    ) -> int:
        """Clean up sessions inactive for too long.

        Args:
            max_idle_seconds: Maximum idle time before cleanup

        Returns:
            Number of sessions cleaned up
        """
        async with self._lock:
            now = datetime.now()
            to_remove = []

            for client_id, session in self._sessions.items():
                idle_time = (now - session.last_active).total_seconds()
                if idle_time > max_idle_seconds:
                    to_remove.append(client_id)

            for client_id in to_remove:
                await self.remove_session(client_id)

            if to_remove:
                logger.info(
                    f"Cleaned up {len(to_remove)} inactive sessions: {to_remove}"
                )

            return len(to_remove)


# Global session manager instance
session_manager = SessionManager()
