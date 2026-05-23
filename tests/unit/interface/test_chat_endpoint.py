"""Unit tests for the chat API endpoints supporting JSON and SSE streaming."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.session import ChatSession
from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.interface.api.app import create_app
from pnetai_chatbot.interface.api.v1.dependencies import (
    get_agent_orchestrator,
    get_chat_orchestrator,
    get_current_user,
    get_history_repository,
    get_resolve_context_use_case,
    get_session_repository,
    get_summarize_session_use_case,
)


class MockAgentGraph:
    """Mock LangGraph StateGraph compiled object."""

    def __init__(self, chunks: list[dict]) -> None:
        """Initialize with predefined stream chunks.

        Args:
            chunks: List of predefined dictionary chunks to stream.
        """
        self.chunks = chunks

    async def astream(self, initial_state: dict) -> AsyncIterator[dict]:
        """Stream mock graph execution steps.

        Args:
            initial_state: The initial state dictionary.

        Yields:
            Predefined dictionary chunks.
        """
        for chunk in self.chunks:
            yield chunk


@pytest.fixture
def mock_chat_orchestrator() -> AsyncMock:
    """Provide a mock ChatOrchestratorUseCase."""
    return AsyncMock()


@pytest.fixture
def mock_resolve_context() -> AsyncMock:
    """Provide a mock ResolveUserContextUseCase."""
    return AsyncMock()


@pytest.fixture
def mock_summarize_use_case() -> AsyncMock:
    """Provide a mock SummarizeSessionUseCase."""
    return AsyncMock()


@pytest.fixture
def mock_history_repo() -> AsyncMock:
    """Provide a mock HistoryRepository."""
    return AsyncMock()


@pytest.fixture
def mock_session_repo() -> AsyncMock:
    """Provide a mock SessionRepository."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_chat_non_stream_guest(
    mock_chat_orchestrator: AsyncMock,
    mock_resolve_context: AsyncMock,
) -> None:
    """Test non-streamed chat for guests yielding ephemeral session context."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.guest()
    app.dependency_overrides[get_chat_orchestrator] = lambda: mock_chat_orchestrator
    app.dependency_overrides[get_resolve_context_use_case] = lambda: (
        mock_resolve_context
    )

    session = ChatSession.create_ephemeral()
    mock_resolve_context.execute.return_value = (session, [])

    assistant_msg = Message.create_assistant_message(
        session_id=session.id,
        content="Đây là phản hồi cho khách.",
        tokens_used=150,
        model="gpt-4o-mini",
    )
    mock_chat_orchestrator.execute.return_value = assistant_msg

    payload = {
        "query": "Hỏi đáp nhanh không lưu lịch sử",
        "stream": False,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Đây là phản hồi cho khách."
    assert data["session_id"] == str(session.id)
    assert data["tokens_used"] == 150
    assert data["model"] == "gpt-4o-mini"
    mock_resolve_context.execute.assert_called_once_with(
        session_id=None,
        user_id=None,
    )


@pytest.mark.asyncio
async def test_chat_non_stream_auth_member(
    mock_chat_orchestrator: AsyncMock,
    mock_resolve_context: AsyncMock,
) -> None:
    """Test non-streamed chat for members utilizing persistent session logs."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.authenticated("user_123")
    app.dependency_overrides[get_chat_orchestrator] = lambda: mock_chat_orchestrator
    app.dependency_overrides[get_resolve_context_use_case] = lambda: (
        mock_resolve_context
    )

    session = ChatSession.create(user_id="user_123")
    history_msg = Message.create_user_message(
        message_id=uuid4(),
        session_id=session.id,
        content="Chào buổi sáng",
    )
    mock_resolve_context.execute.return_value = (session, [history_msg])

    assistant_msg = Message.create_assistant_message(
        session_id=session.id,
        content="Chào bạn, tôi có thể giúp gì cho bạn?",
        tokens_used=220,
        model="gpt-4o-mini",
    )
    mock_chat_orchestrator.execute.return_value = assistant_msg

    payload = {
        "query": "Hỏi về sản phẩm",
        "session_id": str(session.id),
        "stream": False,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Chào bạn, tôi có thể giúp gì cho bạn?"
    assert data["session_id"] == str(session.id)
    mock_resolve_context.execute.assert_called_once_with(
        session_id=session.id,
        user_id="user_123",
    )


@pytest.mark.asyncio
async def test_chat_ownership_denied(
    mock_resolve_context: AsyncMock,
) -> None:
    """Test ownership mismatch throws a clean 403 error to protect access."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.authenticated("user_999")
    app.dependency_overrides[get_resolve_context_use_case] = lambda: (
        mock_resolve_context
    )

    mock_resolve_context.execute.side_effect = ValueError(
        "Access denied: You do not own this chat session."
    )

    payload = {
        "query": "Xâm phạm session",
        "session_id": str(uuid4()),
        "stream": False,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/chat", json=payload)

    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_chat_sse_stream_guest(
    mock_resolve_context: AsyncMock,
) -> None:
    """Test that guests receive a full SSE streaming reasoning progression."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.guest()
    app.dependency_overrides[get_resolve_context_use_case] = lambda: (
        mock_resolve_context
    )

    session = ChatSession.create_ephemeral()
    mock_resolve_context.execute.return_value = (session, [])

    # Predefined nodes execution updates
    chunks = [
        {"intent_analyzer": {"tools_to_execute": [{"tool": "tavily_search"}]}},
        {
            "tool_executor": {
                "tool_results": {
                    "tavily_search": {
                        "output_summary": "Tìm thấy 3 bài viết về Poodle",
                        "success": True,
                    }
                }
            }
        },
        {"response_generator": {"final_response": "Đây là kết quả tìm được."}},
    ]
    mock_graph = MockAgentGraph(chunks)
    app.dependency_overrides[get_agent_orchestrator] = lambda: mock_graph

    payload = {
        "query": "Tìm bài viết Poodle",
        "stream": True,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Decode SSE stream lines
    lines = [line for line in response.iter_lines() if line.startswith("data:")]
    events = [json.loads(line[5:].strip()) for line in lines]

    assert len(events) >= 5
    assert events[0]["type"] == "thinking"
    assert events[1]["type"] == "tool_call"
    assert events[1]["tool"] == "tavily_search"
    assert events[2]["type"] == "tool_result"
    assert events[2]["tool"] == "tavily_search"
    assert events[2]["summary"] == "Tìm thấy 3 bài viết về Poodle"
    assert events[3]["type"] == "answer"
    assert events[3]["content"] == "Đây là kết quả tìm được."
    assert events[4]["type"] == "done"
    assert events[4]["session_id"] == str(session.id)


@pytest.mark.asyncio
async def test_chat_sse_stream_auth_member_with_summarization(
    mock_resolve_context: AsyncMock,
    mock_history_repo: AsyncMock,
    mock_session_repo: MagicMock,
    mock_summarize_use_case: AsyncMock,
) -> None:
    """Test SSE chat for authenticated members triggering history writes and summary."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.authenticated("user_123")
    app.dependency_overrides[get_resolve_context_use_case] = lambda: (
        mock_resolve_context
    )
    app.dependency_overrides[get_history_repository] = lambda: mock_history_repo
    app.dependency_overrides[get_session_repository] = lambda: mock_session_repo
    app.dependency_overrides[get_summarize_session_use_case] = lambda: (
        mock_summarize_use_case
    )

    session = ChatSession.create(user_id="user_123")
    session.message_count = 9
    updated_session = ChatSession.create(user_id="user_123")
    updated_session.id = session.id
    updated_session.message_count = 10
    mock_session_repo.get_by_id = AsyncMock(return_value=updated_session)

    mock_resolve_context.execute.return_value = (session, [])

    # Predefined nodes execution updates
    chunks = [
        {"response_generator": {"final_response": "Xin chào thành viên."}},
    ]
    mock_graph = MockAgentGraph(chunks)
    app.dependency_overrides[get_agent_orchestrator] = lambda: mock_graph

    payload = {
        "query": "Hỏi và tóm tắt",
        "session_id": str(session.id),
        "stream": True,
    }

    # Mock history_repo.insert to execute without error
    mock_history_repo.insert = AsyncMock(return_value=None)
    mock_summarize_use_case.execute = AsyncMock(return_value="Tóm tắt cuộc trò chuyện")

    # Use a small sleep check to allow asyncio background tasks to run in the
    # test event loop.
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/chat", json=payload)

    assert response.status_code == 200

    # Read the full stream to let generator run
    lines = [line for line in response.iter_lines() if line.startswith("data:")]
    events = [json.loads(line[5:].strip()) for line in lines]

    assert len(events) == 3
    assert events[0]["type"] == "thinking"
    assert events[1]["type"] == "answer"
    assert events[2]["type"] == "done"

    # Verify history_repo.insert was called for user query message AND assistant
    # response message.
    assert mock_history_repo.insert.call_count == 2

    # Give the background thread a moment to execute
    await asyncio.sleep(0.1)
    # Verify auto-summarization was triggered in the background
    mock_summarize_use_case.execute.assert_called_once_with(session.id)
