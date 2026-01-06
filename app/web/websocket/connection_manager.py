"""WebSocket connection manager.

Manages WebSocket connections, broadcasting, and connection lifecycle.
Based on FastAPI WebSocket best practices.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting.

    Features:
    - Track active connections by client_id
    - Send messages to specific clients
    - Broadcast messages to all connections
    - Graceful connection cleanup
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        # client_id -> WebSocket mapping
        self._connections: Dict[str, WebSocket] = {}
        # Track connections for debugging/stats
        self._connection_count = 0

    @property
    def active_connections(self) -> Set[str]:
        """Get set of active client IDs."""
        return set(self._connections.keys())

    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self._connections)

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect a new WebSocket client.

        Args:
            websocket: The WebSocket connection instance
            client_id: Unique identifier for the client
        """
        await websocket.accept()
        self._connections[client_id] = websocket
        self._connection_count += 1
        logger.info(f"Client connected: {client_id} (total: {self.connection_count})")

    def disconnect(self, client_id: str) -> None:
        """Disconnect a client.

        Args:
            client_id: Unique identifier for the client to disconnect
        """
        if client_id in self._connections:
            del self._connections[client_id]
            logger.info(f"Client disconnected: {client_id} (total: {self.connection_count})")

    async def send_to_client(
        self,
        message: dict | str,
        client_id: str,
    ) -> bool:
        """Send a message to a specific client.

        Args:
            message: The message to send (dict or str)
            client_id: The target client ID

        Returns:
            True if message was sent successfully, False otherwise
        """
        websocket = self._connections.get(client_id)
        if not websocket:
            logger.warning(f"Client not found: {client_id}")
            return False

        try:
            if isinstance(message, dict):
                import json
                await websocket.send_json(message)
            else:
                await websocket.send_text(message)
            return True
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")
            # Clean up broken connection
            self.disconnect(client_id)
            return False

    async def broadcast(self, message: dict | str) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        if not self._connections:
            return

        # Create tasks for all sends
        tasks = [
            self.send_to_client(message, client_id)
            for client_id in self.active_connections
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def send_to_all_except(
        self,
        message: dict | str,
        exclude_client_id: str,
    ) -> None:
        """Send a message to all clients except one.

        Args:
            message: The message to send
            exclude_client_id: The client ID to exclude
        """
        tasks = [
            self.send_to_client(message, client_id)
            for client_id in self.active_connections
            if client_id != exclude_client_id
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    def is_connected(self, client_id: str) -> bool:
        """Check if a client is currently connected.

        Args:
            client_id: The client ID to check

        Returns:
            True if client is connected, False otherwise
        """
        return client_id in self._connections

    def get_websocket(self, client_id: str) -> WebSocket | None:
        """Get the WebSocket for a specific client.

        Args:
            client_id: The client ID

        Returns:
            The WebSocket instance if connected, None otherwise
        """
        return self._connections.get(client_id)


# Global connection manager instance
connection_manager = ConnectionManager()
