"""Unit tests for MongoDB HistoryRepository implementation."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.infrastructure.persistence.mongodb.history_repo import (
    HistoryRepository,
)


@pytest.mark.asyncio
async def test_history_repo_insert() -> None:
    """Test inserting a message into the history repository."""
    mock_db = MagicMock()
    mock_messages_coll = MagicMock()
    mock_sessions_coll = MagicMock()

    # Distinguish which collection is accessed
    def get_coll(name: str) -> MagicMock:
        if name == "chat_messages":
            return mock_messages_coll
        elif name == "chat_sessions":
            return mock_sessions_coll
        return MagicMock()

    mock_db.__getitem__.side_effect = get_coll

    mock_messages_coll.insert_one = AsyncMock()
    mock_sessions_coll.update_one = AsyncMock()

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.history_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = HistoryRepository()
        session_id = uuid4()
        message = Message.create_user_message(
            message_id=uuid4(),
            session_id=session_id,
            content="Hello chatbot",
        )

        res = await repo.insert(message)

        assert res.id == message.id
        assert res.content == "Hello chatbot"
        mock_messages_coll.insert_one.assert_called_once()
        mock_sessions_coll.update_one.assert_called_once()
        update_args = mock_sessions_coll.update_one.call_args[0]
        assert update_args[0] == {"_id": str(session_id)}
        assert update_args[1]["$inc"] == {"message_count": 1}


@pytest.mark.asyncio
async def test_history_repo_get_by_session() -> None:
    """Test retrieving messages for a session (chronologically ascending)."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    mock_cursor = MagicMock()
    mock_coll.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor

    session_id = uuid4()
    msg_id_1 = uuid4()
    msg_id_2 = uuid4()
    ts1 = datetime(2026, 5, 22, 10, 0, 0)
    ts2 = datetime(2026, 5, 22, 10, 1, 0)

    # Motor cursor returns descending list in get_by_session,
    # then repository reverses them
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "_id": str(msg_id_2),
                "session_id": str(session_id),
                "role": "assistant",
                "content": "Hi there",
                "timestamp": ts2,
                "tool_calls": [],
            },
            {
                "_id": str(msg_id_1),
                "session_id": str(session_id),
                "role": "user",
                "content": "Hello",
                "timestamp": ts1,
                "tool_calls": [],
            },
        ]
    )

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.history_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = HistoryRepository()
        res = await repo.get_by_session(session_id=session_id, limit=10)

        # After reversal: user first, assistant second
        assert len(res) == 2
        assert res[0].id == msg_id_1
        assert res[1].id == msg_id_2
        assert res[0].content == "Hello"
        assert res[1].content == "Hi there"

        mock_coll.find.assert_called_once_with({"session_id": str(session_id)})
        mock_cursor.sort.assert_called_once_with("timestamp", -1)
        mock_cursor.to_list.assert_called_once_with(length=10)


@pytest.mark.asyncio
async def test_history_repo_get_by_session_with_cursor() -> None:
    """Test retrieving messages with before_timestamp cursor."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    mock_cursor = MagicMock()
    mock_coll.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[])

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.history_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = HistoryRepository()
        session_id = uuid4()
        before_ts = "2026-05-22T12:00:00Z"
        await repo.get_by_session(
            session_id=session_id,
            limit=5,
            before_timestamp=before_ts,
        )

        mock_coll.find.assert_called_once()
        find_query = mock_coll.find.call_args[0][0]
        assert find_query["session_id"] == str(session_id)
        assert "$lt" in find_query["timestamp"]
        assert isinstance(find_query["timestamp"]["$lt"], datetime)


@pytest.mark.asyncio
async def test_history_repo_delete_by_session() -> None:
    """Test deleting all messages associated with a session."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    mock_res = MagicMock()
    mock_res.deleted_count = 15
    mock_coll.delete_many = AsyncMock(return_value=mock_res)

    mock_client = MagicMock()
    mock_client.db = mock_db

    with patch(
        "pnetai_chatbot.infrastructure.persistence.mongodb.history_repo.get_chat_client",
        return_value=mock_client,
    ):
        repo = HistoryRepository()
        session_id = uuid4()
        res = await repo.delete_by_session(session_id)

        assert res == 15
        mock_coll.delete_many.assert_called_once_with({"session_id": str(session_id)})
