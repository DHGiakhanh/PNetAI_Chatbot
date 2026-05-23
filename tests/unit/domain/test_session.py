"""Unit tests for the ChatSession domain entity."""

from __future__ import annotations

from datetime import datetime

from pnetai_chatbot.domain.entities.session import ChatSession


def test_create_session() -> None:
    """Test ChatSession creation via standard factory method."""
    user_id = "user_123"
    metadata = {"source": "pnetai_web"}

    session = ChatSession.create(user_id=user_id, metadata=metadata)

    assert session.id is not None
    assert session.user_id == user_id
    assert session.is_authenticated is True
    assert session.metadata == metadata
    assert session.message_count == 0
    assert session.summary is None
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)


def test_create_ephemeral_session() -> None:
    """Test creating an ephemeral (guest) session."""
    session = ChatSession.create_ephemeral()

    assert session.id is not None
    assert session.user_id is None
    assert session.is_authenticated is False
    assert len(session.metadata) == 0
    assert session.message_count == 0
    assert session.summary is None
