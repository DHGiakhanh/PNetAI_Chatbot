"""Create session use case."""

from __future__ import annotations

import logging
from typing import Any

from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository
from pnetai_chatbot.domain.entities.session import ChatSession

logger = logging.getLogger(__name__)


class CreateSessionUseCase:
    """Use case to create a new chat session."""

    def __init__(self, session_repository: ISessionRepository) -> None:
        """Initialize the CreateSessionUseCase.

        Args:
            session_repository: The session database repository port.
        """
        self._session_repo = session_repository

    async def execute(
        self,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatSession:
        """Execute the use case to create and persist (or return ephemeral) session.

        Args:
            user_id: Optional ID of the authenticated user.
            metadata: Optional additional metadata dictionary.

        Returns:
            The created ChatSession entity.
        """
        if user_id is None:
            # Ephemeral session for guest users (not persisted)
            logger.info("Creating ephemeral guest session")
            return ChatSession.create_ephemeral()

        # Persistent session for authenticated users
        logger.info("Creating persistent session for user: %s", user_id)
        session = ChatSession.create(user_id=user_id, metadata=metadata)
        return await self._session_repo.create(session)
