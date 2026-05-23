"""Resolve user context use case."""

from __future__ import annotations

import logging
from uuid import UUID

from pydantic import UUID4

from pnetai_chatbot.application.ports.history_repo_port import IHistoryRepository
from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository
from pnetai_chatbot.application.services.permission_service import PermissionService
from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.session import ChatSession

logger = logging.getLogger(__name__)


class ResolveUserContextUseCase:
    """Use case to coordinate authorization scopes at endpoint load."""

    def __init__(
        self,
        session_repository: ISessionRepository,
        history_repository: IHistoryRepository,
        permission_service: PermissionService,
    ) -> None:
        """Initialize the ResolveUserContextUseCase.

        Args:
            session_repository: The session database repository port.
            history_repository: The message history database repository port.
            permission_service: The service to check user permissions.
        """
        self._session_repo = session_repository
        self._history_repo = history_repository
        self._permission_service = permission_service

    async def execute(
        self,
        session_id: UUID4 | str | None = None,
        user_id: str | None = None,
    ) -> tuple[ChatSession, list[Message]]:
        """Resolve a session based on the requested session ID and user ID.

        Args:
            session_id: The ID of the session, if requested.
            user_id: The ID of the authenticated user, or None if guest.

        Returns:
            A tuple of (ChatSession, list[Message]) representing
            the active session and its history.

        Raises:
            ValueError: If ownership check fails or the session is not found.
        """
        is_auth = user_id is not None

        if not is_auth:
            # Guest user: completely ephemeral session, ignore any database fetch
            logger.info("Resolving guest context: creating ephemeral session")
            session = ChatSession.create_ephemeral()
            return session, []

        # Authenticated user
        if session_id is None:
            # Create a brand new persistent session
            logger.info(
                "Resolving auth context: creating new persistent session for %s",
                user_id,
            )
            session = ChatSession.create(user_id=user_id)
            session = await self._session_repo.create(session)
            return session, []

        # Find existing session in database
        logger.info(
            "Resolving auth context: loading session %s for user %s",
            session_id,
            user_id,
        )
        # Parse session_id to UUID if it's a string
        target_id = session_id
        if isinstance(target_id, str):
            try:
                target_id = UUID(target_id)
            except ValueError as e:
                raise ValueError("Invalid session ID format.") from e

        session = await self._session_repo.get_by_id(target_id)
        if not session:
            logger.warning("Session not found in DB: %s", target_id)
            # Create a brand new session with this session_id for the user
            session = ChatSession.create(user_id=user_id)
            session.id = target_id
            session = await self._session_repo.create(session)
            return session, []

        # Validate ownership
        if session.user_id != user_id:
            logger.warning(
                "Access denied: Session %s belongs to %s, but user %s requested it",
                target_id,
                session.user_id,
                user_id,
            )
            raise ValueError("Access denied: You do not own this chat session.")

        # Load message history
        messages = await self._history_repo.get_by_session(session_id=target_id)
        return session, messages
