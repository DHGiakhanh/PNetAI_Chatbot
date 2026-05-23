"""Session repository port interface."""

from abc import ABC, abstractmethod

from pnetai_chatbot.domain.entities.session import ChatSession
from pnetai_chatbot.domain.value_objects.session_id import SessionId


class ISessionRepository(ABC):
    """Port interface for chat session persistence.

    Implementations:
        - SessionRepository (MongoDB)
    """

    @abstractmethod
    async def create(self, session: ChatSession) -> ChatSession:
        """Persist a new chat session.

        Args:
            session: The session entity to persist.

        Returns:
            The persisted session.
        """
        ...

    @abstractmethod
    async def get_by_id(self, session_id: SessionId) -> ChatSession | None:
        """Retrieve a session by its ID.

        Args:
            session_id: The session identifier.

        Returns:
            The session if found, None otherwise.
        """
        ...

    @abstractmethod
    async def update_summary(self, session_id: SessionId, summary: str) -> None:
        """Update the summary for a session.

        Args:
            session_id: The session identifier.
            summary: The new summary text.
        """
        ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[ChatSession]:
        """List all sessions belonging to a user.

        Args:
            user_id: The user identifier.

        Returns:
            List of chat sessions.
        """
        ...

    @abstractmethod
    async def delete(self, session_id: SessionId) -> None:
        """Delete a session and all its messages.

        Args:
            session_id: The session identifier.
        """
        ...
