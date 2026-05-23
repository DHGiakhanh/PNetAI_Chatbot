"""ChatSession entity."""

from datetime import datetime
from typing import Any

from pydantic import UUID4, BaseModel, Field


class ChatSession(BaseModel):
    """Represents a chat session between a user and the chatbot."""

    id: UUID4 = Field(..., description="Unique session identifier")
    user_id: str | None = Field(
        default=None,
        description="Authenticated user ID (None for guests)",
    )
    is_authenticated: bool = Field(
        default=False,
        description="Whether the session belongs to an authenticated user",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp",
    )
    message_count: int = Field(
        default=0,
        description="Number of messages in this session",
    )
    summary: str | None = Field(
        default=None,
        description="Auto-generated session summary",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (source_page, device, etc.)",
    )

    @classmethod
    def create(
        cls,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ChatSession":
        """Factory method to create a new session."""
        from uuid import uuid4

        return cls(
            id=uuid4(),
            user_id=user_id,
            is_authenticated=user_id is not None,
            metadata=metadata or {},
        )

    @classmethod
    def create_ephemeral(cls) -> "ChatSession":
        """Create a temporary session for guest users (not persisted)."""
        return cls.create(user_id=None)
