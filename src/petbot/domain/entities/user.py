from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from src.petbot.domain.enums.user_permission import UserPermission


@dataclass
class User:
    id: str
    name: Optional[str] = None
    is_authenticated: bool = False
    permissions: List[UserPermission] = field(default_factory=lambda: [UserPermission.GUEST])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "is_authenticated": self.is_authenticated,
            "permissions": [p.value for p in self.permissions],
        }


__all__ = ["User"]
from dataclasses import dataclass

@dataclass
class User:
    id: str
    is_authenticated: bool = False
