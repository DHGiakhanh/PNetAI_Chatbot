from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.petbot.domain.value_objects.session_id import SessionId
    from src.petbot.domain.entities.message import Message


class IHistoryRepository(ABC):
    """Repository port for session message history."""

    @abstractmethod
    async def append_message(self, message: "Message") -> None:
        ...

    @abstractmethod
    async def get_history(self, session_id: "SessionId", limit: int = 100) -> List["Message"]:
        ...


__all__ = ["IHistoryRepository"]
