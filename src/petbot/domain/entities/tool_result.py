from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import uuid


@dataclass
class ToolCallResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    success: bool = True
    output: Any = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


__all__ = ["ToolCallResult"]
