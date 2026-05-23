"""User entity."""

from pydantic import BaseModel, Field

from pnetai_chatbot.domain.enums.user_permission import UserPermission


class User(BaseModel):
    """Represents a chatbot user (guest or authenticated)."""

    id: str | None = Field(
        default=None,
        description="User identifier (None for guests)",
    )
    is_authenticated: bool = Field(
        default=False,
        description="Whether the user has a valid JWT",
    )

    @property
    def permission(self) -> UserPermission:
        """Derive permission level from authentication state."""
        if not self.is_authenticated:
            return UserPermission.GUEST
        return UserPermission.MEMBER

    @classmethod
    def guest(cls) -> "User":
        """Create a guest user."""
        return cls(is_authenticated=False)

    @classmethod
    def authenticated(cls, user_id: str) -> "User":
        """Create an authenticated user."""
        return cls(id=user_id, is_authenticated=True)
