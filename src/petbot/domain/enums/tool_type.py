from enum import Enum


class ToolType(str, Enum):
    TAVILY = "tavily"
    VECTOR = "vector"
    MONGO = "mongo"
    LLM = "llm"
    OTHER = "other"


__all__ = ["ToolType"]
