"""Session repository implementation using MongoDB."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository
from pnetai_chatbot.domain.entities.session import ChatSession
from pnetai_chatbot.infrastructure.persistence.mongodb.client import get_chat_client
from pnetai_chatbot.infrastructure.persistence.mongodb.schemas.session_schema import (
    mongo_to_session,
    session_to_mongo,
)

if TYPE_CHECKING:
    from pnetai_chatbot.domain.value_objects.session_id import SessionId

logger = logging.getLogger(__name__)


class SessionRepository(ISessionRepository):
    """MongoDB implementation of the chat session repository using Motor."""

    def __init__(self, db: Any = None) -> None:
        """Initialize the SessionRepository.

        Args:
            db: Optional MongoDB database instance.
        """
        self._db = db if db is not None else get_chat_client().db
        self._collection = self._db["chat_sessions"]

    async def create(self, session: ChatSession) -> ChatSession:
        """Persist a new chat session.

        Args:
            session: The session entity to persist.

        Returns:
            The persisted session.
        """
        doc = session_to_mongo(session)
        await self._collection.insert_one(doc)
        logger.info("Created chat session: %s", session.id)
        return session

    async def get_by_id(self, session_id: SessionId) -> ChatSession | None:
        """Retrieve a session by its ID.

        Args:
            session_id: The session identifier.

        Returns:
            The session if found, None otherwise.
        """
        doc = await self._collection.find_one({"_id": str(session_id)})
        if not doc:
            return None
        return mongo_to_session(doc)

    async def update_summary(self, session_id: SessionId, summary: str) -> None:
        """Update the summary for a session.

        Args:
            session_id: The session identifier.
            summary: The new summary text.
        """
        from datetime import datetime

        now = datetime.utcnow()
        await self._collection.update_one(
            {"_id": str(session_id)},
            {"$set": {"summary": summary, "updated_at": now}},
        )
        logger.info("Updated summary for session: %s", session_id)

    async def list_by_user(self, user_id: str) -> list[ChatSession]:
        """List all sessions belonging to a user.

        Args:
            user_id: The user identifier.

        Returns:
            List of chat sessions sorted by updated_at descending.
        """
        cursor = self._collection.find({"user_id": user_id}).sort("updated_at", -1)
        docs = await cursor.to_list(length=100)
        return [mongo_to_session(doc) for doc in docs]

    async def delete(self, session_id: SessionId) -> None:
        """Delete a session and all its messages.

        Args:
            session_id: The session identifier.
        """
        # Delete session
        await self._collection.delete_one({"_id": str(session_id)})

        # Delete corresponding messages cascade
        # Import dynamically to avoid circular import issues
        from pnetai_chatbot.infrastructure.persistence.mongodb.history_repo import (
            HistoryRepository,
        )

        history_repo = HistoryRepository(self._db)
        await history_repo.delete_by_session(session_id)
        logger.info("Deleted session %s and all its messages", session_id)
