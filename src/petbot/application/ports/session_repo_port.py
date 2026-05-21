from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.petbot.domain.entities.session import ChatSession
    from src.petbot.domain.value_objects.session_id import SessionId


class ISessionRepository(ABC):
    """Repository port for chat sessions."""

    @abstractmethod
    async def create(self, session: "ChatSession") -> "ChatSession":
        ...

    @abstractmethod
    async def get_by_id(self, session_id: "SessionId") -> Optional["ChatSession"]:
        ...

    @abstractmethod
    async def update_summary(self, session_id: "SessionId", summary: str) -> None:
        ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> List["ChatSession"]:
        ...

    @abstractmethod
    async def delete(self, session_id: "SessionId") -> None:
        ...


__all__ = ["ISessionRepository"]
