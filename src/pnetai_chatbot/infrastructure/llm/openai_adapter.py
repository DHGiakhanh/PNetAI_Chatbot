"""OpenAI LLM adapter."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

from pnetai_chatbot.application.ports.llm_port import LLMResponse
from pnetai_chatbot.infrastructure.llm.base_adapter import BaseLLMAdapter, llm_retry
from pnetai_chatbot.infrastructure.llm.llm_factory import register

logger = logging.getLogger(__name__)


@register("openai")
class OpenAIAdapter(BaseLLMAdapter):
    """LLM adapter for OpenAI models (GPT-4o, GPT-4o-mini, etc.)."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str = "",
        embedding_model: str = "text-embedding-ada-002",
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, **kwargs)
        self._client = AsyncOpenAI(api_key=api_key)
        self._embedding_model = embedding_model
        logger.info("OpenAIAdapter initialized: model=%s", model)

    @llm_retry
    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            kwargs["tools"] = tools

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls: list[dict[str, Any]] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                )

        finish_reason = choice.finish_reason or "stop"

        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )

    @llm_retry
    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model=self._embedding_model,
            input=text,
        )
        return response.data[0].embedding
