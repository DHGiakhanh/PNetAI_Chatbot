"""Global state definition for the Agent Orchestrator."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Global state for the LangGraph agent orchestrator.

    Attributes:
        query: User input query string.
        session_id: ID of the current chat session.
        user_id: Optional ID of the authenticated user.
        is_authenticated: True if the user is authenticated.
        conversation_history: List of past message dictionaries.
        session_summary: Optional summary of past messages.
        messages: LangGraph accumulated message list with add_messages reducer.
        tool_calls_made: List of tools that have been executed.
        tool_results: Dictionary mapping tool names/calls to results.
        final_response: Optional generated final answer string.
        error: Optional execution error message.
        iterations: Number of tool-calling iterations performed.
    """

    query: str
    session_id: str
    user_id: str | None
    is_authenticated: bool
    conversation_history: list[dict[str, Any]]
    session_summary: str | None
    messages: Annotated[list[Any], add_messages]
    tool_calls_made: list[str]
    tool_results: dict[str, Any]
    tools_to_execute: list[dict[str, Any]]
    unified_context: str | None
    final_response: str | None
    error: str | None
    iterations: int
