"""Chat history routes.

Provides endpoints for chat history management.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.memory.chat_history_manager import ChatHistoryManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


class HistoryResponse(BaseModel):
    """Chat history response."""

    session_id: str
    messages: list[dict[str, str]]
    count: int


class HistoryClearResponse(BaseModel):
    """History clear response."""

    session_id: str
    message: str


@router.get("/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str) -> HistoryResponse:
    """Get chat history for a session.

    Args:
        session_id: The session identifier

    Returns:
        HistoryResponse with messages
    """
    try:
        history_manager = ChatHistoryManager(session_id=session_id)
        messages = history_manager.get_messages()

        return HistoryResponse(
            session_id=session_id,
            messages=[
                {"role": m.role, "content": m.content}
                for m in messages
            ],
            count=len(messages),
        )
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting history: {e}",
        )


@router.delete("/{session_id}", response_model=HistoryClearResponse)
async def clear_history(session_id: str) -> HistoryClearResponse:
    """Clear chat history for a session.

    Args:
        session_id: The session identifier

    Returns:
        HistoryClearResponse with confirmation
    """
    try:
        history_manager = ChatHistoryManager(session_id=session_id)
        history_manager.clear_messages()
        await history_manager.save_checkpoint()

        return HistoryClearResponse(
            session_id=session_id,
            message="History cleared successfully",
        )
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing history: {e}",
        )


@router.post("/{session_id}/restore")
async def restore_history(session_id: str) -> dict[str, Any]:
    """Restore chat history from checkpoint.

    Args:
        session_id: The session identifier

    Returns:
        dict with restored message count
    """
    try:
        history_manager = ChatHistoryManager(session_id=session_id)
        await history_manager.restore_from_checkpoint()
        messages = history_manager.get_messages()

        return {
            "session_id": session_id,
            "message_count": len(messages),
            "messages": [
                {"role": m.role, "content": m.content}
                for m in messages
            ],
        }
    except Exception as e:
        logger.error(f"Error restoring history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error restoring history: {e}",
        )
