"""Tool executor node for the Agent Orchestrator."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter
from pnetai_chatbot.domain.entities.tool_result import ToolCallResult
from pnetai_chatbot.infrastructure.agent.state import AgentState
from pnetai_chatbot.infrastructure.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutorNode:
    """Node that concurrently executes all selected tools.

    Integrates with the ToolRegistry to invoke Qdrant vector search,
    MongoDB query validation/execution, and Tavily web search.
    """

    def __init__(self, registry: ToolRegistry, llm: ILLMAdapter) -> None:
        """Initialize the ToolExecutorNode.

        Args:
            registry: The tool registry instance holding active tool ports.
            llm: LLM adapter instance (for embeddings and mongo gen queries).
        """
        self._registry = registry
        self._llm = llm

    async def _execute_single_tool(
        self,
        tool_spec: dict[str, Any],
        user_id: str | None,
    ) -> ToolCallResult:
        """Execute a single tool based on its specification.

        Args:
            tool_spec: Specification dict from the intent analyzer.
            user_id: Optional ID of the authenticated user.

        Returns:
            A populated ToolCallResult object.
        """
        tool_name = tool_spec.get("tool")
        reason = tool_spec.get("reason", "")
        params_hint = tool_spec.get("params_hint", {})

        logger.info("Executing tool '%s' for reason: '%s'", tool_name, reason)
        start_time = time.perf_counter()

        try:
            tool_inst = self._registry.get_tool(tool_name)
        except KeyError as e:
            return ToolCallResult(
                tool_name=str(tool_name),
                input_summary=str(params_hint),
                success=False,
                error_message=f"Tool registry lookup failed: {e}",
            )

        try:
            if tool_name == "tavily_search":
                query = params_hint.get("query", "")
                results = await tool_inst.search(query=query, max_results=5)
                # Map results to raw dict
                data = {
                    "results": [
                        {
                            "title": r.title,
                            "url": r.url,
                            "content": r.content,
                            "score": r.score,
                        }
                        for r in results
                    ]
                }
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                return ToolCallResult(
                    tool_name=tool_name,
                    input_summary=f"Web search: '{query}'",
                    output_summary=f"Found {len(results)} web results",
                    execution_time_ms=elapsed_ms,
                    data=data,
                    success=True,
                )

            elif tool_name == "vector_search":
                query = params_hint.get("query", "")
                # 1. Generate query embedding using the LLM
                embedding = await self._llm.embed(query)
                # 2. Query Qdrant
                results = await tool_inst.similarity_search(
                    query_embedding=embedding, top_k=5
                )
                data = {
                    "results": [
                        {
                            "id": r.id,
                            "content": r.content,
                            "score": r.score,
                            "metadata": r.metadata,
                        }
                        for r in results
                    ]
                }
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                return ToolCallResult(
                    tool_name=tool_name,
                    input_summary=f"Vector search: '{query}'",
                    output_summary=f"Retrieved {len(results)} documents",
                    execution_time_ms=elapsed_ms,
                    data=data,
                    success=True,
                )

            elif tool_name == "mongodb_query":
                collection = params_hint.get("collection", "")
                query_intent = params_hint.get("query_intent", "")

                # 1. Retrieve the schema description to inject to LLM
                schema_context = await tool_inst.get_schema_context(collection)

                # 2. Invoke generator
                from pnetai_chatbot.infrastructure.tools.mongo_query_tool import MongoQueryGenerator
                generator = MongoQueryGenerator(self._llm)
                generated = await generator.generate_query(
                    user_query=query_intent,
                    collection=collection,
                    schema_context=schema_context,
                )

                # 3. Execute query with validation
                results = await tool_inst.execute_generated_query(
                    collection=collection,
                    filter_query=generated.get("filter", {}),
                    projection=generated.get("projection"),
                    limit=generated.get("limit", 20),
                    sort=generated.get("sort"),
                    user_id=user_id,
                )
                data = {"results": results, "generated_query": generated}
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                return ToolCallResult(
                    tool_name=tool_name,
                    input_summary=f"Collection '{collection}': {query_intent}",
                    output_summary=f"Found {len(results)} matches in {collection}",
                    execution_time_ms=elapsed_ms,
                    data=data,
                    success=True,
                )

            else:
                return ToolCallResult(
                    tool_name=str(tool_name),
                    input_summary=str(params_hint),
                    success=False,
                    error_message=f"Unsupported tool name: {tool_name}",
                )

        except Exception as e:
            logger.error("Error executing tool '%s': %s", tool_name, e)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return ToolCallResult(
                tool_name=str(tool_name),
                input_summary=str(params_hint),
                execution_time_ms=elapsed_ms,
                success=False,
                error_message=f"Execution error: {e}",
            )

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        """Execute the tool executor node concurrently.

        Args:
            state: The current agent execution state.

        Returns:
            Dictionary containing state updates.
        """
        tools_list = state.get("tools_to_execute", [])
        user_id = state.get("user_id")

        if not tools_list:
            logger.info("No tools to execute in this iteration.")
            return {
                "tool_calls_made": state.get("tool_calls_made", []),
                "tool_results": state.get("tool_results", {}),
                "iterations": state.get("iterations", 0) + 1,
            }

        # Concurrently execute all tools
        logger.info("Executing %d tools concurrently...", len(tools_list))
        tasks = [self._execute_single_tool(t, user_id=user_id) for t in tools_list]
        results: list[ToolCallResult] = await asyncio.gather(*tasks)

        # Merge results into state
        new_calls = list(state.get("tool_calls_made", []))
        current_results = dict(state.get("tool_results", {}))

        messages_to_add = []
        for spec, res in zip(tools_list, results, strict=True):
            tool_name = spec.get("tool", "unknown")
            new_calls.append(tool_name)
            current_results[tool_name] = res.model_dump()

            status = "Success" if res.success else "Failed"
            messages_to_add.append(
                {
                    "role": "assistant",
                    "content": (
                        f"Executed Tool: {tool_name}\n"
                        f"Status: {status}\n"
                        f"Summary: {res.output_summary or res.error_message}"
                    ),
                }
            )

        return {
            "tool_calls_made": new_calls,
            "tool_results": current_results,
            "tools_to_execute": [],  # Clear pending tools
            "iterations": state.get("iterations", 0) + 1,
            "messages": messages_to_add,
        }


BaseNode = ToolExecutorNode
