"""Integration tests for the full chat API flow supporting JSON and SSE streaming."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from pnetai_chatbot.domain.entities.session import ChatSession
from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.infrastructure.persistence.mongodb.history_repo import (
    HistoryRepository,
)
from pnetai_chatbot.infrastructure.persistence.mongodb.session_repo import (
    SessionRepository,
)
from pnetai_chatbot.interface.api.app import create_app
from pnetai_chatbot.interface.api.v1.dependencies import (
    get_agent_orchestrator,
    get_current_user,
    get_history_repository,
    get_session_repository,
)


class IntegrationMockAgentGraph:
    """Mock LangGraph StateGraph compiled object for integration testing."""

    def __init__(self, chunks: list[dict]) -> None:
        """Initialize with predefined stream chunks.

        Args:
            chunks: List of predefined dictionary chunks to stream.
        """
        self.chunks = chunks

    async def ainvoke(self, initial_state: dict) -> dict:
        """Invoke mock graph execution.

        Args:
            initial_state: The initial state dictionary.

        Returns:
            The final state dict.
        """
        # Return simulated final state with response and tool call results
        return {
            "final_response": "Đây là kết quả tư vấn tích hợp thực tế.",
            "tool_results": {
                "vector_search": {
                    "input_summary": "Poodle con",
                    "output_summary": "Kết quả cẩm nang chăm sóc Poodle con",
                    "execution_time_ms": 25,
                    "data": {},
                    "success": True,
                }
            },
        }

    async def astream(self, initial_state: dict) -> AsyncIterator[dict]:
        """Stream mock graph execution steps.

        Args:
            initial_state: The initial state dictionary.

        Yields:
            Predefined dictionary chunks.
        """
        for chunk in self.chunks:
            yield chunk


@pytest.mark.asyncio
async def test_full_chat_flow_json_integration(test_db: AsyncIOMotorDatabase) -> None:
    """Verify full chat flow under JSON non-streaming mode with database logging."""
    app = create_app()

    # 1. Setup real repository instances tied to our test database
    session_repo = SessionRepository(db=test_db)
    history_repo = HistoryRepository(db=test_db)

    # 2. Pre-create a persistent session in the test DB
    user_id = "integration_member"
    session = ChatSession.create(user_id=user_id, metadata={"env": "integration"})
    await session_repo.create(session)

    # 3. Mount dependency overrides
    app.dependency_overrides[get_current_user] = lambda: User.authenticated(user_id)
    app.dependency_overrides[get_session_repository] = lambda: session_repo
    app.dependency_overrides[get_history_repository] = lambda: history_repo

    mock_graph = IntegrationMockAgentGraph([])
    app.dependency_overrides[get_agent_orchestrator] = lambda: mock_graph

    payload = {
        "query": "Làm thế nào để chăm sóc Poodle?",
        "session_id": str(session.id),
        "stream": False,
    }

    # 4. Fire REST call
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/chat", json=payload)

    # 5. Assert API contracts
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Đây là kết quả tư vấn tích hợp thực tế."
    assert data["session_id"] == str(session.id)
    assert len(data["tool_calls"]) == 1
    assert data["tool_calls"][0]["tool_name"] == "vector_search"

    # 6. Verify real DB integration (both User & Assistant messages written to test_db)
    saved_history = await history_repo.get_by_session(session.id)
    assert len(saved_history) == 2
    assert saved_history[0].content == "Làm thế nào để chăm sóc Poodle?"
    assert saved_history[0].role.value == "user"
    assert saved_history[1].content == "Đây là kết quả tư vấn tích hợp thực tế."
    assert saved_history[1].role.value == "assistant"
    assert len(saved_history[1].tool_calls) == 1


@pytest.mark.asyncio
async def test_full_chat_flow_sse_integration(test_db: AsyncIOMotorDatabase) -> None:
    """Verify full chat flow under SSE streaming mode with database logging."""
    app = create_app()

    session_repo = SessionRepository(db=test_db)
    history_repo = HistoryRepository(db=test_db)

    user_id = "integration_sse_member"
    session = ChatSession.create(user_id=user_id)
    await session_repo.create(session)

    app.dependency_overrides[get_current_user] = lambda: User.authenticated(user_id)
    app.dependency_overrides[get_session_repository] = lambda: session_repo
    app.dependency_overrides[get_history_repository] = lambda: history_repo

    chunks = [
        {"intent_analyzer": {"tools_to_execute": [{"tool": "mongo_query"}]}},
        {
            "tool_executor": {
                "tool_results": {
                    "mongo_query": {
                        "output_summary": "Tìm thấy đơn hàng hạt cho chó mèo",
                        "success": True,
                    }
                }
            }
        },
        {"response_generator": {"final_response": "Đây là kết quả stream sse."}},
    ]
    mock_graph = IntegrationMockAgentGraph(chunks)
    app.dependency_overrides[get_agent_orchestrator] = lambda: mock_graph

    payload = {
        "query": "Kiểm tra đơn hàng của tôi",
        "session_id": str(session.id),
        "stream": True,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Decode lines
    lines = [line for line in response.iter_lines() if line.startswith("data:")]
    events = [json.loads(line[5:].strip()) for line in lines]

    assert len(events) >= 5
    assert events[0]["type"] == "thinking"
    assert events[1]["type"] == "tool_call"
    assert events[1]["tool"] == "mongo_query"
    assert events[2]["type"] == "tool_result"
    assert events[2]["tool"] == "mongo_query"
    assert events[2]["summary"] == "Tìm thấy đơn hàng hạt cho chó mèo"
    assert events[3]["type"] == "answer"
    assert events[3]["content"] == "Đây là kết quả stream sse."
    assert events[4]["type"] == "done"
    assert events[4]["session_id"] == str(session.id)

    # Allow tiny delay for async tasks to persist to DB
    await asyncio.sleep(0.05)

    # Verify data successfully committed to the test database
    saved_history = await history_repo.get_by_session(session.id)
    assert len(saved_history) == 2
    assert saved_history[0].content == "Kiểm tra đơn hàng của tôi"
    assert saved_history[1].content == "Đây là kết quả stream sse."
