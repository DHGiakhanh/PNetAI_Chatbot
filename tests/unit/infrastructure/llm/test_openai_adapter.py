"""Unit tests for OpenAIAdapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pnetai_chatbot.infrastructure.llm.openai_adapter import OpenAIAdapter


@pytest.mark.asyncio
async def test_openai_adapter_init() -> None:
    """Test that OpenAIAdapter initializes correctly."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.openai_adapter.AsyncOpenAI"
    ) as mock_openai_cls:
        adapter = OpenAIAdapter(
            model="test-gpt",
            api_key="test-key",
            embedding_model="test-emb",
        )
        assert adapter.model_name == "test-gpt"
        assert adapter._embedding_model == "test-emb"
        mock_openai_cls.assert_called_once_with(api_key="test-key")


@pytest.mark.asyncio
async def test_openai_adapter_chat_success() -> None:
    """Test standard chat execution successfully returning a text response."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.openai_adapter.AsyncOpenAI"
    ) as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Setup mock chat completion response
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello, world!"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 150

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model = "test-gpt"

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        adapter = OpenAIAdapter(model="test-gpt", api_key="test-key")
        messages = [{"role": "user", "content": "Hi"}]
        response = await adapter.chat(
            messages=messages, temperature=0.5, max_tokens=100
        )

        assert response.text == "Hello, world!"
        assert response.model == "test-gpt"
        assert response.tokens_used == 150
        assert len(response.tool_calls) == 0
        assert response.finish_reason == "stop"

        mock_client.chat.completions.create.assert_called_once_with(
            model="test-gpt",
            messages=messages,
            temperature=0.5,
            max_tokens=100,
        )


@pytest.mark.asyncio
async def test_openai_adapter_chat_with_tool_calls() -> None:
    """Test chat execution that requests tool calls."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.openai_adapter.AsyncOpenAI"
    ) as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Setup mock tool calls
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "web_search"
        mock_tool_call.function.arguments = '{"query": "cats"}'

        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.finish_reason = "tool_calls"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 80

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model = "test-gpt"

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        adapter = OpenAIAdapter(model="test-gpt", api_key="test-key")
        tools = [{"type": "function", "function": {"name": "web_search"}}]
        response = await adapter.chat(
            messages=[{"role": "user", "content": "Search for cats"}],
            tools=tools,
        )

        assert response.text == ""
        assert response.finish_reason == "tool_calls"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0] == {
            "id": "call_123",
            "name": "web_search",
            "arguments": '{"query": "cats"}',
        }


@pytest.mark.asyncio
async def test_openai_adapter_embed() -> None:
    """Test embedding generation."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.openai_adapter.AsyncOpenAI"
    ) as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_emb_data = MagicMock()
        mock_emb_data.embedding = [0.1, 0.2, 0.3]

        mock_response = MagicMock()
        mock_response.data = [mock_emb_data]

        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        adapter = OpenAIAdapter(
            model="test-gpt",
            api_key="test-key",
            embedding_model="test-emb",
        )
        vector = await adapter.embed("hello")

        assert vector == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once_with(
            model="test-emb",
            input="hello",
        )
