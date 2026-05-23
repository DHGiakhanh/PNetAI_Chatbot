"""MongoDB schema mapping for Message."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.tool_result import ToolCallResult
from pnetai_chatbot.domain.enums.role import MessageRole


def message_to_mongo(message: Message) -> dict[str, Any]:
    """Convert Message domain entity to MongoDB document dict.

    Args:
        message: The Message domain entity.

    Returns:
        A dictionary representation suitable for MongoDB.
    """
    tool_calls_dump = [tc.model_dump() for tc in message.tool_calls]

    role_val = (
        message.role.value if hasattr(message.role, "value") else str(message.role)
    )

    return {
        "_id": str(message.id),
        "session_id": str(message.session_id),
        "role": role_val,
        "content": message.content,
        "tool_calls": tool_calls_dump,
        "timestamp": message.timestamp,
        "tokens_used": message.tokens_used,
        "model": message.model,
    }


def mongo_to_message(doc: dict[str, Any]) -> Message:
    """Convert MongoDB document dict to Message domain entity.

    Args:
        doc: The MongoDB document dictionary.

    Returns:
        The reconstructed Message domain entity.
    """
    tool_calls = [ToolCallResult(**tc) for tc in doc.get("tool_calls", [])]
    return Message(
        id=UUID(doc["_id"]),
        session_id=UUID(doc["session_id"]),
        role=MessageRole(doc["role"]),
        content=doc["content"],
        tool_calls=tool_calls,
        timestamp=doc["timestamp"],
        tokens_used=doc.get("tokens_used"),
        model=doc.get("model"),
    )
