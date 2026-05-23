"""Get session history use case."""

from __future__ import annotations

import logging

from pydantic import UUID4

from pnetai_chatbot.application.ports.history_repo_port import IHistoryRepository
from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository
from pnetai_chatbot.domain.entities.message import Message

logger = logging.getLogger(__name__)


class GetSessionHistoryUseCase:
    """Use case to retrieve the message history of a session with ownership checks."""

    def __init__(
        self,
        session_repository: ISessionRepository,
        history_repository: IHistoryRepository,
    ) -> None:
        """Initialize the GetSessionHistoryUseCase.

        Args:
            session_repository: The session database repository port.
            history_repository: The message history database repository port.
        """
        self._session_repo = session_repository
        self._history_repo = history_repository

    async def execute(
        self,
        session_id: UUID4,
        user_id: str | None = None,
        limit: int = 50,
        before_timestamp: str | None = None,
    ) -> list[Message]:
        """Execute the use case to fetch messages for a session.

        Args:
            session_id: The unique identifier of the session.
            user_id: Optional ID of the requesting user.
            limit: Maximum number of messages to return.
            before_timestamp: Optional cursor for pagination.

        Returns:
            List of Message entities chronologically ordered.

        Raises:
            ValueError: If the session is not found or user ownership validation fails.
        """
        if user_id is None:
            # Guests are not permitted to fetch persisted database history
            logger.warning(
                "Access denied: Unauthenticated guest cannot read session history."
            )
            raise ValueError("Guest users cannot load persisted session history.")

        session = await self._session_repo.get_by_id(session_id)
        if not session:
            logger.warning("Session not found: %s", session_id)
            raise ValueError("Session not found.")

        # Enforce strict ownership isolation
        if session.user_id != user_id:
            logger.warning(
                "Ownership validation failed: user %s attempted to "
                "load session %s belonging to %s",
                user_id,
                session_id,
                session.user_id,
            )
            raise ValueError("Access denied: You do not own this chat session.")

        logger.info(
            "Fetching messages for session %s (User: %s, Limit: %d)",
            session_id,
            user_id,
            limit,
        )
        return await self._history_repo.get_by_session(
            session_id=session_id,
            limit=limit,
            before_timestamp=before_timestamp,
        )
