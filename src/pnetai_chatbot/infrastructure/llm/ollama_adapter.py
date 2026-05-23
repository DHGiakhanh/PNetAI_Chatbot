"""Ollama (local) LLM adapter."""

from __future__ import annotations

import logging
from typing import Any

import ollama

from pnetai_chatbot.application.ports.llm_port import LLMResponse
from pnetai_chatbot.infrastructure.llm.base_adapter import BaseLLMAdapter, llm_retry
from pnetai_chatbot.infrastructure.llm.llm_factory import register

logger = logging.getLogger(__name__)


@register("ollama")
class OllamaAdapter(BaseLLMAdapter):
    """LLM adapter for local Ollama models (chat only)."""

    def __init__(
        self,
        model: str = "llama3.2",
        host: str = "http://localhost:11434",
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, **kwargs)
        self._client = ollama.AsyncClient(host=host)
        logger.info("OllamaAdapter initialized: model=%s host=%s", model, host)

    @llm_retry
    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        response = await self._client.chat(
            model=self._model,
            messages=messages,
            options={"temperature": temperature, "num_predict": max_tokens},
        )

        tool_calls: list[dict[str, Any]] = []
        if response.message.tool_calls:
            for tc in response.message.tool_calls:
                tool_calls.append(
                    {
                        "id": getattr(tc, "id", ""),
                        "name": tc.function.name if hasattr(tc, "function") else "",
                        "arguments": (
                            tc.function.arguments if hasattr(tc, "function") else {}
                        ),
                    }
                )

        return LLMResponse(
            text=response.message.content or "",
            model=response.model or self._model,
            tokens_used=(
                (response.eval_count or 0) + (response.prompt_eval_count or 0)
            ),
            tool_calls=tool_calls,
            finish_reason="stop",
        )

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "OllamaAdapter does not support embeddings. "
            "Use OpenAIAdapter for embedding generation."
        )
