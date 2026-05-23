"""History repository implementation using MongoDB."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pnetai_chatbot.application.ports.history_repo_port import IHistoryRepository
from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.infrastructure.persistence.mongodb.client import get_chat_client
from pnetai_chatbot.infrastructure.persistence.mongodb.schemas.message_schema import (
    message_to_mongo,
    mongo_to_message,
)

if TYPE_CHECKING:
    from pnetai_chatbot.domain.value_objects.session_id import SessionId

logger = logging.getLogger(__name__)


class HistoryRepository(IHistoryRepository):
    """MongoDB implementation of the message history repository using Motor."""

    def __init__(self, db: Any = None) -> None:
        """Initialize the HistoryRepository.

        Args:
            db: Optional MongoDB database instance.
        """
        self._db = db if db is not None else get_chat_client().db
        self._collection = self._db["chat_messages"]

    async def insert(self, message: Message) -> Message:
        """Insert a new message into the history.

        Args:
            message: The message entity to persist.

        Returns:
            The persisted message.
        """
        doc = message_to_mongo(message)
        await self._collection.insert_one(doc)
        logger.info(
            "Inserted chat message %s into session %s", message.id, message.session_id
        )

        # Update message count in ChatSession using update_one
        session_coll = self._db["chat_sessions"]
        from datetime import datetime

        await session_coll.update_one(
            {"_id": str(message.session_id)},
            {
                "$inc": {"message_count": 1},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        return message

    async def get_by_session(
        self,
        session_id: SessionId,
        limit: int = 50,
        before_timestamp: str | None = None,
    ) -> list[Message]:
        """Retrieve messages for a session.

        Args:
            session_id: The session identifier.
            limit: Maximum number of messages to return.
            before_timestamp: Optional cursor for pagination.

        Returns:
            List of messages ordered by timestamp ascending.
        """
        from datetime import datetime

        query: dict[str, Any] = {"session_id": str(session_id)}
        if before_timestamp:
            try:
                # Standard fromisoformat parsing (strip Z if present as fromisoformat supports it in Python 3.11)
                clean_ts = before_timestamp
                if before_timestamp.endswith("Z"):
                    clean_ts = before_timestamp[:-1] + "+00:00"
                before_dt = datetime.fromisoformat(clean_ts)
                query["timestamp"] = {"$lt": before_dt}
            except ValueError as e:
                logger.warning(
                    "Failed to parse before_timestamp: %s (%s)", before_timestamp, e
                )

        # Fetch in timestamp descending order first to apply the limit, then sort ascending for the prompt flow
        cursor = self._collection.find(query).sort("timestamp", -1)
        docs = await cursor.to_list(length=limit)

        # Map and reverse to maintain chronological order
        messages = [mongo_to_message(doc) for doc in docs]
        messages.reverse()
        return messages

    async def delete_by_session(self, session_id: SessionId) -> int:
        """Delete all messages for a session.

        Args:
            session_id: The session identifier.

        Returns:
            Number of deleted messages.
        """
        res = await self._collection.delete_many({"session_id": str(session_id)})
        deleted_count = res.deleted_count
        logger.info("Deleted %d messages for session %s", deleted_count, session_id)
        return deleted_count
