"""Intent analyzer node for the Agent Orchestrator."""

from __future__ import annotations

import json
import logging
from typing import Any

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter
from pnetai_chatbot.infrastructure.agent.prompts.agent_prompts import (
    INTENT_ANALYZER_SYSTEM_PROMPT,
)
from pnetai_chatbot.infrastructure.agent.state import AgentState

logger = logging.getLogger(__name__)


class IntentAnalyzerNode:
    """Node that analyzes user query intent to determine which tools are required.

    Uses an LLM at zero temperature to predict required tool queries based on
    the user's query and conversation history.
    """

    def __init__(self, llm: ILLMAdapter) -> None:
        """Initialize the IntentAnalyzerNode.

        Args:
            llm: LLM adapter instance for invoking chat requests.
        """
        self._llm = llm

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        """Execute the intent analyzer node.

        Args:
            state: The current agent execution state.

        Returns:
            Dictionary containing state updates.
        """
        iterations = state.get("iterations", 0)
        from pnetai_chatbot.infrastructure.agent.orchestrator import MAX_TOOL_ITERATIONS

        if iterations >= MAX_TOOL_ITERATIONS:
            logger.info(
                "Max iterations reached (%d/%d). Skipping intent analysis.",
                iterations,
                MAX_TOOL_ITERATIONS,
            )
            return {
                "tools_to_execute": [],
            }

        query = state.get("query", "")
        history_list = state.get("conversation_history", [])

        # 1. Format conversational history for the prompt
        history_str = ""
        for msg in history_list:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_str += f"- {role.capitalize()}: {content}\n"

        prompt = INTENT_ANALYZER_SYSTEM_PROMPT.format(
            query=query,
            conversation_history=history_str or "No history available.",
        )

        logger.info("Running intent analysis for query: '%s'", query)

        # 2. Invoke LLM with zero temperature for deterministic classification
        try:
            response = await self._llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            text = response.text.strip()
        except Exception as e:
            logger.error("LLM call failed in intent analyzer: %s", e)
            return {
                "error": f"Intent analyzer failed: {e}",
                "tools_to_execute": [],
            }

        # 3. Clean and parse JSON response
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            parsed = json.loads(text)
            tools_needed = parsed.get("tools_needed", [])
            # Sort tools by priority ascending (priority 1 runs first)
            tools_needed.sort(key=lambda t: t.get("priority", 99))
            logger.info(
                "Parsed tools needed: %s (Reasoning: %s)",
                [t.get("tool") for t in tools_needed],
                parsed.get("reasoning", "None provided"),
            )
            return {
                "tools_to_execute": tools_needed,
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Intent Analysis: {parsed.get('reasoning', '')}",
                    }
                ],
            }
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(
                "Failed to parse intent JSON: %s. Raw LLM response: %s",
                e,
                text,
            )
            # Default to no tools to avoid breaking execution
            return {
                "tools_to_execute": [],
                "error": f"Failed to parse intent JSON: {e}",
            }


BaseNode = IntentAnalyzerNode
