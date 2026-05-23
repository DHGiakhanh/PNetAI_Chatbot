"""Unit tests for ChatOrchestratorUseCase in the Application Layer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from pnetai_chatbot.application.ports.history_repo_port import IHistoryRepository
from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository
from pnetai_chatbot.application.use_cases.chat.chat_orchestrator_use_case import (
    ChatOrchestratorUseCase,
)
from pnetai_chatbot.application.use_cases.session.summarize_session import (
    SummarizeSessionUseCase,
)
from pnetai_chatbot.domain.entities.session import ChatSession


@pytest.mark.asyncio
async def test_chat_orchestrator_auth_success() -> None:
    """Test ChatOrchestratorUseCase success flow for an authenticated member."""
    session_id = uuid4()
    user_id = "user_123"
    query = "Hỏi về thức ăn cho mèo Poodle?"

    # Mock Repositories
    mock_session = ChatSession.create(user_id=user_id)
    mock_session.id = session_id
    mock_session.message_count = 5  # Initial message count

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=mock_session)

    mock_history_repo = MagicMock(spec=IHistoryRepository)
    mock_history_repo.get_by_session = AsyncMock(return_value=[])
    mock_history_repo.insert = AsyncMock()

    # Mock LangGraph instance
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "final_response": "Nên dùng thức ăn hữu cơ cho mèo.",
            "tool_results": {
                "vector_search": {
                    "input_summary": "mèo Poodle",
                    "output_summary": "kết quả search",
                    "execution_time_ms": 100,
                    "data": {},
                    "success": True,
                }
            },
        }
    )

    mock_summarize = MagicMock(spec=SummarizeSessionUseCase)

    # Instantiate use case
    use_case = ChatOrchestratorUseCase(
        compiled_graph=mock_graph,
        session_repository=mock_session_repo,
        history_repository=mock_history_repo,
        summarize_use_case=mock_summarize,
    )

    # Execute
    res = await use_case.execute(
        session_id=session_id,
        query=query,
        user_id=user_id,
        is_authenticated=True,
    )

    # Verify return message
    assert res.session_id == session_id
    assert res.content == "Nên dùng thức ăn hữu cơ cho mèo."
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].tool_name == "vector_search"

    # Verify history persists both user and assistant messages
    assert mock_history_repo.insert.call_count == 2
    # Verify graph input state
    mock_graph.ainvoke.assert_called_once()
    initial_state_passed = mock_graph.ainvoke.call_args[0][0]
    assert initial_state_passed["query"] == query
    assert initial_state_passed["user_id"] == user_id
    assert initial_state_passed["is_authenticated"] is True

    # Summarization should not be triggered since count is not % 10 == 0
    mock_summarize.execute.assert_not_called()


@pytest.mark.asyncio
async def test_chat_orchestrator_guest_ephemeral() -> None:
    """Test ChatOrchestratorUseCase for a guest user (never persists history)."""
    session_id = uuid4()
    query = "Hello guest!"

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=None)

    mock_history_repo = MagicMock(spec=IHistoryRepository)
    mock_history_repo.get_by_session = AsyncMock(return_value=[])
    mock_history_repo.insert = AsyncMock()

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "final_response": "Phản hồi cho khách vãng lai.",
            "tool_results": {},
        }
    )

    use_case = ChatOrchestratorUseCase(
        compiled_graph=mock_graph,
        session_repository=mock_session_repo,
        history_repository=mock_history_repo,
    )

    res = await use_case.execute(
        session_id=session_id,
        query=query,
        user_id=None,
        is_authenticated=False,
    )

    assert res.content == "Phản hồi cho khách vãng lai."
    # Ephemeral guest sessions check DB but NEVER insert/write history
    mock_session_repo.get_by_id.assert_called_once_with(session_id)
    mock_history_repo.get_by_session.assert_called_once_with(session_id, limit=20)
    mock_history_repo.insert.assert_not_called()


@pytest.mark.asyncio
async def test_chat_orchestrator_trigger_summarization() -> None:
    """Test background summarization auto-triggers at message_count multiple of 10."""
    session_id = uuid4()
    user_id = "user_123"

    mock_session = ChatSession.create(user_id=user_id)
    mock_session.id = session_id
    # message_count = 10 (a multiple of 10)
    mock_session.message_count = 10

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session_repo.get_by_id = AsyncMock(return_value=mock_session)

    mock_history_repo = MagicMock(spec=IHistoryRepository)
    mock_history_repo.get_by_session = AsyncMock(return_value=[])
    mock_history_repo.insert = AsyncMock()

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "final_response": "OK",
            "tool_results": {},
        }
    )

    mock_summarize = MagicMock(spec=SummarizeSessionUseCase)
    mock_summarize.execute = AsyncMock()

    use_case = ChatOrchestratorUseCase(
        compiled_graph=mock_graph,
        session_repository=mock_session_repo,
        history_repository=mock_history_repo,
        summarize_use_case=mock_summarize,
    )

    await use_case.execute(
        session_id=session_id,
        query="hi",
        user_id=user_id,
        is_authenticated=True,
    )

    # Verify background summarize task was spawned
    mock_summarize.execute.assert_called_once_with(session_id)


@pytest.mark.asyncio
async def test_chat_orchestrator_graph_failure() -> None:
    """Test ChatOrchestratorUseCase gracefully handles LangGraph invocation crash."""
    session_id = uuid4()

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=Exception("LangGraph exploded!"))

    use_case = ChatOrchestratorUseCase(compiled_graph=mock_graph)

    res = await use_case.execute(
        session_id=session_id,
        query="crash test",
        user_id=None,
        is_authenticated=False,
    )

    assert "đã có lỗi hệ thống xảy ra" in res.content
