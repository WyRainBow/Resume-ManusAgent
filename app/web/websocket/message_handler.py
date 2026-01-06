"""WebSocket message handler.

Handles incoming WebSocket messages and routes them to appropriate handlers.
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from app.web.websocket.connection_manager import ConnectionManager
from app.web.websocket.session_manager import SessionManager, AgentSession
from app.web.streaming.agent_stream import StreamProcessor
from app.web.streaming.state_machine import AgentStateMachine

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles WebSocket messages for agent interaction.

    Features:
    - Route messages to appropriate handlers
    - Execute agent tasks
    - Manage history operations
    - Handle stop requests
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        session_manager: SessionManager,
        stream_processor: StreamProcessor,
    ) -> None:
        """Initialize the message handler.

        Args:
            connection_manager: The connection manager
            session_manager: The session manager
            stream_processor: The stream processor for agent execution
        """
        self._connection_manager = connection_manager
        self._session_manager = session_manager
        self._stream_processor = stream_processor

    async def handle_message(
        self,
        websocket: WebSocket,
        client_id: str,
        message: str | bytes | dict,
    ) -> None:
        """Handle an incoming WebSocket message.

        Args:
            websocket: The WebSocket connection
            client_id: The client identifier
            message: The received message
        """
        try:
            # Convert bytes to str if needed
            if isinstance(message, bytes):
                message = message.decode("utf-8")

            # Parse JSON if string, otherwise use dict directly
            if isinstance(message, str):
                data = json.loads(message)
            else:
                data = message

            message_type = data.get("type")

            logger.info(f"[{client_id}] Received message type: {message_type}")

            # Route to appropriate handler
            handler = self._get_handler(message_type)
            if handler:
                await handler(websocket, client_id, data)
            else:
                logger.warning(f"[{client_id}] Unknown message type: {message_type}")
                await self._send_error(
                    client_id,
                    f"Unknown message type: {message_type}",
                )

        except json.JSONDecodeError as e:
            logger.error(f"[{client_id}] Invalid JSON: {e}")
            await self._send_error(client_id, "Invalid JSON format")
        except Exception as e:
            logger.exception(f"[{client_id}] Error handling message: {e}")
            await self._send_error(client_id, str(e))

    async def handle_prompt(
        self,
        websocket: WebSocket,
        client_id: str,
        data: dict[str, Any],
    ) -> None:
        """Handle a prompt message from the client.

        Args:
            websocket: The WebSocket connection
            client_id: The client identifier
            data: The message data containing 'prompt'
        """
        prompt = data.get("prompt", "")
        cv_path = data.get("cv_path")

        if not prompt:
            await self._send_error(client_id, "Prompt is required")
            return

        # Get or create session
        session = await self._session_manager.get_or_create_session(
            client_id,
            cv_path=cv_path,
        )

        # Check if already running
        if session.is_running:
            await self._send_error(
                client_id,
                "Agent is already running. Wait for completion or send 'stop' first.",
            )
            return

        # Create state machine for this execution
        state_machine = AgentStateMachine(session.client_id)

        # Define event sender
        async def send_event(event_data: dict[str, Any]) -> None:
            await self._connection_manager.send_to_client(event_data, client_id)

        # Start streaming execution
        try:
            session.is_running = True
            session.reset_stop_event()

            await self._stream_processor.start_stream(
                session_id=client_id,
                agent=session.agent,
                state_machine=state_machine,
                event_sender=send_event,
                user_message=prompt,
            )
        except Exception as e:
            logger.exception(f"[{client_id}] Error starting stream: {e}")
            await self._send_error(client_id, f"Error starting agent: {e}")
            session.is_running = False

    async def handle_restore_history(
        self,
        websocket: WebSocket,
        client_id: str,
        data: dict[str, Any],
    ) -> None:
        """Handle a restore history request.

        Args:
            websocket: The WebSocket connection
            client_id: The client identifier
            data: The message data
        """
        session = self._session_manager.get_session(client_id)
        if not session:
            await self._send_error(client_id, "No session found")
            return

        try:
            # Restore chat history from checkpoint
            await session.history_manager.restore_from_checkpoint()
            messages = session.history_manager.get_messages()

            await self._connection_manager.send_to_client(
                {
                    "type": "history_restored",
                    "data": {
                        "message_count": len(messages),
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                    },
                },
                client_id,
            )
            logger.info(f"[{client_id}] History restored ({len(messages)} messages)")

        except Exception as e:
            logger.exception(f"[{client_id}] Error restoring history: {e}")
            await self._send_error(client_id, f"Error restoring history: {e}")

    async def handle_clear_history(
        self,
        websocket: WebSocket,
        client_id: str,
        data: dict[str, Any],
    ) -> None:
        """Handle a clear history request.

        Args:
            websocket: The WebSocket connection
            client_id: The client identifier
            data: The message data
        """
        session = self._session_manager.get_session(client_id)
        if not session:
            await self._send_error(client_id, "No session found")
            return

        try:
            session.history_manager.clear_messages()

            # Save new checkpoint
            await session.history_manager.save_checkpoint()

            await self._connection_manager.send_to_client(
                {
                    "type": "history_cleared",
                    "data": {"message": "Chat history cleared"},
                },
                client_id,
            )
            logger.info(f"[{client_id}] History cleared")

        except Exception as e:
            logger.exception(f"[{client_id}] Error clearing history: {e}")
            await self._send_error(client_id, f"Error clearing history: {e}")

    async def handle_stop(
        self,
        websocket: WebSocket,
        client_id: str,
        data: dict[str, Any],
    ) -> None:
        """Handle a stop request.

        Args:
            websocket: The WebSocket connection
            client_id: The client identifier
            data: The message data
        """
        # Stop the stream processor
        stopped = await self._stream_processor.stop_stream(client_id)

        # Also stop the session
        await self._session_manager.stop_session(client_id)

        if stopped:
            await self._connection_manager.send_to_client(
                {
                    "type": "stopped",
                    "data": {"message": "Agent execution stopped"},
                },
                client_id,
            )
            logger.info(f"[{client_id}] Agent stopped by user")
        else:
            await self._send_error(
                client_id,
                "No active agent execution to stop",
            )

    def _get_handler(self, message_type: str):
        """Get the handler function for a message type.

        Args:
            message_type: The type of message

        Returns:
            The handler function or None
        """
        handlers = {
            "prompt": self.handle_prompt,
            "restore_history": self.handle_restore_history,
            "clear_history": self.handle_clear_history,
            "stop": self.handle_stop,
        }
        return handlers.get(message_type)

    async def _send_error(
        self,
        client_id: str,
        message: str,
    ) -> None:
        """Send an error message to the client.

        Args:
            client_id: The client identifier
            message: The error message
        """
        await self._connection_manager.send_to_client(
            {
                "type": "error",
                "data": {"message": message},
            },
            client_id,
        )
