"""Agent Orchestrator building the LangGraph StateGraph pipeline."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter
from pnetai_chatbot.infrastructure.agent.nodes.context_merger import ContextMergerNode
from pnetai_chatbot.infrastructure.agent.nodes.intent_analyzer import IntentAnalyzerNode
from pnetai_chatbot.infrastructure.agent.nodes.response_generator import (
    ResponseGeneratorNode,
)
from pnetai_chatbot.infrastructure.agent.nodes.tool_executor import ToolExecutorNode
from pnetai_chatbot.infrastructure.agent.state import AgentState
from pnetai_chatbot.infrastructure.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

# Max loop limit to avoid high billing or infinite loops
MAX_TOOL_ITERATIONS = 3


def route_after_analyzer(state: AgentState) -> str:
    """Determine the next node based on the analyzer's output and iteration count.

    Args:
        state: The current agent execution state.

    Returns:
        The name of the next node to transition to.
    """
    tools = state.get("tools_to_execute", [])
    iterations = state.get("iterations", 0)

    if tools and iterations < MAX_TOOL_ITERATIONS:
        logger.info(
            "Routing to tool_executor (Iteration %d/%d, Tools: %s)",
            iterations,
            MAX_TOOL_ITERATIONS,
            [t.get("tool") for t in tools],
        )
        return "tool_executor"

    logger.info(
        "Routing to context_merger (Iteration %d/%d, Tools spec empty: %s)",
        iterations,
        MAX_TOOL_ITERATIONS,
        not tools,
    )
    return "context_merger"


class AgentOrchestrator:
    """Builder for the LangGraph multi-step ReAct orchestration pipeline."""

    def __init__(self, registry: ToolRegistry, llm: ILLMAdapter) -> None:
        """Initialize the AgentOrchestrator.

        Args:
            registry: The tool registry instance containing active tool ports.
            llm: The primary LLM adapter for reasoning and synthesis nodes.
        """
        self._registry = registry
        self._llm = llm

    def build_agent_graph(self) -> Any:
        """Build and compile the LangGraph StateGraph.

        Returns:
            The compiled, executable LangGraph instance.
        """
        # 1. Initialize StateGraph with TypedDict AgentState
        workflow = StateGraph(AgentState)

        # 2. Add active nodes to graph
        workflow.add_node("intent_analyzer", IntentAnalyzerNode(self._llm))
        workflow.add_node("tool_executor", ToolExecutorNode(self._registry, self._llm))
        workflow.add_node("context_merger", ContextMergerNode())
        workflow.add_node("response_generator", ResponseGeneratorNode(self._llm))

        # 3. Setup structural edges
        workflow.add_edge(START, "intent_analyzer")

        # 4. Add conditional routing from intent_analyzer
        workflow.add_conditional_edges(
            "intent_analyzer",
            route_after_analyzer,
            {
                "tool_executor": "tool_executor",
                "context_merger": "context_merger",
            },
        )

        # 5. Connect tool execution loop back to analyzer
        workflow.add_edge("tool_executor", "intent_analyzer")

        # 6. Final response pipeline edges
        workflow.add_edge("context_merger", "response_generator")
        workflow.add_edge("response_generator", END)

        logger.info("LangGraph agent orchestrator constructed and compiled.")
        return workflow.compile()
