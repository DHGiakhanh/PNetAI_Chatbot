"""Tool type enumeration."""

from enum import StrEnum


class ToolType(StrEnum):
    """Available agent tools."""

    TAVILY = "tavily"
    VECTOR = "vector"
    MONGO = "mongo"
    LLM = "llm"
