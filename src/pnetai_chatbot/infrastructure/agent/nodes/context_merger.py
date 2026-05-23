"""Context merger node for the Agent Orchestrator."""

from __future__ import annotations

import logging
from typing import Any

from pnetai_chatbot.infrastructure.agent.state import AgentState

logger = logging.getLogger(__name__)


class ContextMergerNode:
    """Node that aggregates and formats all tool execution results.

    Synthesizes raw outputs from MongoDB queries, vector similarity lookups,
    and web searches into a single unified markdown block.
    """

    def __call__(self, state: AgentState) -> dict[str, Any]:
        """Execute the context merger node.

        Args:
            state: The current agent execution state.

        Returns:
            Dictionary containing state updates.
        """
        results_dict = state.get("tool_results", {})

        if not results_dict:
            logger.info("No tool results to merge. Creating empty context.")
            return {"unified_context": "No external context was retrieved."}

        logger.info("Merging results from tools: %s", list(results_dict.keys()))
        context_parts = []

        # 1. Format MongoDB Results
        if "mongodb_query" in results_dict:
            res = results_dict["mongodb_query"]
            if res.get("success") and res.get("data"):
                items = res["data"].get("results", [])
                generated = res["data"].get("generated_query", {})
                coll = generated.get("collection", "database")

                if items:
                    part = f"### [Database Query] Results from collection '{coll}':\n"
                    for idx, doc in enumerate(items, 1):
                        part += f"{idx}. "
                        fields = []
                        for k, v in doc.items():
                            if k == "_id":
                                continue
                            fields.append(f"**{k}**: {v}")
                        part += " | ".join(fields) + "\n"
                    context_parts.append(part)
                else:
                    context_parts.append(
                        f"### [Database Query] "
                        f"No records found in collection '{coll}'.\n"
                    )
            elif not res.get("success"):
                context_parts.append(
                    f"### [Database Query] Failed: {res.get('error_message')}\n"
                )

        # 2. Format Vector Search Results
        if "vector_search" in results_dict:
            res = results_dict["vector_search"]
            if res.get("success") and res.get("data"):
                docs = res["data"].get("results", [])
                if docs:
                    part = "### [Knowledge Base] Similar articles and advice:\n"
                    for idx, doc in enumerate(docs, 1):
                        meta = doc.get("metadata") or {}
                        title = meta.get("title", f"Document {idx}")
                        content = doc.get("content", "").strip()
                        score = doc.get("score", 0)
                        part += f"**{idx}. {title}** (Relevance: {score:.2f})\n"
                        part += f"   *Snippet*: {content}\n\n"
                    context_parts.append(part)
                else:
                    context_parts.append(
                        "### [Knowledge Base] No relevant articles found.\n"
                    )
            elif not res.get("success"):
                context_parts.append(
                    f"### [Knowledge Base] Failed: {res.get('error_message')}\n"
                )

        # 3. Format Tavily Search Results
        if "tavily_search" in results_dict:
            res = results_dict["tavily_search"]
            if res.get("success") and res.get("data"):
                web_hits = res["data"].get("results", [])
                if web_hits:
                    part = "### [Web Search] Internet search results:\n"
                    for idx, hit in enumerate(web_hits, 1):
                        title = hit.get("title", f"Web Result {idx}")
                        url = hit.get("url", "#")
                        content = hit.get("content", "").strip()
                        part += f"**{idx}. [{title}]({url})**\n"
                        part += f"   *Snippet*: {content}\n\n"
                    context_parts.append(part)
                else:
                    context_parts.append("### [Web Search] No web results found.\n")
            elif not res.get("success"):
                context_parts.append(
                    f"### [Web Search] Failed: {res.get('error_message')}\n"
                )

        unified = "\n\n".join(context_parts).strip()
        return {"unified_context": unified}


BaseNode = ContextMergerNode
