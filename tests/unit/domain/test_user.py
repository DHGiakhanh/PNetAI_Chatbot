"""Unit tests for the User domain entity."""

from __future__ import annotations

from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.domain.enums.user_permission import UserPermission


def test_user_guest() -> None:
    """Test guest User entity attributes and derived permissions."""
    user = User.guest()

    assert user.id is None
    assert user.is_authenticated is False
    assert user.permission == UserPermission.GUEST


def test_user_authenticated() -> None:
    """Test authenticated User entity attributes and derived permissions."""
    user_id = "user_999"
    user = User.authenticated(user_id=user_id)

    assert user.id == user_id
    assert user.is_authenticated is True
    assert user.permission == UserPermission.MEMBER
