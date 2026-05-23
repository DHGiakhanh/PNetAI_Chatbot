"""Unit tests for session and history-related use cases."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from pnetai_chatbot.application.ports.history_repo_port import IHistoryRepository
from pnetai_chatbot.application.ports.llm_port import ILLMAdapter, LLMResponse
from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository
from pnetai_chatbot.application.services.permission_service import (
    PermissionService,
)
from pnetai_chatbot.application.use_cases.chat.create_session import (
    CreateSessionUseCase,
)
from pnetai_chatbot.application.use_cases.chat.get_session_history import (
    GetSessionHistoryUseCase,
)
from pnetai_chatbot.application.use_cases.session.resolve_user_context import (
    ResolveUserContextUseCase,
)
from pnetai_chatbot.application.use_cases.session.summarize_session import (
    SummarizeSessionUseCase,
)
from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.session import ChatSession


# ==========================================
# 1. CreateSessionUseCase Tests
# ==========================================
@pytest.mark.asyncio
async def test_create_session_guest() -> None:
    """Test creating an ephemeral session for a guest."""
    mock_session_repo = MagicMock(spec=ISessionRepository)
    use_case = CreateSessionUseCase(mock_session_repo)

    session = await use_case.execute(user_id=None)

    assert session.is_authenticated is False
    assert session.user_id is None
    mock_session_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_session_auth() -> None:
    """Test creating and persisting a session for an authenticated user."""
    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.create = AsyncMock(side_effect=lambda x: x)
    use_case = CreateSessionUseCase(mock_session_repo)

    session = await use_case.execute(user_id="user_123")

    assert session.is_authenticated is True
    assert session.user_id == "user_123"
    mock_session_repo.create.assert_called_once()


# ==========================================
# 2. GetSessionHistoryUseCase Tests
# ==========================================
@pytest.mark.asyncio
async def test_get_session_history_guest_denied() -> None:
    """Test that a guest cannot access session history."""
    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    use_case = GetSessionHistoryUseCase(mock_session_repo, mock_history_repo)

    with pytest.raises(
        ValueError, match="Guest users cannot load persisted session history"
    ):
        await use_case.execute(session_id=uuid4(), user_id=None)


@pytest.mark.asyncio
async def test_get_session_history_not_found() -> None:
    """Test loading history for non-existent session raises error."""
    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=None)
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    use_case = GetSessionHistoryUseCase(mock_session_repo, mock_history_repo)

    with pytest.raises(ValueError, match="Session not found"):
        await use_case.execute(session_id=uuid4(), user_id="user_123")


@pytest.mark.asyncio
async def test_get_session_history_ownership_violation() -> None:
    """Test that retrieving session belonging to another user raises error."""
    session_id = uuid4()
    mock_session = ChatSession.create(user_id="user_abc")
    mock_session.id = session_id

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=mock_session)
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    use_case = GetSessionHistoryUseCase(mock_session_repo, mock_history_repo)

    with pytest.raises(ValueError, match="Access denied: You do not own"):
        await use_case.execute(session_id=session_id, user_id="user_xyz")


@pytest.mark.asyncio
async def test_get_session_history_success() -> None:
    """Test successfully retrieving history for owned session."""
    session_id = uuid4()
    mock_session = ChatSession.create(user_id="user_123")
    mock_session.id = session_id

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=mock_session)

    mock_messages = [
        Message.create_user_message(uuid4(), session_id, "hello"),
        Message.create_assistant_message(session_id, "hi"),
    ]
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    mock_history_repo.get_by_session = AsyncMock(return_value=mock_messages)

    use_case = GetSessionHistoryUseCase(mock_session_repo, mock_history_repo)
    res = await use_case.execute(session_id=session_id, user_id="user_123")

    assert len(res) == 2
    assert res[0].content == "hello"
    assert res[1].content == "hi"
    mock_history_repo.get_by_session.assert_called_once_with(
        session_id=session_id, limit=50, before_timestamp=None
    )


# ==========================================
# 3. ResolveUserContextUseCase Tests
# ==========================================
@pytest.mark.asyncio
async def test_resolve_user_context_guest() -> None:
    """Test guest context resolution returns ephemeral session and no history."""
    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    perm_service = PermissionService()

    use_case = ResolveUserContextUseCase(
        mock_session_repo, mock_history_repo, perm_service
    )
    session, history = await use_case.execute(session_id=None, user_id=None)

    assert session.is_authenticated is False
    assert session.user_id is None
    assert history == []
    mock_session_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_user_context_auth_no_session() -> None:
    """Test auth context resolution without session ID creates new session."""
    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.create = AsyncMock(side_effect=lambda x: x)
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    perm_service = PermissionService()

    use_case = ResolveUserContextUseCase(
        mock_session_repo, mock_history_repo, perm_service
    )
    session, history = await use_case.execute(session_id=None, user_id="user_123")

    assert session.is_authenticated is True
    assert session.user_id == "user_123"
    assert history == []
    mock_session_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_user_context_auth_session_not_found() -> None:
    """Test auth context resolution with session ID (not in DB) creates it."""
    session_id = uuid4()
    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=None)
    mock_session_repo.create = AsyncMock(side_effect=lambda x: x)
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    perm_service = PermissionService()

    use_case = ResolveUserContextUseCase(
        mock_session_repo, mock_history_repo, perm_service
    )
    session, history = await use_case.execute(session_id=session_id, user_id="user_123")

    assert session.is_authenticated is True
    assert session.id == session_id
    assert session.user_id == "user_123"
    assert history == []
    mock_session_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_user_context_auth_success() -> None:
    """Test auth context resolution retrieves existing session and history."""
    session_id = uuid4()
    mock_session = ChatSession.create(user_id="user_123")
    mock_session.id = session_id

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=mock_session)

    mock_messages = [Message.create_user_message(uuid4(), session_id, "hello")]
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    mock_history_repo.get_by_session = AsyncMock(return_value=mock_messages)
    perm_service = PermissionService()

    use_case = ResolveUserContextUseCase(
        mock_session_repo, mock_history_repo, perm_service
    )
    session, history = await use_case.execute(session_id=session_id, user_id="user_123")

    assert session.id == session_id
    assert len(history) == 1
    assert history[0].content == "hello"


@pytest.mark.asyncio
async def test_resolve_user_context_auth_ownership_violation() -> None:
    """Test auth context resolution raises error on ownership mismatch."""
    session_id = uuid4()
    mock_session = ChatSession.create(user_id="user_abc")
    mock_session.id = session_id

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=mock_session)
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    perm_service = PermissionService()

    use_case = ResolveUserContextUseCase(
        mock_session_repo, mock_history_repo, perm_service
    )

    with pytest.raises(ValueError, match="Access denied: You do not own"):
        await use_case.execute(session_id=session_id, user_id="user_xyz")


# ==========================================
# 4. SummarizeSessionUseCase Tests
# ==========================================
@pytest.mark.asyncio
async def test_summarize_session_empty_history() -> None:
    """Test that summarization skips when history is empty."""
    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    mock_history_repo.get_by_session = AsyncMock(return_value=[])
    mock_llm = MagicMock(spec=ILLMAdapter)

    use_case = SummarizeSessionUseCase(mock_session_repo, mock_history_repo, mock_llm)
    summary = await use_case.execute(uuid4())

    assert summary == ""
    mock_llm.chat.assert_not_called()
    mock_session_repo.update_summary.assert_not_called()


@pytest.mark.asyncio
async def test_summarize_session_success() -> None:
    """Test successful summarization flow."""
    session_id = uuid4()
    mock_session = ChatSession.create(user_id="user_123")
    mock_session.summary = "Old summary"

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=mock_session)
    mock_session_repo.update_summary = AsyncMock()

    mock_messages = [
        Message.create_user_message(uuid4(), session_id, "hello my cat is sick"),
        Message.create_assistant_message(session_id, "sorry to hear that"),
    ]
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    mock_history_repo.get_by_session = AsyncMock(return_value=mock_messages)

    mock_llm = MagicMock(spec=ILLMAdapter)
    mock_response = LLMResponse(
        text="New veterinary chatbot summary context.", model="mock-model"
    )
    mock_llm.chat = AsyncMock(return_value=mock_response)

    use_case = SummarizeSessionUseCase(mock_session_repo, mock_history_repo, mock_llm)
    summary = await use_case.execute(session_id)

    assert summary == "New veterinary chatbot summary context."
    mock_history_repo.get_by_session.assert_called_once_with(
        session_id=session_id, limit=20
    )
    mock_llm.chat.assert_called_once()
    chat_args = mock_llm.chat.call_args[1]
    assert chat_args["temperature"] == 0.3
    mock_session_repo.update_summary.assert_called_once_with(
        session_id, "New veterinary chatbot summary context."
    )
