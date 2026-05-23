"""Unit tests for ToolRegistry."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pnetai_chatbot.application.ports.mongo_query_port import IMongoQueryExecutor
from pnetai_chatbot.application.ports.vector_store_port import IVectorStore
from pnetai_chatbot.application.ports.web_search_port import IWebSearchTool
from pnetai_chatbot.infrastructure.tools.tool_registry import ToolRegistry


def test_tool_registry_success() -> None:
    """Test that ToolRegistry registers and retrieves tools correctly."""
    mock_search = MagicMock(spec=IWebSearchTool)
    mock_vector = MagicMock(spec=IVectorStore)
    mock_mongo = MagicMock(spec=IMongoQueryExecutor)

    registry = ToolRegistry(
        web_search_tool=mock_search,
        vector_store_tool=mock_vector,
        mongo_query_executor=mock_mongo,
    )

    # List tools
    tool_names = registry.list_tools()
    assert len(tool_names) == 3
    assert "tavily_search" in tool_names
    assert "vector_search" in tool_names
    assert "mongodb_query" in tool_names

    # Retrieve tools
    assert registry.get_tool("tavily_search") == mock_search
    assert registry.get_tool("vector_search") == mock_vector
    assert registry.get_tool("mongodb_query") == mock_mongo


def test_tool_registry_not_found() -> None:
    """Test that ToolRegistry raises KeyError for unknown tool names."""
    mock_search = MagicMock(spec=IWebSearchTool)
    mock_vector = MagicMock(spec=IVectorStore)
    mock_mongo = MagicMock(spec=IMongoQueryExecutor)

    registry = ToolRegistry(
        web_search_tool=mock_search,
        vector_store_tool=mock_vector,
        mongo_query_executor=mock_mongo,
    )

    with pytest.raises(KeyError, match="Tool 'unknown_tool' is not registered"):
        registry.get_tool("unknown_tool")
