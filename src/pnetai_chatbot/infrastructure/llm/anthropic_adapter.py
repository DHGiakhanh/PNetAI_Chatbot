"""Anthropic (Claude) LLM adapter."""

from __future__ import annotations

import logging
from typing import Any

from anthropic import AsyncAnthropic

from pnetai_chatbot.application.ports.llm_port import LLMResponse
from pnetai_chatbot.infrastructure.llm.base_adapter import BaseLLMAdapter, llm_retry
from pnetai_chatbot.infrastructure.llm.llm_factory import register

logger = logging.getLogger(__name__)


@register("anthropic")
class AnthropicAdapter(BaseLLMAdapter):
    """LLM adapter for Anthropic Claude models (Sonnet, Haiku, etc.)."""

    def __init__(
        self,
        model: str = "claude-haiku-4-5",
        api_key: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, **kwargs)
        self._client = AsyncAnthropic(api_key=api_key)
        logger.info("AnthropicAdapter initialized: model=%s", model)

    @llm_retry
    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send a chat completion request to Anthropic."""
        system_prompt = ""
        conversation: list[dict[str, str]] = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt += msg["content"] + "\n"
            else:
                conversation.append(msg)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": conversation,
            "max_tokens": max_tokens,
        }

        if system_prompt.strip():
            kwargs["system"] = system_prompt.strip()

        if tools:
            kwargs["tools"] = tools

        if not tools:
            kwargs["temperature"] = temperature

        response = await self._client.messages.create(**kwargs)

        tool_calls: list[dict[str, Any]] = []
        text_blocks = []
        for block in response.content:
            if block.type == "text":
                text_blocks.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "arguments": block.input,
                    }
                )

        finish_reason = response.stop_reason or "stop"
        if finish_reason == "end_turn":
            finish_reason = "stop"
        elif finish_reason == "tool_use":
            finish_reason = "tool_calls"

        return LLMResponse(
            text="\n".join(text_blocks),
            model=response.model,
            tokens_used=(
                response.usage.input_tokens + response.usage.output_tokens
                if response.usage
                else 0
            ),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )

    async def embed(self, text: str) -> list[float]:
        """Anthropic does not provide a dedicated embeddings API."""
        raise NotImplementedError(
            "Anthropic does not support embeddings. Use OpenAI for embedding."
        )
