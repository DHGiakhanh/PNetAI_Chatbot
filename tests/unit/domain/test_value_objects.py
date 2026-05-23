"""Unit tests for value objects and enums in the Domain Layer."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.domain.value_objects.query import UserQuery
from pnetai_chatbot.domain.value_objects.session_id import SessionId


def test_session_id_ephemeral() -> None:
    """Test ephemeral SessionId initialization."""
    sess_id = SessionId.ephemeral()
    assert sess_id.is_ephemeral is True
    assert sess_id.value.int == 0
    assert str(sess_id) == "00000000-0000-0000-0000-000000000000"


def test_session_id_from_str_and_uuid() -> None:
    """Test SessionId initialization from strings and raw UUIDs."""
    raw_uuid = uuid4()

    # Str init
    sess_id_str = SessionId(str(raw_uuid))
    assert sess_id_str.is_ephemeral is False
    assert sess_id_str.value == raw_uuid

    # UUID init
    sess_id_uuid = SessionId(raw_uuid)
    assert sess_id_uuid.is_ephemeral is False
    assert sess_id_uuid == sess_id_str


def test_session_id_equality_and_hash() -> None:
    """Test SessionId equality, representation, and hashing mechanics."""
    raw_uuid = uuid4()
    s1 = SessionId(raw_uuid)
    s2 = SessionId(raw_uuid)

    assert s1 == s2
    assert hash(s1) == hash(s2)
    assert repr(s1) == f"SessionId({raw_uuid!r})"


def test_user_query() -> None:
    """Test UserQuery initialization and field structure."""
    sess_id = SessionId(uuid4())
    user = User.authenticated("user_123")
    text = "Query text content"

    q = UserQuery(
        raw_text=text,
        session_id=sess_id,
        user=user,
    )

    assert q.raw_text == text
    assert q.session_id == sess_id
    assert q.user == user
    assert isinstance(q.timestamp, datetime)
