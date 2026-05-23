"""LLM Factory with provider registry.

Config-driven switching via LLM_PROVIDER env variable.
"""

from __future__ import annotations

import logging
from typing import Any

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter

logger = logging.getLogger(__name__)

# Registry: provider_name -> adapter_class
_registry: dict[str, type[ILLMAdapter]] = {}


def register(provider: str) -> Any:
    """Decorator to register an adapter class in the factory."""

    def decorator(cls: type[ILLMAdapter]) -> type[ILLMAdapter]:
        _registry[provider] = cls
        logger.debug("Registered LLM provider: %s -> %s", provider, cls.__name__)
        return cls

    return decorator


class LLMFactory:
    """Factory that creates LLM adapters from configuration."""

    @staticmethod
    def _ensure_registry() -> None:
        """Lazy-load adapters to avoid circular imports."""
        if not _registry:
            # Trigger registration via decorators
            from pnetai_chatbot.infrastructure.llm import (
                anthropic_adapter,  # noqa: F401
                gemini_adapter,  # noqa: F401
                ollama_adapter,  # noqa: F401
                openai_adapter,  # noqa: F401
            )

    @classmethod
    def create(
        cls,
        provider: str,
        model: str | None = None,
        **kwargs: Any,
    ) -> ILLMAdapter:
        """Create an LLM adapter instance.

        Args:
            provider: Provider name (openai, anthropic, gemini, ollama).
            model: Model name (uses default if not specified).
            **kwargs: Additional keyword args passed to the adapter.

        Returns:
            An initialized ILLMAdapter instance.

        Raises:
            ValueError: If the provider is unknown.
        """
        cls._ensure_registry()

        adapter_cls = _registry.get(provider)
        if not adapter_cls:
            available = ", ".join(sorted(_registry.keys()))
            raise ValueError(
                f"Unknown LLM provider: '{provider}'. Available: {available}"
            )

        if model:
            kwargs["model"] = model

        return adapter_cls(**kwargs)

    @classmethod
    def create_from_settings(cls) -> ILLMAdapter:
        """Create the primary LLM adapter from application settings."""
        from pnetai_chatbot.infrastructure.config.settings import get_settings

        settings = get_settings()

        # Map provider to kwargs
        provider_kwargs: dict[str, Any] = {}

        if settings.llm_provider == "openai":
            provider_kwargs["api_key"] = settings.openai_api_key
        elif settings.llm_provider == "anthropic":
            provider_kwargs["api_key"] = settings.anthropic_api_key
        elif settings.llm_provider == "gemini":
            provider_kwargs["api_key"] = settings.gemini_api_key
        elif settings.llm_provider == "ollama":
            provider_kwargs["host"] = settings.ollama_host

        return cls.create(
            provider=settings.llm_provider,
            model=settings.llm_model,
            **provider_kwargs,
        )

    @classmethod
    def list_providers(cls) -> list[str]:
        """Return all registered provider names."""
        cls._ensure_registry()
        return sorted(_registry.keys())
