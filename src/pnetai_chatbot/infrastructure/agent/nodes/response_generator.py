"""Response generator node for the Agent Orchestrator."""

from __future__ import annotations

import logging
from typing import Any

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter
from pnetai_chatbot.infrastructure.agent.prompts.agent_prompts import (
    RESPONSE_GENERATOR_SYSTEM_PROMPT,
)
from pnetai_chatbot.infrastructure.agent.state import AgentState

logger = logging.getLogger(__name__)


class ResponseGeneratorNode:
    """Node that synthesizes the final conversational response.

    Combines the user query, historical context, session summaries,
    and aggregated search contexts to generate a friendly, professional response.
    """

    def __init__(self, llm: ILLMAdapter) -> None:
        """Initialize the ResponseGeneratorNode.

        Args:
            llm: LLM adapter instance for final completion.
        """
        self._llm = llm

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        """Execute the response generator node.

        Args:
            state: The current agent execution state.

        Returns:
            Dictionary containing state updates.
        """
        query = state.get("query", "")
        history_list = state.get("conversation_history", [])
        summary = state.get("session_summary")
        context = state.get("unified_context")

        logger.info("Generating final response for query: '%s'", query)

        # 1. Format conversation history for prompt
        history_str = ""
        for msg in history_list:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_str += f"- {role.capitalize()}: {content}\n"

        prompt = RESPONSE_GENERATOR_SYSTEM_PROMPT.format(
            query=query,
            conversation_history=history_str or "No history available.",
            session_summary=summary or "No summary available.",
            context=context or "No context available.",
        )

        # 2. Invoke LLM to generate natural expert response (temp=0.7)
        try:
            response = await self._llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            final_text = response.text.strip()
        except Exception as e:
            logger.error("LLM call failed in response generator: %s", e)
            return {
                "error": f"Response generation failed: {e}",
                "final_response": (
                    "Tôi xin lỗi, hiện tại tôi đang gặp sự cố kỹ thuật "
                    "khi kết nối hệ thống. Xin vui lòng thử lại sau."
                ),
            }

        return {
            "final_response": final_text,
            "messages": [
                {
                    "role": "assistant",
                    "content": final_text,
                }
            ],
        }


BaseNode = ResponseGeneratorNode
