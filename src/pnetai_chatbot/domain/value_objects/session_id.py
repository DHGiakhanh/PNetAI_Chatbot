"""SessionId value object."""

from uuid import UUID


class SessionId:
    """Value object representing a chat session identifier."""

    def __init__(self, value: UUID | str | None = None) -> None:
        if value is None:
            self._value = UUID(int=0)  # ephemeral
        elif isinstance(value, str):
            self._value = UUID(value)
        else:
            self._value = value

    @property
    def value(self) -> UUID:
        """Return the underlying UUID."""
        return self._value

    @property
    def is_ephemeral(self) -> bool:
        """Check if this is an ephemeral (guest) session."""
        return self._value.int == 0

    @classmethod
    def ephemeral(cls) -> "SessionId":
        """Create an ephemeral session ID."""
        return cls()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SessionId):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"SessionId({self._value!r})"
