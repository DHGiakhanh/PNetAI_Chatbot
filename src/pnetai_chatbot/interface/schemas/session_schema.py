"""Pydantic schemas for the session endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import UUID4, BaseModel, Field


class SessionResponse(BaseModel):
    """Response schema for a single chat session overview."""

    id: UUID4 = Field(..., description="Unique session ID")
    created_at: datetime = Field(..., description="Session creation timestamp")
    message_count: int = Field(..., description="Number of messages in the session")
    summary: str | None = Field(
        default=None,
        description="Auto-generated Vietnamese summary of the session history",
    )
    updated_at: datetime = Field(..., description="Last active session timestamp")


class SessionListResponse(BaseModel):
    """Response schema containing a list of chat sessions."""

    sessions: list[SessionResponse] = Field(
        ...,
        description="Chronological list of sessions belonging to the authenticated user",
    )


class MessageItemSchema(BaseModel):
    """Individual message record item inside session history."""

    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Text content of the message")
    timestamp: datetime = Field(..., description="When the message was recorded")
    tool_calls: list[Any] = Field(
        default_factory=list,
        description="Detail profiles on any external systems queried",
    )


class HistoryResponse(BaseModel):
    """Response schema returned when requesting a session's history log."""

    session_id: UUID4 = Field(..., description="Target session UUID")
    messages: list[MessageItemSchema] = Field(
        ...,
        description="Chronological logs of messages in the thread",
    )
    summary: str | None = Field(
        default=None,
        description="The latest session conversation summary context",
    )
