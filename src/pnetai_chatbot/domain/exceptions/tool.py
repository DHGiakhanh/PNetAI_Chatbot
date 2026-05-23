"""Tool-related domain exceptions."""


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""

    def __init__(self, tool_name: str, reason: str) -> None:
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Tool '{tool_name}' failed: {reason}")


class InvalidToolQueryError(ToolExecutionError):
    """Raised when a generated MongoDB query is invalid."""

    def __init__(self, tool_name: str, reason: str) -> None:
        super().__init__(tool_name, f"Invalid query: {reason}")
