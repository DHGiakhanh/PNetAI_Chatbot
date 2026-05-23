"""Agent Tool Registry mapping tool names to tool instances."""

from __future__ import annotations

import logging
from typing import Any

from pnetai_chatbot.application.ports.mongo_query_port import IMongoQueryExecutor
from pnetai_chatbot.application.ports.vector_store_port import IVectorStore
from pnetai_chatbot.application.ports.web_search_port import IWebSearchTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry to manage and retrieve available agent tools."""

    def __init__(
        self,
        web_search_tool: IWebSearchTool,
        vector_store_tool: IVectorStore,
        mongo_query_executor: IMongoQueryExecutor,
    ) -> None:
        """Initialize the ToolRegistry with tool implementations.

        Args:
            web_search_tool: The web search tool instance.
            vector_store_tool: The vector store search tool instance.
            mongo_query_executor: The MongoDB query executor instance.
        """
        self._tools = {
            "tavily_search": web_search_tool,
            "vector_search": vector_store_tool,
            "mongodb_query": mongo_query_executor,
        }

    def get_tool(self, name: str) -> Any:
        """Retrieve a tool instance by name.

        Args:
            name: The name of the tool.

        Returns:
            The tool instance.

        Raises:
            KeyError: If the tool name is not registered.
        """
        if name not in self._tools:
            logger.error("Requested tool '%s' is not registered.", name)
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            A list of registered tool names.
        """
        return list(self._tools.keys())
