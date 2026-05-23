"""Unit and integration tests for the LangGraph Agent Orchestrator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from pnetai_chatbot.application.ports.history_repo_port import IHistoryRepository
from pnetai_chatbot.application.ports.llm_port import ILLMAdapter, LLMResponse
from pnetai_chatbot.application.ports.mongo_query_port import IMongoQueryExecutor
from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository
from pnetai_chatbot.application.ports.vector_store_port import IVectorStore
from pnetai_chatbot.application.ports.web_search_port import IWebSearchTool
from pnetai_chatbot.application.use_cases.chat.chat_orchestrator_use_case import (
    ChatOrchestratorUseCase,
)
from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.session import ChatSession
from pnetai_chatbot.infrastructure.agent.orchestrator import AgentOrchestrator
from pnetai_chatbot.infrastructure.tools.tool_registry import ToolRegistry


@pytest.mark.asyncio
async def test_orchestrator_end_to_end_loop() -> None:
    """Test compiled StateGraph end-to-end multi-step ReAct routing."""
    # 1. Mock LLM adapter responses
    mock_llm = MagicMock(spec=ILLMAdapter)

    # 1st call: IntentAnalyzerNode decides mongodb_query is needed
    response1 = MagicMock(spec=LLMResponse)
    response1.text = """
    ```json
    {
      "reasoning": "Need pet products from MongoDB.",
      "tools_needed": [
        {
          "tool": "mongodb_query",
          "priority": 1,
          "reason": "Find dog toys",
          "params_hint": {
            "collection": "products",
            "query_intent": "dog toys"
          }
        }
      ]
    }
    ```
    """

    # 2nd call: MongoQueryGenerator translates query_intent into query schema
    response_gen = MagicMock(spec=LLMResponse)
    response_gen.text = """
    ```json
    {
      "collection": "products",
      "filter": {"name": {"$regex": "toy", "$options": "i"}},
      "projection": {"name": 1, "price": 1},
      "sort": {},
      "limit": 5
    }
    ```
    """

    # 3rd call: IntentAnalyzerNode sees tool result and decides we are done
    response2 = MagicMock(spec=LLMResponse)
    response2.text = """
    ```json
    {
      "reasoning": "Product details retrieved. Generating answer.",
      "tools_needed": []
    }
    ```
    """

    # 4th call: ResponseGeneratorNode generates the final response
    response3 = MagicMock(spec=LLMResponse)
    response3.text = "Here are the best dog toys available: Chew Toy - 50k VNĐ."

    mock_llm.chat = AsyncMock(
        side_effect=[response1, response_gen, response2, response3]
    )

    # 2. Mock MongoDB Query Tool execution
    mock_mongo = MagicMock(spec=IMongoQueryExecutor)
    mock_mongo.get_schema_context = AsyncMock(return_value="Mock schema context")
    mock_mongo.execute_generated_query = AsyncMock(
        return_value=[{"name": "Chew Toy", "price": 50000}]
    )

    registry = ToolRegistry(
        web_search_tool=MagicMock(spec=IWebSearchTool),
        vector_store_tool=MagicMock(spec=IVectorStore),
        mongo_query_executor=mock_mongo,
    )

    # 3. Compile graph
    orchestrator = AgentOrchestrator(registry=registry, llm=mock_llm)
    compiled_graph = orchestrator.build_agent_graph()

    # 4. Invoke graph
    initial_state = {
        "query": "Tìm đồ chơi cho chó",
        "session_id": "session-123",
        "user_id": None,
        "is_authenticated": False,
        "conversation_history": [],
        "session_summary": None,
        "messages": [],
        "tool_calls_made": [],
        "tool_results": {},
        "tools_to_execute": [],
        "unified_context": None,
        "final_response": None,
        "error": None,
        "iterations": 0,
    }

    final_state = await compiled_graph.ainvoke(initial_state)

    # 5. Assert results
    assert final_state["iterations"] == 1
    assert "mongodb_query" in final_state["tool_calls_made"]
    assert final_state["final_response"] == (
        "Here are the best dog toys available: Chew Toy - 50k VNĐ."
    )


@pytest.mark.asyncio
async def test_orchestrator_max_iteration_guard() -> None:
    """Test that max iteration guard halts infinite routing loops."""
    # LLM always returns a tool spec to execute (simulates looping)
    mock_llm = MagicMock(spec=ILLMAdapter)
    response_loop = MagicMock(spec=LLMResponse)
    response_loop.text = """
    ```json
    {
      "reasoning": "Need external info",
      "tools_needed": [
        {
          "tool": "tavily_search",
          "priority": 1,
          "reason": "Looping",
          "params_hint": {"query": "loop query"}
        }
      ]
    }
    ```
    """
    response_final = MagicMock(spec=LLMResponse)
    response_final.text = "Final fallback response after loop breaks."

    mock_llm.chat = AsyncMock(
        side_effect=[
            response_loop,  # analyzer 1
            response_loop,  # analyzer 2
            response_loop,  # analyzer 3
            response_final,  # final response generator
        ]
    )

    mock_search = MagicMock(spec=IWebSearchTool)
    mock_search.search = AsyncMock(return_value=[])

    registry = ToolRegistry(
        web_search_tool=mock_search,
        vector_store_tool=MagicMock(spec=IVectorStore),
        mongo_query_executor=MagicMock(spec=IMongoQueryExecutor),
    )

    orchestrator = AgentOrchestrator(registry=registry, llm=mock_llm)
    compiled_graph = orchestrator.build_agent_graph()

    initial_state = {
        "query": "Infinite loop test",
        "session_id": "session-123",
        "user_id": None,
        "is_authenticated": False,
        "conversation_history": [],
        "session_summary": None,
        "messages": [],
        "tool_calls_made": [],
        "tool_results": {},
        "tools_to_execute": [],
        "unified_context": None,
        "final_response": None,
        "error": None,
        "iterations": 0,
    }

    final_state = await compiled_graph.ainvoke(initial_state)

    # Should break exactly at MAX_TOOL_ITERATIONS = 3
    assert final_state["iterations"] == 3
    assert len(final_state["tool_calls_made"]) == 3
    assert final_state["final_response"] == "Final fallback response after loop breaks."


@pytest.mark.asyncio
async def test_chat_orchestrator_use_case() -> None:
    """Test ChatOrchestratorUseCase wrapping repositories and graph run."""
    # 1. Mock DB history and session repositories
    mock_history_repo = MagicMock(spec=IHistoryRepository)
    mock_history_repo.get_by_session = AsyncMock(return_value=[])

    mock_session_repo = MagicMock(spec=ISessionRepository)
    mock_session = ChatSession(
        id=uuid4(),
        user_id="user-1",
        is_guest=False,
        summary="Past conversation summary",
    )
    mock_session_repo.get_by_id = AsyncMock(return_value=mock_session)

    # 2. Mock Compiled Graph
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "final_response": "Expert veterinary answer.",
            "tool_results": {
                "vector_search": {
                    "success": True,
                    "input_summary": "KB lookup",
                    "output_summary": "Retrieved 1 doc",
                    "execution_time_ms": 12,
                    "data": {"results": []},
                }
            },
        }
    )

    # 3. Instantiate Use Case
    use_case = ChatOrchestratorUseCase(
        compiled_graph=mock_graph,
        session_repository=mock_session_repo,
        history_repository=mock_history_repo,
    )

    session_uuid = uuid4()
    msg = await use_case.execute(
        session_id=session_uuid,
        query="My dog has a fever",
        user_id="user-1",
        is_authenticated=True,
    )

    # 4. Verify use case interactions
    mock_session_repo.get_by_id.assert_called_once_with(session_uuid)
    mock_history_repo.get_by_session.assert_called_once_with(session_uuid, limit=20)

    # 5. Assert final Message mappings
    assert isinstance(msg, Message)
    assert msg.session_id == session_uuid
    assert msg.content == "Expert veterinary answer."
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0].tool_name == "vector_search"
    assert msg.tool_calls[0].success is True
    assert msg.tool_calls[0].execution_time_ms == 12
