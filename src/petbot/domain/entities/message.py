from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Any
import uuid

from src.petbot.domain.value_objects.session_id import SessionId
from src.petbot.domain.enums.role import MessageRole
from src.petbot.domain.entities.tool_result import ToolCallResult


@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: SessionId
    role: MessageRole
    content: str
    tool_calls: Optional[List[ToolCallResult]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tokens_used: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": str(self.session_id),
            "role": self.role.value,
            "content": self.content,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls] if self.tool_calls else None,
            "timestamp": self.timestamp.isoformat(),
            "tokens_used": self.tokens_used,
        }


__all__ = ["Message"]
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    id: str
    session_id: str
    role: str
    content: str
    timestamp: datetime
