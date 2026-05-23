"""Self-hosted LLM adapter for OpenAI-compatible endpoints.

Supports local / fine-tuned model servers that expose an OpenAI-compatible
chat completion API, such as vLLM, LM Studio, text-generation-webui,
LMDeploy, or any custom FastAPI server following the OpenAI spec.

Usage (in .env):
    RESPONSE_LLM_PROVIDER=selfhosted
    RESPONSE_LLM_MODEL=pet-bot-v1
    SELFHOSTED_BASE_URL=http://localhost:8080/v1
    SELFHOSTED_API_KEY=not-required
    SELFHOSTED_TIMEOUT=60.0
"""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

from pnetai_chatbot.application.ports.llm_port import LLMResponse
from pnetai_chatbot.infrastructure.llm.base_adapter import BaseLLMAdapter, llm_retry
from pnetai_chatbot.infrastructure.llm.llm_factory import register

logger = logging.getLogger(__name__)


@register("selfhosted")
class SelfHostedAdapter(BaseLLMAdapter):
    """LLM adapter for self-hosted OpenAI-compatible model servers.

    This adapter is intended *only* for the final response generation step.
    It does NOT participate in reasoning, intent analysis, or tool-calling —
    the primary reasoning LLM handles those steps instead.

    The adapter uses the official ``openai`` SDK with a custom ``base_url``
    so it works with any server that mirrors the OpenAI chat completion API.
    """

    def __init__(
        self,
        model: str = "finetune-pet-bot",
        base_url: str = "http://localhost:8080/v1",
        api_key: str = "not-required",
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> None:
        """Initialize the SelfHostedAdapter.

        Args:
            model: Model name as registered / served by the self-hosted server.
            base_url: Base URL of the OpenAI-compatible server (e.g. http://localhost:8080/v1).
            api_key: API key for the server. Many local servers accept any non-empty string.
            timeout: HTTP request timeout in seconds (higher than cloud APIs to account
                     for slower local inference).
            **kwargs: Extra keyword arguments forwarded to BaseLLMAdapter.
        """
        super().__init__(model=model, **kwargs)
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )
        logger.info(
            "SelfHostedAdapter initialized: model=%s base_url=%s",
            model,
            base_url,
        )

    @llm_retry
    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send a chat completion request to the self-hosted model server.

        Tool calling is intentionally NOT supported here — this adapter is
        only used for the final "answer synthesis" step which never requires
        structured tool outputs.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Ignored; included only for interface compatibility.
            temperature: Sampling temperature (0.0 – 1.0).
            max_tokens: Maximum tokens in the response.

        Returns:
            Standardized LLMResponse with the generated text.
        """
        if tools:
            logger.warning(
                "SelfHostedAdapter received tool definitions but does not "
                "support tool-calling. Tools will be ignored."
            )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0] if response.choices else None
        text = choice.message.content or "" if choice else ""
        finish_reason = choice.finish_reason or "stop" if choice else "stop"

        return LLMResponse(
            text=text.strip(),
            model=response.model or self._model,
            tokens_used=(
                response.usage.total_tokens if response.usage else 0
            ),
            tool_calls=[],
            finish_reason=finish_reason,
        )

    async def embed(self, text: str) -> list[float]:
        """Not supported — use OpenAIAdapter for embedding generation.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "SelfHostedAdapter does not support embeddings. "
            "Use OpenAIAdapter for embedding generation."
        )
