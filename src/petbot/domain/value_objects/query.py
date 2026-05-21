from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from src.petbot.domain.value_objects.session_id import SessionId

if TYPE_CHECKING:
    from src.petbot.domain.entities.user import User


@dataclass
class UserQuery:
    raw_text: str
    session_id: SessionId
    user: Optional["User"] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "session_id": str(self.session_id),
            "user_id": self.user.id if self.user else None,
            "timestamp": self.timestamp.isoformat(),
        }


__all__ = ["UserQuery"]
