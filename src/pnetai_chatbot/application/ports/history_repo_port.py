"""History repository port interface."""

from abc import ABC, abstractmethod

from pnetai_chatbot.domain.entities.message import Message
from pnetai_chatbot.domain.value_objects.session_id import SessionId


class IHistoryRepository(ABC):
    """Port interface for message history persistence.

    Implementations:
        - HistoryRepository (MongoDB)
    """

    @abstractmethod
    async def insert(self, message: Message) -> Message:
        """Insert a new message into the history.

        Args:
            message: The message entity to persist.

        Returns:
            The persisted message.
        """
        ...

    @abstractmethod
    async def get_by_session(
        self,
        session_id: SessionId,
        limit: int = 50,
        before_timestamp: str | None = None,
    ) -> list[Message]:
        """Retrieve messages for a session.

        Args:
            session_id: The session identifier.
            limit: Maximum number of messages to return.
            before_timestamp: Optional cursor for pagination.

        Returns:
            List of messages ordered by timestamp ascending.
        """
        ...

    @abstractmethod
    async def delete_by_session(self, session_id: SessionId) -> int:
        """Delete all messages for a session.

        Args:
            session_id: The session identifier.

        Returns:
            Number of deleted messages.
        """
        ...
