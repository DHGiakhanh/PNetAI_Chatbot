from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from src.petbot.domain.value_objects.session_id import SessionId


@dataclass
class ChatSession:
    id: SessionId = field(default_factory=SessionId.new)
    user_id: Optional[str] = None
    is_authenticated: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()

    def increment(self, by: int = 1) -> None:
        self.message_count += by
        self.touch()

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "is_authenticated": self.is_authenticated,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
            "summary": self.summary,
            "metadata": self.metadata,
        }


__all__ = ["ChatSession"]
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChatSession:
    id: str
    user_id: str | None
    is_authenticated: bool
    created_at: datetime
    updated_at: datetime
