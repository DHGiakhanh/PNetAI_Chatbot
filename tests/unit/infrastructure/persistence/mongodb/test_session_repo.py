"""Unit tests for MongoDB SessionRepository implementation."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from pnetai_chatbot.domain.entities.session import ChatSession
from pnetai_chatbot.infrastructure.persistence.mongodb.session_repo import (
    SessionRepository,
)


@pytest.mark.asyncio
async def test_session_repo_create() -> None:
    """Test creating a chat session in the repository."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_coll.insert_one = AsyncMock()

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.session_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = SessionRepository()
        session = ChatSession.create(user_id="user_123")
        res = await repo.create(session)

        assert res.id == session.id
        assert res.user_id == "user_123"
        mock_coll.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_session_repo_get_by_id_found() -> None:
    """Test getting a chat session by ID when it exists."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    session_id = uuid4()
    now = datetime.utcnow()
    mock_coll.find_one = AsyncMock(
        return_value={
            "_id": str(session_id),
            "user_id": "user_123",
            "is_authenticated": True,
            "created_at": now,
            "updated_at": now,
            "message_count": 5,
            "summary": "This is a summary",
            "metadata": {"source": "test"},
        }
    )

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.session_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = SessionRepository()
        res = await repo.get_by_id(session_id)

        assert res is not None
        assert res.id == session_id
        assert res.user_id == "user_123"
        assert res.summary == "This is a summary"
        mock_coll.find_one.assert_called_once_with({"_id": str(session_id)})


@pytest.mark.asyncio
async def test_session_repo_get_by_id_not_found() -> None:
    """Test getting a chat session by ID when it does not exist."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_coll.find_one = AsyncMock(return_value=None)

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.session_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = SessionRepository()
        session_id = uuid4()
        res = await repo.get_by_id(session_id)

        assert res is None
        mock_coll.find_one.assert_called_once_with({"_id": str(session_id)})


@pytest.mark.asyncio
async def test_session_repo_update_summary() -> None:
    """Test updating a chat session's summary."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_coll.update_one = AsyncMock()

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.session_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = SessionRepository()
        session_id = uuid4()
        await repo.update_summary(session_id, "New Summary")

        mock_coll.update_one.assert_called_once()
        args, kwargs = mock_coll.update_one.call_args
        assert args[0] == {"_id": str(session_id)}
        assert args[1]["$set"]["summary"] == "New Summary"
        assert isinstance(args[1]["$set"]["updated_at"], datetime)


@pytest.mark.asyncio
async def test_session_repo_list_by_user() -> None:
    """Test listing all chat sessions belonging to a user."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    mock_cursor = MagicMock()
    mock_coll.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor

    session_id_1 = uuid4()
    session_id_2 = uuid4()
    now = datetime.utcnow()
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "_id": str(session_id_1),
                "user_id": "user_123",
                "is_authenticated": True,
                "created_at": now,
                "updated_at": now,
                "message_count": 0,
                "summary": None,
                "metadata": {},
            },
            {
                "_id": str(session_id_2),
                "user_id": "user_123",
                "is_authenticated": True,
                "created_at": now,
                "updated_at": now,
                "message_count": 1,
                "summary": "Summary",
                "metadata": {},
            },
        ]
    )

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.session_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = SessionRepository()
        res = await repo.list_by_user("user_123")

        assert len(res) == 2
        assert res[0].id == session_id_1
        assert res[1].id == session_id_2
        mock_coll.find.assert_called_once_with({"user_id": "user_123"})
        mock_cursor.sort.assert_called_once_with("updated_at", -1)
        mock_cursor.to_list.assert_called_once_with(length=100)


@pytest.mark.asyncio
async def test_session_repo_delete() -> None:
    """Test deleting a chat session (checking cascade call)."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_coll.delete_one = AsyncMock()

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.session_repo.get_chat_client",
        return_value=mock_client,
    ):
        mock_history_repo = MagicMock()
        mock_history_repo.delete_by_session = AsyncMock()

        with patch(
            "pnetai_chatbot.infrastructure.persistence.mongodb.history_repo.HistoryRepository",
            return_value=mock_history_repo,
        ):
            repo = SessionRepository()
            session_id = uuid4()
            await repo.delete(session_id)

            mock_coll.delete_one.assert_called_once_with({"_id": str(session_id)})
            mock_history_repo.delete_by_session.assert_called_once_with(session_id)
