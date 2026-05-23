"""ToolCallResult entity."""

from typing import Any

from pydantic import BaseModel, Field


class ToolCallResult(BaseModel):
    """Represents the result of a single tool execution."""

    tool_name: str = Field(
        ..., description="Name of the tool (tavily, vector, mongo, llm)"
    )
    input_summary: str = Field(
        default="",
        description="Brief summary of the input",
    )
    output_summary: str = Field(
        default="",
        description="Brief summary of the output",
    )
    execution_time_ms: int = Field(
        default=0,
        description="Execution time in milliseconds",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw tool result data",
    )
    success: bool = Field(default=True, description="Whether the tool call succeeded")
    error_message: str | None = Field(
        default=None,
        description="Error message if the tool call failed",
    )
