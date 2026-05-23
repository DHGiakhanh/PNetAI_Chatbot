"""Unit tests for QdrantVectorSearchTool."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from qdrant_client import AsyncQdrantClient

from pnetai_chatbot.application.ports.vector_store_port import VectorSearchResult
from pnetai_chatbot.infrastructure.tools.vector_search_tool import (
    QdrantVectorSearchTool,
)


@pytest.mark.asyncio
async def test_vector_search_tool_init() -> None:
    """Test that QdrantVectorSearchTool initializes correctly."""
    mock_client = MagicMock(spec=AsyncQdrantClient)
    tool = QdrantVectorSearchTool(client=mock_client, collection_name="test_kb")
    assert tool._client == mock_client
    assert tool._collection_name == "test_kb"


@pytest.mark.asyncio
async def test_vector_search_tool_similarity_search_success() -> None:
    """Test that similarity_search successfully queries Qdrant and maps results."""
    mock_client = MagicMock(spec=AsyncQdrantClient)
    mock_client.search = AsyncMock()

    # Define mock ScoredPoints returned from Qdrant
    mock_point_1 = MagicMock()
    mock_point_1.id = "uuid-1"
    mock_point_1.score = 0.92
    mock_point_1.payload = {
        "title": "Dog Nutrition",
        "content": "Feed protein-rich food.",
        "category": "nutrition",
    }

    mock_point_2 = MagicMock()
    mock_point_2.id = "uuid-2"
    mock_point_2.score = 0.81
    mock_point_2.payload = {
        "title": "Dog Health",
        "content": "Schedule vaccines.",
        "category": "healthcare",
    }

    mock_client.search.return_value = [mock_point_1, mock_point_2]

    tool = QdrantVectorSearchTool(client=mock_client, collection_name="test_kb")
    embedding = [0.1] * 1536
    filters = {"must": [{"key": "category", "match": {"value": "nutrition"}}]}

    results = await tool.similarity_search(
        query_embedding=embedding, top_k=2, filters=filters
    )

    # Assert client.search called with correct args
    mock_client.search.assert_called_once_with(
        collection_name="test_kb",
        query_vector=embedding,
        limit=2,
        query_filter=filters,
        with_payload=True,
    )

    # Assert results mapping
    assert len(results) == 2
    assert all(isinstance(r, VectorSearchResult) for r in results)

    assert results[0].id == "uuid-1"
    assert results[0].score == 0.92
    assert results[0].content == "Feed protein-rich food."
    assert results[0].metadata == {
        "title": "Dog Nutrition",
        "content": "Feed protein-rich food.",
        "category": "nutrition",
    }

    assert results[1].id == "uuid-2"
    assert results[1].score == 0.81
    assert results[1].content == "Schedule vaccines."
    assert results[1].metadata == {
        "title": "Dog Health",
        "content": "Schedule vaccines.",
        "category": "healthcare",
    }


@pytest.mark.asyncio
async def test_vector_search_tool_similarity_search_failure() -> None:
    """Test that similarity_search propagates exceptions raised by Qdrant."""
    mock_client = MagicMock(spec=AsyncQdrantClient)
    mock_client.search = AsyncMock(side_effect=Exception("Qdrant unavailable"))

    tool = QdrantVectorSearchTool(client=mock_client, collection_name="test_kb")
    embedding = [0.1] * 1536

    with pytest.raises(Exception, match="Qdrant unavailable"):
        await tool.similarity_search(query_embedding=embedding)
