from __future__ import annotations

from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class SessionId:
    value: uuid.UUID

    @classmethod
    def new(cls) -> "SessionId":
        return cls(uuid.uuid4())

    @classmethod
    def from_str(cls, value: str) -> "SessionId":
        return cls(uuid.UUID(value))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"SessionId({str(self)})"

    def to_hex(self) -> str:
        return self.value.hex


__all__ = ["SessionId"]
