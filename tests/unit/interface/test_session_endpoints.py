"""Unit tests for the persisted chat session REST API endpoints."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.session import ChatSession
from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.domain.enums.role import MessageRole
from pnetai_chatbot.interface.api.app import create_app
from pnetai_chatbot.interface.api.v1.dependencies import (
    get_current_user,
    get_get_history_use_case,
    get_session_repository,
)


@pytest.fixture
def mock_session_repo() -> AsyncMock:
    """Mock the persistent SessionRepository."""
    return AsyncMock()


@pytest.fixture
def mock_history_use_case() -> AsyncMock:
    """Mock the GetSessionHistoryUseCase."""
    return AsyncMock()


@pytest.fixture
def test_sessions() -> list[ChatSession]:
    """Provide a standard list of mock chat sessions."""
    sid1 = uuid4()
    sid2 = uuid4()
    return [
        ChatSession(
            id=sid1,
            user_id="user_123",
            is_authenticated=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            message_count=4,
            summary="Hỏi về Poodle P1",
            metadata={},
        ),
        ChatSession(
            id=sid2,
            user_id="user_123",
            is_authenticated=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            message_count=6,
            summary="Hỏi về Husky P2",
            metadata={},
        ),
    ]


@pytest.mark.asyncio
async def test_list_sessions_guest_blocked() -> None:
    """Test that guest unauthenticated users are blocked from listing sessions (401)."""
    app = create_app()
    # Override current user to return guest
    app.dependency_overrides[get_current_user] = lambda: User.guest()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/sessions")

    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_sessions_success(
    mock_session_repo: AsyncMock,
    test_sessions: list[ChatSession],
) -> None:
    """Test successful retrieval of session lists for authenticated members."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.authenticated("user_123")
    app.dependency_overrides[get_session_repository] = lambda: mock_session_repo

    mock_session_repo.list_by_user.return_value = test_sessions

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/sessions")

    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) == 2
    assert data["sessions"][0]["summary"] == "Hỏi về Poodle P1"
    assert (
        data["sessions"][1]["summary"] == "Husky" in data["sessions"][1]["summary"]
        or "Husky P2" in data["sessions"][1]["summary"]
    )
    mock_session_repo.list_by_user.assert_called_once_with("user_123")


@pytest.mark.asyncio
async def test_get_session_history_not_found(
    mock_session_repo: AsyncMock,
) -> None:
    """Test that fetching history for a non-existent session yields 404."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.authenticated("user_123")
    app.dependency_overrides[get_session_repository] = lambda: mock_session_repo

    mock_session_repo.get_by_id.return_value = None
    target_uuid = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(f"/api/v1/sessions/{target_uuid}/history")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_session_history_ownership_denied(
    mock_session_repo: AsyncMock,
    test_sessions: list[ChatSession],
) -> None:
    """Test that users are strictly prevented from loading others' threads (403)."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.authenticated("user_999")
    app.dependency_overrides[get_session_repository] = lambda: mock_session_repo

    # Session belongs to "user_123"
    target_session = test_sessions[0]
    mock_session_repo.get_by_id.return_value = target_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(f"/api/v1/sessions/{target_session.id}/history")

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_session_history_success(
    mock_session_repo: AsyncMock,
    mock_history_use_case: AsyncMock,
    test_sessions: list[ChatSession],
) -> None:
    """Test successfully loading session history for authenticated owners."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.authenticated("user_123")
    app.dependency_overrides[get_session_repository] = lambda: mock_session_repo
    app.dependency_overrides[get_get_history_use_case] = lambda: mock_history_use_case

    target_session = test_sessions[0]
    mock_session_repo.get_by_id.return_value = target_session

    # Setup history messages
    msg1 = Message(
        id=uuid4(),
        session_id=target_session.id,
        role=MessageRole.USER,
        content="Hello PnetAI",
        tool_calls=[],
        timestamp=datetime.utcnow(),
    )
    msg2 = Message(
        id=uuid4(),
        session_id=target_session.id,
        role=MessageRole.ASSISTANT,
        content="Chào bạn, tôi là PetBot",
        tool_calls=[],
        timestamp=datetime.utcnow(),
    )

    mock_history_use_case.execute.return_value = [msg1, msg2]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(f"/api/v1/sessions/{target_session.id}/history")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == str(target_session.id)
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Hello PnetAI"
    assert data["messages"][1]["role"] == "assistant"
    assert data["summary"] == "Hỏi về Poodle P1"


@pytest.mark.asyncio
async def test_delete_session_success(
    mock_session_repo: AsyncMock,
    test_sessions: list[ChatSession],
) -> None:
    """Test successfully cascade deleting a session and all related history logs."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User.authenticated("user_123")
    app.dependency_overrides[get_session_repository] = lambda: mock_session_repo

    target_session = test_sessions[0]
    mock_session_repo.get_by_id.return_value = target_session
    mock_session_repo.delete.return_value = None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.delete(f"/api/v1/sessions/{target_session.id}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_session_repo.delete.assert_called_once_with(target_session.id)
