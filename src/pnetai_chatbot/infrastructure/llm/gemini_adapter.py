"""Google Gemini LLM adapter."""

from __future__ import annotations

import logging
from typing import Any

from google import genai

from pnetai_chatbot.application.ports.llm_port import LLMResponse
from pnetai_chatbot.infrastructure.llm.base_adapter import BaseLLMAdapter, llm_retry
from pnetai_chatbot.infrastructure.llm.llm_factory import register

logger = logging.getLogger(__name__)


@register("gemini")
class GeminiAdapter(BaseLLMAdapter):
    """LLM adapter for Google Gemini models."""

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, **kwargs)
        self._client = genai.Client(api_key=api_key)
        logger.info("GeminiAdapter initialized: model=%s", model)

    def _convert_messages(self, messages: list[dict[str, str]]) -> list[dict[str, Any]]:
        converted = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                converted.append(
                    {
                        "role": "user",
                        "parts": [{"text": f"[SYSTEM]\n{msg['content']}"}],
                    }
                )
                converted.append(
                    {
                        "role": "model",
                        "parts": [{"text": "Understood."}],
                    }
                )
            elif role == "assistant":
                converted.append(
                    {
                        "role": "model",
                        "parts": [{"text": msg["content"]}],
                    }
                )
            else:
                converted.append(
                    {
                        "role": "user",
                        "parts": [{"text": msg["content"]}],
                    }
                )
        return converted

    @llm_retry
    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        config = genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if tools:
            config.tools = tools

        converted = self._convert_messages(messages)

        response = self._client.models.generate_content(
            model=self._model,
            contents=converted,
            config=config,
        )

        tool_calls: list[dict[str, Any]] = []
        text_parts = []

        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text:
                        text_parts.append(part.text)
                    if part.function_call:
                        tool_calls.append(
                            {
                                "id": part.function_call.id or "",
                                "name": part.function_call.name,
                                "arguments": part.function_call.args or {},
                            }
                        )

        finish_reason = "tool_calls" if tool_calls else "stop"

        return LLMResponse(
            text="\n".join(text_parts),
            model=self._model,
            tokens_used=(
                response.usage_metadata.total_token_count
                if response.usage_metadata
                else 0
            ),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )

    async def embed(self, text: str) -> list[float]:
        response = self._client.models.embed_content(
            model="text-embedding-004",
            contents=[text],
        )
        if response.embeddings:
            return list(response.embeddings[0].values)
        raise RuntimeError("Gemini embedding returned empty result")
