class SessionNotFoundError(Exception):
    """Raised when a session cannot be found in repositories."""


class InvalidSessionError(Exception):
    """Raised when session data is invalid or inconsistent."""


__all__ = ["SessionNotFoundError", "InvalidSessionError"]
