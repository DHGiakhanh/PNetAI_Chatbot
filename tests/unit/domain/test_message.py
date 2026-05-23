"""Unit tests for the Message domain entity."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.entities.tool_result import ToolCallResult
from pnetai_chatbot.domain.enums.role import MessageRole


def test_create_user_message() -> None:
    """Test standard user message creation via factory method."""
    msg_id = uuid4()
    sess_id = uuid4()
    content = "Hello there!"

    msg = Message.create_user_message(
        message_id=msg_id,
        session_id=sess_id,
        content=content,
    )

    assert msg.id == msg_id
    assert msg.session_id == sess_id
    assert msg.role == MessageRole.USER
    assert msg.content == content
    assert len(msg.tool_calls) == 0
    assert isinstance(msg.timestamp, datetime)


def test_create_assistant_message() -> None:
    """Test standard assistant message creation via factory method."""
    sess_id = uuid4()
    content = "Hi, how can I help you?"
    tool_calls = [
        ToolCallResult(
            tool_name="tavily",
            input_summary="search cats",
            output_summary="found cats info",
            execution_time_ms=150,
            data={"status": "ok"},
            success=True,
        )
    ]
    tokens = 45
    model_name = "gpt-4o-mini"

    msg = Message.create_assistant_message(
        session_id=sess_id,
        content=content,
        tool_calls=tool_calls,
        tokens_used=tokens,
        model=model_name,
    )

    assert msg.id is not None
    assert msg.session_id == sess_id
    assert msg.role == MessageRole.ASSISTANT
    assert msg.content == content
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0].tool_name == "tavily"
    assert msg.tokens_used == tokens
    assert msg.model == model_name
