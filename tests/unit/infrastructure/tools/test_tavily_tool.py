"""Unit tests for TavilyWebSearchTool."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from pnetai_chatbot.application.ports.web_search_port import WebSearchResult
from pnetai_chatbot.infrastructure.tools.tavily_tool import TavilyWebSearchTool


@pytest.mark.asyncio
async def test_tavily_tool_init() -> None:
    """Test that TavilyWebSearchTool initializes correctly."""
    tool = TavilyWebSearchTool(api_key="tvly-test-key")
    assert tool._client is not None


@pytest.mark.asyncio
async def test_tavily_tool_search_success() -> None:
    """Test that TavilyWebSearchTool successfully searches and maps results."""
    mock_results = {
        "results": [
            {
                "title": "Dog Care Guide",
                "url": "https://example.com/dog-care",
                "content": "A comprehensive guide on taking care of dogs.",
                "score": 0.95,
            },
            {
                "title": "Healthy Pet Food",
                "url": "https://example.com/pet-food",
                "content": "Articles about high protein ingredients.",
                "score": 0.88,
            },
        ]
    }

    # Patch AsyncTavilyClient.search to return mock results
    with patch(
        "tavily.AsyncTavilyClient.search", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_results

        tool = TavilyWebSearchTool(api_key="tvly-test-key")
        results = await tool.search(
            query="dog care", max_results=2, search_depth="advanced"
        )

        # Assert client was called correctly
        mock_search.assert_called_once_with(
            query="dog care", max_results=2, search_depth="advanced"
        )

        # Assert results were mapped correctly
        assert len(results) == 2
        assert all(isinstance(r, WebSearchResult) for r in results)

        assert results[0].title == "Dog Care Guide"
        assert results[0].url == "https://example.com/dog-care"
        assert results[0].content == "A comprehensive guide on taking care of dogs."
        assert results[0].score == 0.95

        assert results[1].title == "Healthy Pet Food"
        assert results[1].url == "https://example.com/pet-food"
        assert results[1].content == "Articles about high protein ingredients."
        assert results[1].score == 0.88


@pytest.mark.asyncio
async def test_tavily_tool_search_failure() -> None:
    """Test that TavilyWebSearchTool propagates exceptions on client error."""
    with patch(
        "tavily.AsyncTavilyClient.search", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = Exception("API connection error")

        tool = TavilyWebSearchTool(api_key="tvly-test-key")
        with pytest.raises(Exception, match="API connection error"):
            await tool.search(query="dog care")
