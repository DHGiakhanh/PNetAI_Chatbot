from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


__all__ = ["MessageRole"]
