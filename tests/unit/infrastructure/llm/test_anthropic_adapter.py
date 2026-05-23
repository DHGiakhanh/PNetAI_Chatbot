"""Unit tests for AnthropicAdapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pnetai_chatbot.infrastructure.llm.anthropic_adapter import AnthropicAdapter


@pytest.mark.asyncio
async def test_anthropic_adapter_init() -> None:
    """Test that AnthropicAdapter initializes correctly."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.anthropic_adapter.AsyncAnthropic"
    ) as mock_anthropic_cls:
        adapter = AnthropicAdapter(model="test-claude", api_key="test-key")
        assert adapter.model_name == "test-claude"
        mock_anthropic_cls.assert_called_once_with(api_key="test-key")


@pytest.mark.asyncio
async def test_anthropic_adapter_chat_success() -> None:
    """Test standard chat completion with a text block."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.anthropic_adapter.AsyncAnthropic"
    ) as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Hello from Claude"

        mock_usage = MagicMock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 100

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_response.stop_reason = "end_turn"
        mock_response.model = "test-claude"
        mock_response.usage = mock_usage

        mock_client.messages.create = AsyncMock(return_value=mock_response)

        adapter = AnthropicAdapter(model="test-claude", api_key="test-key")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ]

        response = await adapter.chat(
            messages=messages, temperature=0.7, max_tokens=100
        )

        assert response.text == "Hello from Claude"
        assert response.model == "test-claude"
        assert response.tokens_used == 150
        assert len(response.tool_calls) == 0
        assert response.finish_reason == "stop"

        mock_client.messages.create.assert_called_once_with(
            model="test-claude",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            system="You are a helpful assistant.",
            temperature=0.7,
        )


@pytest.mark.asyncio
async def test_anthropic_adapter_chat_with_tool_use() -> None:
    """Test chat execution that results in a tool use block."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.anthropic_adapter.AsyncAnthropic"
    ) as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_tool_use_block = MagicMock()
        mock_tool_use_block.type = "tool_use"
        mock_tool_use_block.id = "toolu_123"
        mock_tool_use_block.name = "get_weather"
        mock_tool_use_block.input = {"location": "Hanoi"}

        mock_usage = MagicMock()
        mock_usage.input_tokens = 60
        mock_usage.output_tokens = 40

        mock_response = MagicMock()
        mock_response.content = [mock_tool_use_block]
        mock_response.stop_reason = "tool_use"
        mock_response.model = "test-claude"
        mock_response.usage = mock_usage

        mock_client.messages.create = AsyncMock(return_value=mock_response)

        adapter = AnthropicAdapter(model="test-claude", api_key="test-key")
        tools = [{"name": "get_weather", "description": "Get weather info"}]
        response = await adapter.chat(
            messages=[{"role": "user", "content": "What is the weather in Hanoi?"}],
            tools=tools,
        )

        assert response.text == ""
        assert response.finish_reason == "tool_calls"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0] == {
            "id": "toolu_123",
            "name": "get_weather",
            "arguments": {"location": "Hanoi"},
        }


@pytest.mark.asyncio
async def test_anthropic_adapter_embed_not_implemented() -> None:
    """Test that embed() raises NotImplementedError."""
    with patch("pnetai_chatbot.infrastructure.llm.anthropic_adapter.AsyncAnthropic"):
        adapter = AnthropicAdapter(model="test-claude", api_key="test-key")
        with pytest.raises(
            NotImplementedError, match="Anthropic does not support embeddings"
        ):
            await adapter.embed("test text")
