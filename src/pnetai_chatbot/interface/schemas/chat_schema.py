"""Pydantic schemas for the chat endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import UUID4, BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for processing a chat message."""

    query: str = Field(
        ...,
        description="The user input query string",
        examples=["Thức ăn nào tốt cho chó Poodle 3 tháng?"],
    )
    session_id: UUID4 | None = Field(
        default=None,
        description="Optional session ID. If not provided, a new session is created.",
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response via Server-Sent Events (SSE)",
    )


class ChatResponse(BaseModel):
    """Response schema for a completed non-streamed chat message."""

    answer: str = Field(..., description="The assistant's generated response")
    session_id: UUID4 = Field(..., description="The session ID of the conversation")
    tool_calls: list[Any] = Field(
        default_factory=list,
        description="Metadata on the tool calls executed during orchestration",
    )
    tokens_used: int | None = Field(
        default=None,
        description="Token usage statistics if available",
    )
    model: str | None = Field(
        default=None,
        description="Model name utilized for response generation",
    )
