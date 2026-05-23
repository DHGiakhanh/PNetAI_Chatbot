"""Use case for orchestrating RAG search and multi-step chat responses."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import UUID4

from pnetai_chatbot.application.ports.history_repo_port import IHistoryRepository
from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository
from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.tool_result import ToolCallResult

if TYPE_CHECKING:
    from pnetai_chatbot.application.use_cases.session.summarize_session import (
        SummarizeSessionUseCase,
    )

logger = logging.getLogger(__name__)


class ChatOrchestratorUseCase:
    """Use case to invoke the LangGraph Agent Orchestrator.

    Resolves session history and summaries, runs the compiled agent graph,
    and formats the final output into standard domain Message entities.
    """

    def __init__(
        self,
        compiled_graph: Any,
        session_repository: ISessionRepository | None = None,
        history_repository: IHistoryRepository | None = None,
        summarize_use_case: SummarizeSessionUseCase | None = None,
    ) -> None:
        """Initialize the ChatOrchestratorUseCase.

        Args:
            compiled_graph: Compiled LangGraph instance.
            session_repository: Optional session database port.
            history_repository: Optional conversation history database port.
            summarize_use_case: Optional summarization use case.
        """
        self._graph = compiled_graph
        self._session_repo = session_repository
        self._history_repo = history_repository
        self._summarize_use_case = summarize_use_case

    async def execute(
        self,
        session_id: UUID4,
        query: str,
        user_id: str | None = None,
        is_authenticated: bool = False,
        override_history: list[dict[str, Any]] | None = None,
        override_summary: str | None = None,
        location: dict[str, Any] | None = None,
    ) -> Message:
        """Execute the LangGraph orchestrator loop.

        Args:
            session_id: UUID4 of the current chat session.
            query: The user input query string.
            user_id: Optional ID of the authenticated user.
            is_authenticated: True if the user has JWT credentials.
            override_history: Optional pre-loaded message history.
            override_summary: Optional pre-loaded session summary.

        Returns:
            The generated assistant Message entity.
        """
        logger.info(
            "Executing ChatOrchestratorUseCase for session %s (is_auth=%s)",
            session_id,
            is_authenticated,
        )

        # 1. Resolve session history and summary
        conversation_history = override_history or []
        session_summary = override_summary

        if not override_history and self._history_repo and self._session_repo:
            try:
                session = await self._session_repo.get_by_id(session_id)
                if session:
                    session_summary = session.summary

                messages = await self._history_repo.get_by_session(session_id, limit=20)
                for msg in messages:
                    role_val = (
                        msg.role.value if hasattr(msg.role, "value") else str(msg.role)
                    )
                    conversation_history.append(
                        {
                            "role": role_val,
                            "content": msg.content,
                        }
                    )
            except Exception as e:
                logger.error("Failed to load history in chat orchestrator: %s", e)

        # 2. Save user's incoming message if authenticated
        user_msg = Message.create_user_message(
            message_id=uuid4(),
            session_id=session_id,
            content=query,
        )
        if is_authenticated and self._history_repo:
            try:
                await self._history_repo.insert(user_msg)
            except Exception as e:
                logger.error("Failed to insert user message to history: %s", e)

        # 3. Build initial state for the LangGraph orchestrator
        initial_state = {
            "query": query,
            "session_id": str(session_id),
            "user_id": user_id,
            "is_authenticated": is_authenticated,
            "conversation_history": conversation_history,
            "session_summary": session_summary,
            "messages": [{"role": "user", "content": query}],
            "tool_calls_made": [],
            "tool_results": {},
            "tools_to_execute": [],
            "unified_context": None,
            "final_response": None,
            "error": None,
            "iterations": 0,
            "location": location,
        }

        # 4. Invoke compiled graph
        try:
            final_state = await self._graph.ainvoke(initial_state)
        except Exception as e:
            logger.error("LangGraph execution encountered an error: %s", e)
            return Message.create_assistant_message(
                session_id=session_id,
                content=(
                    "Tôi rất tiếc, đã có lỗi hệ thống xảy ra khi xử lý yêu cầu của bạn."
                ),
            )

        # 5. Construct domain assistant Message
        content = final_state.get(
            "final_response",
            "Tôi không thể tìm thấy câu trả lời phù hợp tại thời điểm này.",
        )

        # Parse tool calls metadata
        tool_results_dict = final_state.get("tool_results", {})
        tool_calls = []
        for name, res in tool_results_dict.items():
            tool_calls.append(
                ToolCallResult(
                    tool_name=name,
                    input_summary=res.get("input_summary", ""),
                    output_summary=res.get("output_summary", ""),
                    execution_time_ms=res.get("execution_time_ms", 0),
                    data=res.get("data", {}),
                    success=res.get("success", True),
                    error_message=res.get("error_message"),
                )
            )

        assistant_msg = Message.create_assistant_message(
            session_id=session_id,
            content=content,
            tool_calls=tool_calls,
        )

        # 6. Save assistant's generated message if authenticated
        if is_authenticated and self._history_repo:
            try:
                await self._history_repo.insert(assistant_msg)
            except Exception as e:
                logger.error("Failed to insert assistant message to history: %s", e)

        # 7. Check if message count % 10 == 0 and trigger auto-summarize
        if is_authenticated and self._session_repo and self._summarize_use_case:
            try:
                session = await self._session_repo.get_by_id(session_id)
                if (
                    session
                    and session.message_count > 0
                    and session.message_count % 10 == 0
                ):
                    asyncio.create_task(self._summarize_use_case.execute(session_id))
            except Exception as e:
                logger.error("Failed to trigger background summarization: %s", e)

        return assistant_msg
