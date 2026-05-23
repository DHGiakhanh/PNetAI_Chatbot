"""API endpoint for user interaction with the LangGraph multi-step chatbot agent."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from pnetai_chatbot.application.use_cases.chat.chat_orchestrator_use_case import (
    ChatOrchestratorUseCase,
)
from pnetai_chatbot.application.use_cases.session.resolve_user_context import (
    ResolveUserContextUseCase,
)
from pnetai_chatbot.application.use_cases.session.summarize_session import (
    SummarizeSessionUseCase,
)
from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.tool_result import ToolCallResult
from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.interface.api.v1.dependencies import (
    get_agent_orchestrator,
    get_chat_orchestrator,
    get_current_user,
    get_history_repository,
    get_resolve_context_use_case,
    get_session_repository,
    get_summarize_session_use_case,
)
from pnetai_chatbot.interface.schemas.chat_schema import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", tags=["Chat"], response_model=None)
async def process_chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    chat_orchestrator: ChatOrchestratorUseCase = Depends(get_chat_orchestrator),
    resolve_context: ResolveUserContextUseCase = Depends(get_resolve_context_use_case),
    agent_graph: Any = Depends(get_agent_orchestrator),
    history_repo: Any = Depends(get_history_repository),
    session_repo: Any = Depends(get_session_repository),
    summarize_use_case: SummarizeSessionUseCase = Depends(
        get_summarize_session_use_case
    ),
) -> ChatResponse | StreamingResponse:
    """Coordinate the chatbot reasoning and answer synthesis loops.

    Supports both non-streamed JSON and real-time Server-Sent Events (SSE) modes.

    Args:
        request: Pydantic request payload including query and session details.
        user: Context domain User entity.
        chat_orchestrator: ChatOrchestratorUseCase injector.
        resolve_context: ResolveUserContextUseCase injector.
        agent_graph: Compiled LangGraph state graph.
        history_repo: Message History repository.
        session_repo: Chat Session repository.
        summarize_use_case: Auto-summarization service.

    Returns:
        ChatResponse if non-streaming, or a StreamingResponse yielding SSE events.

    Raises:
        HTTPException: 500 on database failure, or 403 on ownership violation.
    """
    # 1. Resolve raw query with fallback support for natural field mapping
    raw_query = request.query or request.message
    if not raw_query:
        raise HTTPException(
            status_code=400,
            detail="Either 'query' or 'message' field must be provided.",
        )

    # 2. Package location parameters if present
    location_dict = None
    if request.location:
        location_dict = {
            "coordinates": request.location.coordinates,
            "addressName": request.location.addressName,
        }

    logger.info(
        "Chat request received. Query: '%s', Stream: %s, User: %s",
        raw_query,
        request.stream,
        user.id,
    )

    try:
        session, history = await resolve_context.execute(
            session_id=request.session_id,
            user_id=user.id,
        )
    except ValueError as e:
        logger.warning("Ownership validation failed on context resolve: %s", e)
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to resolve session context: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Internal error resolving session context.",
        )

    # Mode 1: Non-streamed JSON
    if not request.stream:
        try:
            assistant_msg = await chat_orchestrator.execute(
                session_id=session.id,
                query=raw_query,
                user_id=user.id,
                is_authenticated=user.is_authenticated,
                override_history=[
                    {
                        "role": h.role.value
                        if hasattr(h.role, "value")
                        else str(h.role),
                        "content": h.content,
                    }
                    for h in history
                ],
                override_summary=session.summary,
                location=location_dict,
            )

            # Map domain ToolCallResult to API response objects
            response_tools = []
            if assistant_msg.tool_calls:
                for tc in assistant_msg.tool_calls:
                    response_tools.append(
                        {
                            "tool_name": tc.tool_name,
                            "input_summary": tc.input_summary,
                            "output_summary": tc.output_summary,
                            "execution_time_ms": tc.execution_time_ms,
                            "success": tc.success,
                            "error_message": tc.error_message,
                        }
                    )

            return ChatResponse(
                answer=assistant_msg.content,
                session_id=session.id,
                tool_calls=response_tools,
                tokens_used=assistant_msg.tokens_used,
                model=assistant_msg.model,
            )
        except Exception as e:
            logger.error("Non-streamed chat failed: %s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Chat orchestration failed: {e}",
            )

    # Mode 2: Server-Sent Events (SSE) Streaming
    async def sse_event_generator() -> AsyncGenerator[str, None]:
        """Stream chunks using the compiled LangGraph StateGraph astream."""
        # 1. Save user's incoming message to persistent history if authenticated
        if user.is_authenticated and history_repo:
            user_msg = Message.create_user_message(
                message_id=uuid4(),
                session_id=session.id,
                content=raw_query,
            )
            try:
                await history_repo.insert(user_msg)
            except Exception as ex:
                logger.error("Failed to insert user message during stream: %s", ex)

        # 2. Build initial state
        conversation_history = [
            {
                "role": h.role.value if hasattr(h.role, "value") else str(h.role),
                "content": h.content,
            }
            for h in history
        ]
        initial_state = {
            "query": raw_query,
            "session_id": str(session.id),
            "user_id": user.id,
            "is_authenticated": user.is_authenticated,
            "conversation_history": conversation_history,
            "session_summary": session.summary,
            "messages": [{"role": "user", "content": raw_query}],
            "tool_calls_made": [],
            "tool_results": {},
            "tools_to_execute": [],
            "unified_context": None,
            "final_response": None,
            "error": None,
            "iterations": 0,
            "location": location_dict,
        }

        yield f"data: {json.dumps({'type': 'thinking', 'content': 'Đang phân tích câu hỏi...'}, ensure_ascii=False)}\n\n"

        final_response = "Tôi rất tiếc, đã có lỗi xảy ra khi xử lý yêu cầu."
        tool_results_dict = {}

        try:
            # 3. Stream graph execution steps
            async for chunk in agent_graph.astream(initial_state):
                for node_name, updates in chunk.items():
                    logger.debug("Stream received chunk from node: %s", node_name)

                    if "tools_to_execute" in updates and updates["tools_to_execute"]:
                        for t in updates["tools_to_execute"]:
                            tool_event = {
                                "type": "tool_call",
                                "tool": t.get("tool", "unknown"),
                                "status": "running",
                            }
                            yield f"data: {json.dumps(tool_event, ensure_ascii=False)}\n\n"

                    if "tool_results" in updates and updates["tool_results"]:
                        # Record and stream tool outputs
                        for name, res in updates["tool_results"].items():
                            tool_results_dict[name] = res
                            result_event = {
                                "type": "tool_result",
                                "tool": name,
                                "summary": res.get("output_summary", "Thành công"),
                            }
                            yield f"data: {json.dumps(result_event, ensure_ascii=False)}\n\n"

                    if "final_response" in updates and updates["final_response"]:
                        final_response = updates["final_response"]
                        answer_event = {
                            "type": "answer",
                            "content": final_response,
                        }
                        yield f"data: {json.dumps(answer_event, ensure_ascii=False)}\n\n"

        except Exception as ex:
            logger.error("LangGraph execution stream failed: %s", ex)
            error_event = {
                "type": "error",
                "content": "Lỗi hệ thống trong khi suy luận.",
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

        # 4. Construct domain assistant Message
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
            session_id=session.id,
            content=final_response,
            tool_calls=tool_calls,
        )

        # 5. Save assistant's message to persistent history if authenticated
        if user.is_authenticated and history_repo:
            try:
                await history_repo.insert(assistant_msg)
            except Exception as ex:
                logger.error("Failed to insert assistant message during stream: %s", ex)

        # 6. Auto-summarize if count reaches a multiple of 10
        if user.is_authenticated and session_repo and summarize_use_case:
            try:
                updated_session = await session_repo.get_by_id(session.id)
                if (
                    updated_session
                    and updated_session.message_count > 0
                    and updated_session.message_count % 10 == 0
                ):
                    asyncio.create_task(summarize_use_case.execute(session.id))
            except Exception as ex:
                logger.error("Failed to trigger background summarization: %s", ex)

        # 7. Final done event
        done_event = {
            "type": "done",
            "session_id": str(session.id),
        }
        yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
