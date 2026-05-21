from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence, Mapping, Optional


class ILLMAdapter(ABC):
    """Abstract LLM adapter port.

    Implementations should wrap specific LLM provider SDKs and expose a
    consistent async interface used by application use cases.
    """

    @abstractmethod
    async def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        tools: Optional[Sequence[Mapping[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Any:
        """Send chat messages to the LLM and return a provider-specific response."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return embedding vector for `text`."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the underlying model identifier."""


__all__ = ["ILLMAdapter"]
