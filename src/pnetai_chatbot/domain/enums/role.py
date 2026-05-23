"""Message role enumeration."""

from enum import StrEnum


class MessageRole(StrEnum):
    """Role of a chat message participant."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
