"""MongoDB schema mapping for ChatSession."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pnetai_chatbot.domain.entities.session import ChatSession


def session_to_mongo(session: ChatSession) -> dict[str, Any]:
    """Convert ChatSession domain entity to MongoDB document dict.

    Args:
        session: The ChatSession domain entity.

    Returns:
        A dictionary representation suitable for MongoDB.
    """
    return {
        "_id": str(session.id),
        "user_id": session.user_id,
        "is_authenticated": session.is_authenticated,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "message_count": session.message_count,
        "summary": session.summary,
        "metadata": session.metadata,
    }


def mongo_to_session(doc: dict[str, Any]) -> ChatSession:
    """Convert MongoDB document dict to ChatSession domain entity.

    Args:
        doc: The MongoDB document dictionary.

    Returns:
        The reconstructed ChatSession domain entity.
    """
    return ChatSession(
        id=UUID(doc["_id"]),
        user_id=doc.get("user_id"),
        is_authenticated=doc.get("is_authenticated", False),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        message_count=doc.get("message_count", 0),
        summary=doc.get("summary"),
        metadata=doc.get("metadata", {}),
    )
