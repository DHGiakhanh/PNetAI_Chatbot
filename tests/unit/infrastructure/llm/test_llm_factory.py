"""Unit tests for LLMFactory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pnetai_chatbot.infrastructure.config.settings import Settings
from pnetai_chatbot.infrastructure.llm.base_adapter import BaseLLMAdapter
from pnetai_chatbot.infrastructure.llm.llm_factory import LLMFactory


def test_llm_factory_list_providers() -> None:
    """Test listing all registered LLM providers."""
    providers = LLMFactory.list_providers()
    assert "openai" in providers
    assert "anthropic" in providers
    assert "gemini" in providers
    assert "ollama" in providers


def test_llm_factory_create_openai() -> None:
    """Test creating an OpenAIAdapter through LLMFactory."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.openai_adapter.AsyncOpenAI"
    ) as mock_openai_cls:
        adapter = LLMFactory.create(
            provider="openai", model="gpt-4o", api_key="test-key"
        )
        assert isinstance(adapter, BaseLLMAdapter)
        assert adapter.model_name == "gpt-4o"
        mock_openai_cls.assert_called_once_with(api_key="test-key")


def test_llm_factory_create_anthropic() -> None:
    """Test creating an AnthropicAdapter through LLMFactory."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.anthropic_adapter.AsyncAnthropic"
    ) as mock_anthropic_cls:
        adapter = LLMFactory.create(
            provider="anthropic", model="claude-3", api_key="test-key"
        )
        assert isinstance(adapter, BaseLLMAdapter)
        assert adapter.model_name == "claude-3"
        mock_anthropic_cls.assert_called_once_with(api_key="test-key")


def test_llm_factory_create_gemini() -> None:
    """Test creating a GeminiAdapter through LLMFactory."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.gemini_adapter.genai.Client"
    ) as mock_client_cls:
        adapter = LLMFactory.create(
            provider="gemini", model="gemini-flash", api_key="test-key"
        )
        assert isinstance(adapter, BaseLLMAdapter)
        assert adapter.model_name == "gemini-flash"
        mock_client_cls.assert_called_once_with(api_key="test-key")


def test_llm_factory_create_ollama() -> None:
    """Test creating an OllamaAdapter through LLMFactory."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.ollama_adapter.ollama.AsyncClient"
    ) as mock_client_cls:
        adapter = LLMFactory.create(
            provider="ollama", model="llama3", host="http://localhost:11434"
        )
        assert isinstance(adapter, BaseLLMAdapter)
        assert adapter.model_name == "llama3"
        mock_client_cls.assert_called_once_with(host="http://localhost:11434")


def test_llm_factory_create_unknown_provider() -> None:
    """Test that creating an unknown provider raises ValueError."""
    with pytest.raises(ValueError, match="Unknown LLM provider: 'unknown'"):
        LLMFactory.create(provider="unknown")


def test_llm_factory_create_from_settings_openai() -> None:
    """Test creating LLM adapter from settings loaded with OpenAI."""
    # Setup mock Settings
    mock_settings = Settings(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        openai_api_key="settings-openai-key",
    )

    with (
        patch(
            "pnetai_chatbot.infrastructure.config.settings.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "pnetai_chatbot.infrastructure.llm.openai_adapter.AsyncOpenAI"
        ) as mock_openai_cls,
    ):
        adapter = LLMFactory.create_from_settings()
        assert adapter.model_name == "gpt-4o-mini"
        mock_openai_cls.assert_called_once_with(api_key="settings-openai-key")


def test_llm_factory_create_from_settings_anthropic() -> None:
    """Test creating LLM adapter from settings loaded with Anthropic."""
    mock_settings = Settings(
        llm_provider="anthropic",
        llm_model="claude-haiku",
        anthropic_api_key="settings-anthropic-key",
    )

    with (
        patch(
            "pnetai_chatbot.infrastructure.config.settings.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "pnetai_chatbot.infrastructure.llm.anthropic_adapter.AsyncAnthropic"
        ) as mock_anthropic_cls,
    ):
        adapter = LLMFactory.create_from_settings()
        assert adapter.model_name == "claude-haiku"
        mock_anthropic_cls.assert_called_once_with(api_key="settings-anthropic-key")


def test_llm_factory_create_from_settings_gemini() -> None:
    """Test creating LLM adapter from settings loaded with Gemini."""
    mock_settings = Settings(
        llm_provider="gemini",
        llm_model="gemini-pro",
        gemini_api_key="settings-gemini-key",
    )

    with (
        patch(
            "pnetai_chatbot.infrastructure.config.settings.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "pnetai_chatbot.infrastructure.llm.gemini_adapter.genai.Client"
        ) as mock_client_cls,
    ):
        adapter = LLMFactory.create_from_settings()
        assert adapter.model_name == "gemini-pro"
        mock_client_cls.assert_called_once_with(api_key="settings-gemini-key")


def test_llm_factory_create_from_settings_ollama() -> None:
    """Test creating LLM adapter from settings loaded with Ollama."""
    mock_settings = Settings(
        llm_provider="ollama",
        llm_model="llama3.2",
        ollama_host="http://local-ollama:11434",
    )

    with (
        patch(
            "pnetai_chatbot.infrastructure.config.settings.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "pnetai_chatbot.infrastructure.llm.ollama_adapter.ollama.AsyncClient"
        ) as mock_client_cls,
    ):
        adapter = LLMFactory.create_from_settings()
        assert adapter.model_name == "llama3.2"
        mock_client_cls.assert_called_once_with(host="http://local-ollama:11434")
