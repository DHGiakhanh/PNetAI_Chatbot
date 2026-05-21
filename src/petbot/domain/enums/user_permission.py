from enum import Enum


class UserPermission(str, Enum):
    GUEST = "guest"
    MEMBER = "member"
    ADMIN = "admin"


__all__ = ["UserPermission"]
