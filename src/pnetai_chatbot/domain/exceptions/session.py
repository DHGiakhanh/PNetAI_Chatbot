"""Session-related domain exceptions."""


class SessionNotFoundException(Exception):
    """Raised when a session is not found."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionOwnershipException(Exception):
    """Raised when a user tries to access another user's session."""

    def __init__(self, session_id: str, user_id: str) -> None:
        self.session_id = session_id
        self.user_id = user_id
        super().__init__(f"Session {session_id} does not belong to user {user_id}")


class InvalidSessionStateException(Exception):
    """Raised when an operation is attempted on an invalid session state."""

    pass
