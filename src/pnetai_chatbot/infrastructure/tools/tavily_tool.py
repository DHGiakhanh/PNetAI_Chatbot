"""Tavily search implementation of IWebSearchTool."""

from __future__ import annotations

import logging

from tavily import AsyncTavilyClient

from pnetai_chatbot.application.ports.web_search_port import (
    IWebSearchTool,
    WebSearchResult,
)

logger = logging.getLogger(__name__)


class TavilyWebSearchTool(IWebSearchTool):
    """Tavily search implementation of IWebSearchTool."""

    def __init__(self, api_key: str) -> None:
        """Initialize TavilyWebSearchTool with the given API key.

        Args:
            api_key: The Tavily API key.
        """
        if not api_key:
            logger.warning(
                "Tavily API key is empty. Web search tool will fail if used."
            )
        self._client = AsyncTavilyClient(api_key=api_key)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
    ) -> list[WebSearchResult]:
        """Search the web using Tavily.

        Args:
            query: The search query string.
            max_results: Maximum number of results.
            search_depth: 'basic' or 'advanced'.

        Returns:
            List of WebSearchResult objects.
        """
        logger.info(
            "Tavily search query: '%s' (depth=%s, limit=%d)",
            query,
            search_depth,
            max_results,
        )
        try:
            response = await self._client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
            )
            results = []
            for r in response.get("results", []):
                results.append(
                    WebSearchResult(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        content=r.get("content", ""),
                        score=r.get("score", 1.0),
                    )
                )
            return results
        except Exception as e:
            logger.error("Tavily search failed: %s", e)
            raise e
