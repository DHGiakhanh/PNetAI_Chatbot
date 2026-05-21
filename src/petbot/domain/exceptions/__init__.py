"""Domain exceptions package."""

from .session import SessionNotFoundError, InvalidSessionError
from .tool import ToolExecutionError

__all__ = ["SessionNotFoundError", "InvalidSessionError", "ToolExecutionError"]
# src/petbot/domain/exceptions package
