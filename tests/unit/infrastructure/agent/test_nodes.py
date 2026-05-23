"""Unit tests for Agent Orchestrator nodes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter, LLMResponse
from pnetai_chatbot.application.ports.mongo_query_port import IMongoQueryExecutor
from pnetai_chatbot.application.ports.vector_store_port import (
    IVectorStore,
    VectorSearchResult,
)
from pnetai_chatbot.application.ports.web_search_port import (
    IWebSearchTool,
    WebSearchResult,
)
from pnetai_chatbot.infrastructure.agent.nodes.context_merger import ContextMergerNode
from pnetai_chatbot.infrastructure.agent.nodes.intent_analyzer import IntentAnalyzerNode
from pnetai_chatbot.infrastructure.agent.nodes.response_generator import (
    ResponseGeneratorNode,
)
from pnetai_chatbot.infrastructure.agent.nodes.tool_executor import ToolExecutorNode
from pnetai_chatbot.infrastructure.agent.state import AgentState
from pnetai_chatbot.infrastructure.tools.tool_registry import ToolRegistry


# ==========================================
# 1. IntentAnalyzerNode Tests
# ==========================================
@pytest.mark.asyncio
async def test_intent_analyzer_node_success() -> None:
    """Test successful intent analysis output parsing."""
    mock_llm = MagicMock(spec=ILLMAdapter)
    mock_response = MagicMock(spec=LLMResponse)
    mock_response.text = """
    ```json
    {
      "reasoning": "User asks about poodle food, products are in MongoDB.",
      "tools_needed": [
        {
          "tool": "mongodb_query",
          "priority": 1,
          "reason": "Search products collection for poodle food",
          "params_hint": {
            "collection": "products",
            "query_intent": "poodle dog food under 300k"
          }
        }
      ]
    }
    ```
    """
    mock_llm.chat = AsyncMock(return_value=mock_response)

    node = IntentAnalyzerNode(llm=mock_llm)
    state: AgentState = {
        "query": "Thức ăn cho chó poodle dưới 300k",
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

    result = await node(state)

    assert len(result["tools_to_execute"]) == 1
    assert result["tools_to_execute"][0]["tool"] == "mongodb_query"
    assert "Intent Analysis" in result["messages"][0]["content"]


@pytest.mark.asyncio
async def test_intent_analyzer_node_invalid_json() -> None:
    """Test intent analysis node fallback when LLM yields bad JSON."""
    mock_llm = MagicMock(spec=ILLMAdapter)
    mock_response = MagicMock(spec=LLMResponse)
    mock_response.text = "Normal conversational text response."
    mock_llm.chat = AsyncMock(return_value=mock_response)

    node = IntentAnalyzerNode(llm=mock_llm)
    state: AgentState = {
        "query": "Hello",
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

    result = await node(state)

    assert result["tools_to_execute"] == []
    assert "Failed to parse intent JSON" in result["error"]


# ==========================================
# 2. ToolExecutorNode Tests
# ==========================================
@pytest.mark.asyncio
async def test_tool_executor_tavily() -> None:
    """Test executing Tavily web search tool within node."""
    mock_search = MagicMock(spec=IWebSearchTool)
    mock_search.search = AsyncMock(
        return_value=[
            WebSearchResult(
                title="Poodle Care",
                url="https://example.com/poodle",
                content="Poodle grooming secrets",
                score=0.95,
            )
        ]
    )

    registry = ToolRegistry(
        web_search_tool=mock_search,
        vector_store_tool=MagicMock(spec=IVectorStore),
        mongo_query_executor=MagicMock(spec=IMongoQueryExecutor),
    )

    mock_llm = MagicMock(spec=ILLMAdapter)
    node = ToolExecutorNode(registry=registry, llm=mock_llm)

    state: AgentState = {
        "query": "Vector query",
        "session_id": "session-123",
        "user_id": None,
        "is_authenticated": False,
        "conversation_history": [],
        "session_summary": None,
        "messages": [],
        "tool_calls_made": [],
        "tool_results": {},
        "tools_to_execute": [
            {
                "tool": "tavily_search",
                "priority": 1,
                "reason": "Find details online",
                "params_hint": {"query": "poodle care tips"},
            }
        ],
        "unified_context": None,
        "final_response": None,
        "error": None,
        "iterations": 0,
    }

    result = await node(state)

    assert "tavily_search" in result["tool_calls_made"]
    res_data = result["tool_results"]["tavily_search"]
    assert res_data["success"] is True
    assert len(res_data["data"]["results"]) == 1
    assert res_data["data"]["results"][0]["title"] == "Poodle Care"
    assert result["iterations"] == 1


@pytest.mark.asyncio
async def test_tool_executor_vector() -> None:
    """Test executing vector similarity search with embedded lookup."""
    mock_store = MagicMock(spec=IVectorStore)
    mock_store.similarity_search = AsyncMock(
        return_value=[
            VectorSearchResult(
                id="doc-1",
                content="Knowledge doc",
                score=0.88,
                metadata={"title": "Doc Title"},
            )
        ]
    )

    registry = ToolRegistry(
        web_search_tool=MagicMock(spec=IWebSearchTool),
        vector_store_tool=mock_store,
        mongo_query_executor=MagicMock(spec=IMongoQueryExecutor),
    )

    mock_llm = MagicMock(spec=ILLMAdapter)
    mock_llm.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

    node = ToolExecutorNode(registry=registry, llm=mock_llm)

    state: AgentState = {
        "query": "query",
        "session_id": "session-123",
        "user_id": None,
        "is_authenticated": False,
        "conversation_history": [],
        "session_summary": None,
        "messages": [],
        "tool_calls_made": [],
        "tool_results": {},
        "tools_to_execute": [
            {
                "tool": "vector_search",
                "priority": 1,
                "reason": "Search KB",
                "params_hint": {"query": "vector query"},
            }
        ],
        "unified_context": None,
        "final_response": None,
        "error": None,
        "iterations": 0,
    }

    result = await node(state)

    mock_llm.embed.assert_called_once_with("vector query")
    assert "vector_search" in result["tool_calls_made"]
    assert result["tool_results"]["vector_search"]["success"] is True


# ==========================================
# 3. ContextMergerNode Tests
# ==========================================
def test_context_merger_node() -> None:
    """Test merging diverse tool outputs into unified context string."""
    node = ContextMergerNode()
    state: AgentState = {
        "query": "",
        "session_id": "session-123",
        "user_id": None,
        "is_authenticated": False,
        "conversation_history": [],
        "session_summary": None,
        "messages": [],
        "tool_calls_made": [],
        "tool_results": {
            "mongodb_query": {
                "success": True,
                "data": {
                    "results": [{"name": "Dog food", "price": 10000}],
                    "generated_query": {"collection": "products"},
                },
            },
            "vector_search": {
                "success": True,
                "data": {
                    "results": [
                        {
                            "content": "Veterinary advice snippet",
                            "score": 0.9,
                            "metadata": {"title": "Dog Tips"},
                        }
                    ]
                },
            },
        },
        "tools_to_execute": [],
        "unified_context": None,
        "final_response": None,
        "error": None,
        "iterations": 0,
    }

    result = node(state)

    assert "unified_context" in result
    context = result["unified_context"]
    assert "Dog food" in context
    assert "Veterinary advice snippet" in context


# ==========================================
# 4. ResponseGeneratorNode Tests
# ==========================================
@pytest.mark.asyncio
async def test_response_generator_node() -> None:
    """Test generating natural chatbot expert responses."""
    mock_llm = MagicMock(spec=ILLMAdapter)
    mock_response = MagicMock(spec=LLMResponse)
    mock_response.text = "Hello! Here is the expert advice on poodle care."
    mock_llm.chat = AsyncMock(return_value=mock_response)

    node = ResponseGeneratorNode(llm=mock_llm)
    state: AgentState = {
        "query": "Advice",
        "session_id": "session-123",
        "user_id": None,
        "is_authenticated": False,
        "conversation_history": [],
        "session_summary": None,
        "messages": [],
        "tool_calls_made": [],
        "tool_results": {},
        "tools_to_execute": [],
        "unified_context": "Unified search context text",
        "final_response": None,
        "error": None,
        "iterations": 0,
    }

    result = await node(state)

    assert (
        result["final_response"] == "Hello! Here is the expert advice on poodle care."
    )
    assert len(result["messages"]) == 1
    assert (
        result["messages"][0]["content"]
        == "Hello! Here is the expert advice on poodle care."
    )
