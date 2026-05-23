"""Message entity."""

from datetime import datetime

from pydantic import UUID4, BaseModel, Field

from pnetai_chatbot.domain.entities.tool_result import ToolCallResult
from pnetai_chatbot.domain.enums.role import MessageRole


class Message(BaseModel):
    """Represents a single message in a chat session."""

    id: UUID4 = Field(..., description="Unique message identifier")
    session_id: UUID4 = Field(..., description="Session this message belongs to")
    role: MessageRole = Field(..., description="Message sender role")
    content: str = Field(..., description="Message text content")
    tool_calls: list[ToolCallResult] = Field(
        default_factory=list,
        description="Tool calls made for this message (assistant/tool messages)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp",
    )
    tokens_used: int | None = Field(
        default=None,
        description="Number of tokens consumed (if available)",
    )
    model: str | None = Field(
        default=None,
        description="LLM model used (for assistant messages)",
    )

    @classmethod
    def create_user_message(
        cls,
        message_id: UUID4,
        session_id: UUID4,
        content: str,
    ) -> "Message":
        """Create a user message."""
        from uuid import uuid4

        return cls(
            id=message_id or uuid4(),
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
        )

    @classmethod
    def create_assistant_message(
        cls,
        session_id: UUID4,
        content: str,
        tool_calls: list[ToolCallResult] | None = None,
        tokens_used: int | None = None,
        model: str | None = None,
    ) -> "Message":
        """Create an assistant message with optional tool call metadata."""
        from uuid import uuid4

        return cls(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            tool_calls=tool_calls or [],
            tokens_used=tokens_used,
            model=model,
        )
