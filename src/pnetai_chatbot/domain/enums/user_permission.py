"""User permission enumeration."""

from enum import StrEnum


class UserPermission(StrEnum):
    """Permission level for chatbot access."""

    GUEST = "guest"
    MEMBER = "member"
    ADMIN = "admin"
