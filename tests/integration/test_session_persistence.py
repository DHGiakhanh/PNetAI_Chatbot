"""Integration tests for session lifecycle and persistence in MongoDB."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from pnetai_chatbot.application.use_cases.session.summarize_session import (
    SummarizeSessionUseCase,
)
from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.session import ChatSession
from pnetai_chatbot.infrastructure.persistence.mongodb.history_repo import (
    HistoryRepository,
)
from pnetai_chatbot.infrastructure.persistence.mongodb.session_repo import (
    SessionRepository,
)


@pytest.mark.asyncio
async def test_session_lifecycle_persistence(test_db: AsyncIOMotorDatabase) -> None:
    """Test full persistent session database lifecycle.

    Create -> Insert Messages -> Check DB -> Summarize -> Cascade Delete.
    """
    user_id = "member_456"
    session_id = uuid4()

    # 1. Initialize repositories with test database
    session_repo = SessionRepository(db=test_db)
    history_repo = HistoryRepository(db=test_db)

    # 2. Create ChatSession entity and persist it
    session = ChatSession.create(
        user_id=user_id, metadata={"source": "integration_test"}
    )
    session.id = session_id  # set fixed ID for verification
    await session_repo.create(session)

    # Verify session document exists in MongoDB
    saved_session = await session_repo.get_by_id(session_id)
    assert saved_session is not None
    assert saved_session.id == session_id
    assert saved_session.user_id == user_id
    assert saved_session.message_count == 0
    assert saved_session.summary is None

    # 3. Create and insert Message entities
    msg1 = Message.create_user_message(
        message_id=uuid4(),
        session_id=session_id,
        content="Xin chào, tôi cần tư vấn về dinh dưỡng cho chó Poodle con.",
    )
    await history_repo.insert(msg1)

    # Verify message_count in ChatSession document is incremented to 1
    updated_session = await session_repo.get_by_id(session_id)
    assert updated_session.message_count == 1

    msg2 = Message.create_assistant_message(
        session_id=session_id,
        content="Chào bạn! Chó Poodle con cần chế độ ăn giàu protein và dễ tiêu hóa.",
        tokens_used=50,
        model="gpt-4o-mini",
    )
    await history_repo.insert(msg2)

    # Verify message_count in ChatSession document is incremented to 2
    updated_session = await session_repo.get_by_id(session_id)
    assert updated_session.message_count == 2

    # 4. Load history and verify ordering and completeness
    history = await history_repo.get_by_session(session_id)
    assert len(history) == 2
    assert history[0].content == msg1.content
    assert history[1].content == msg2.content
    assert history[0].role.value == "user"
    assert history[1].role.value == "assistant"

    # 5. Trigger Summarize Session Use Case
    mock_llm = MagicMock()
    mock_llm_response = MagicMock()
    mock_llm_response.text = "Tóm tắt: Tư vấn dinh dưỡng Poodle con."
    mock_llm.chat = AsyncMock(return_value=mock_llm_response)

    summarize_use_case = SummarizeSessionUseCase(
        session_repository=session_repo,
        history_repository=history_repo,
        llm=mock_llm,
    )

    summary = await summarize_use_case.execute(session_id)
    assert summary == "Tóm tắt: Tư vấn dinh dưỡng Poodle con."

    # Verify the summary is persisted to the ChatSession document
    summarized_session = await session_repo.get_by_id(session_id)
    assert summarized_session.summary == "Tóm tắt: Tư vấn dinh dưỡng Poodle con."

    # 6. Delete session and verify cascade delete of messages
    await session_repo.delete(session_id)

    # Verify session is deleted
    deleted_session = await session_repo.get_by_id(session_id)
    assert deleted_session is None

    # Verify history messages are also deleted
    deleted_history = await history_repo.get_by_session(session_id)
    assert len(deleted_history) == 0
