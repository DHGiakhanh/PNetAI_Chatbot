"""LLM adapter port interface."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Standardized LLM response across all providers."""

    text: str = Field(..., description="The generated text content")
    model: str = Field(..., description="Model used for generation")
    tokens_used: int = Field(default=0, description="Total tokens consumed")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls requested by the LLM",
    )
    finish_reason: str = Field(
        default="stop",
        description="Reason for finishing (stop, length, tool_calls, etc.)",
    )
    provider_raw: dict[str, Any] | None = Field(
        default=None,
        description="Raw provider response for debugging",
    )

    model_config = {"extra": "allow"}


class ILLMAdapter(ABC):
    """Port interface for LLM provider adapters.

    Implementations:
        - OpenAIAdapter
        - AnthropicAdapter
        - GeminiAdapter
        - OllamaAdapter
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send a chat completion request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions.
            temperature: Sampling temperature (0.0 - 1.0).
            max_tokens: Maximum tokens in the response.

        Returns:
            Standardized LLMResponse.
        """
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text.

        Args:
            text: The text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name used by this adapter."""
        ...
