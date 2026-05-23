"""API router exposing chat session overview, history logs, and session management."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import UUID4

from pnetai_chatbot.application.use_cases.chat.get_session_history import (
    GetSessionHistoryUseCase,
)
from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.interface.api.v1.dependencies import (
    get_current_user,
    get_get_history_use_case,
    get_session_repository,
)
from pnetai_chatbot.interface.schemas.session_schema import (
    HistoryResponse,
    MessageItemSchema,
    SessionListResponse,
    SessionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/sessions", response_model=SessionListResponse, tags=["Sessions"])
async def list_sessions(
    user: User = Depends(get_current_user),
    session_repo: Any = Depends(get_session_repository),
) -> SessionListResponse:
    """List all persisted chat sessions belonging to the authenticated user.

    Args:
        user: The current authenticated or guest user.
        session_repo: Concrete database repository port.

    Returns:
        SessionListResponse containing chronological session summaries.

    Raises:
        HTTPException: 401 if request is unauthenticated.
    """
    if not user.is_authenticated or not user.id:
        logger.warning("Unauthenticated request blocked on GET /sessions")
        raise HTTPException(
            status_code=401,
            detail="Authentication required for this operation",
        )

    try:
        sessions = await session_repo.list_by_user(user.id)
        response_items = []
        for s in sessions:
            response_items.append(
                SessionResponse(
                    id=s.id,
                    created_at=s.created_at,
                    message_count=s.message_count,
                    summary=s.summary,
                    updated_at=s.updated_at,
                )
            )
        return SessionListResponse(sessions=response_items)
    except Exception as e:
        logger.error("Failed to list sessions: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Internal database query failed: {e}",
        )


@router.get(
    "/sessions/{session_id}/history",
    response_model=HistoryResponse,
    tags=["Sessions"],
)
async def get_session_history(
    session_id: UUID4,
    limit: int = Query(default=50, ge=1, le=100),
    before_timestamp: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    session_repo: Any = Depends(get_session_repository),
    history_use_case: GetSessionHistoryUseCase = Depends(get_get_history_use_case),
) -> HistoryResponse:
    """Chronologically retrieve the full message history for a persisted session.

    Args:
        session_id: Target session UUID4 string.
        limit: Max quantity of historical messages to retrieve.
        before_timestamp: Cursor timestamp to retrieve messages before.
        user: Current authenticated or guest user context.
        session_repo: Session Repository port.
        history_use_case: GetSessionHistoryUseCase injector.

    Returns:
        HistoryResponse detailing messages and the session summary.

    Raises:
        HTTPException: 401 if unauthenticated, 403 on ownership failure,
          404 if not found.
    """
    if not user.is_authenticated or not user.id:
        logger.warning(
            "Guest blocked from fetching persisted history for session: %s",
            session_id,
        )
        raise HTTPException(
            status_code=401,
            detail="Guest users cannot load persisted session history.",
        )

    # Validate session exists and is owned by the requesting user
    session = await session_repo.get_by_id(session_id)
    if not session:
        logger.warning("Session %s not found", session_id)
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    if session.user_id != user.id:
        logger.warning(
            "User %s denied access to session %s (owned by %s)",
            user.id,
            session_id,
            session.user_id,
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: You do not own this chat session.",
        )

    try:
        messages = await history_use_case.execute(
            session_id=session_id,
            user_id=user.id,
            limit=limit,
            before_timestamp=before_timestamp,
        )

        message_items = []
        for msg in messages:
            role_str = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            # Standardize tool calls to dictionary list
            tool_calls_dict = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_dict.append(
                        {
                            "tool_name": tc.tool_name,
                            "input_summary": tc.input_summary,
                            "output_summary": tc.output_summary,
                            "execution_time_ms": tc.execution_time_ms,
                            "data": tc.data,
                            "success": tc.success,
                            "error_message": tc.error_message,
                        }
                    )

            message_items.append(
                MessageItemSchema(
                    role=role_str,
                    content=msg.content,
                    timestamp=msg.timestamp,
                    tool_calls=tool_calls_dict,
                )
            )

        return HistoryResponse(
            session_id=session_id,
            messages=message_items,
            summary=session.summary,
        )

    except ValueError as e:
        logger.warning("Value error encountered: %s", e)
        err_msg = str(e)
        if "Access denied" in err_msg or "own" in err_msg:
            raise HTTPException(status_code=403, detail=err_msg)
        if "Guest" in err_msg:
            raise HTTPException(status_code=401, detail=err_msg)
        raise HTTPException(status_code=404, detail=err_msg)


@router.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(
    session_id: UUID4,
    user: User = Depends(get_current_user),
    session_repo: Any = Depends(get_session_repository),
) -> dict[str, str]:
    """Delete a chat session and trigger cascade deletion of its history messages.

    Args:
        session_id: Target session UUID4 string.
        user: Current authenticated or guest user context.
        session_repo: Session Repository port.

    Returns:
        Status dict confirmation.

    Raises:
        HTTPException: 401 if unauthenticated, 403 on ownership failure,
          404 if not found.
    """
    if not user.is_authenticated or not user.id:
        logger.warning("Guest blocked from deleting session: %s", session_id)
        raise HTTPException(
            status_code=401,
            detail="Guest users cannot delete database sessions.",
        )

    session = await session_repo.get_by_id(session_id)
    if not session:
        logger.warning("Session %s not found for deletion", session_id)
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    if session.user_id != user.id:
        logger.warning(
            "User %s denied delete permission for session %s (owned by %s)",
            user.id,
            session_id,
            session.user_id,
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: You do not own this chat session.",
        )

    try:
        await session_repo.delete(session_id)
        logger.info(
            "Cascade deleted session %s and message history (User: %s)",
            session_id,
            user.id,
        )
        return {
            "status": "success",
            "message": (
                f"Session {session_id} and all related message logs "
                "successfully deleted."
            ),
        }
    except Exception as e:
        logger.error("Database deletion failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Internal database deletion failed: {e}",
        )
