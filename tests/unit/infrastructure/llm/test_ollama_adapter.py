"""Unit tests for OllamaAdapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pnetai_chatbot.infrastructure.llm.ollama_adapter import OllamaAdapter


@pytest.mark.asyncio
async def test_ollama_adapter_init() -> None:
    """Test that OllamaAdapter initializes correctly."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.ollama_adapter.ollama.AsyncClient"
    ) as mock_client_cls:
        adapter = OllamaAdapter(model="llama3", host="http://localhost:11434")
        assert adapter.model_name == "llama3"
        mock_client_cls.assert_called_once_with(host="http://localhost:11434")


@pytest.mark.asyncio
async def test_ollama_adapter_chat_success() -> None:
    """Test standard chat completion with Ollama adapter."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.ollama_adapter.ollama.AsyncClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Setup mock ollama response
        mock_response = MagicMock()
        mock_response.message.content = "Hello from Ollama"
        mock_response.message.tool_calls = None
        mock_response.model = "llama3"
        mock_response.eval_count = 50
        mock_response.prompt_eval_count = 20

        mock_client.chat = AsyncMock(return_value=mock_response)

        adapter = OllamaAdapter(model="llama3", host="http://localhost:11434")
        messages = [{"role": "user", "content": "Hello"}]

        response = await adapter.chat(
            messages=messages, temperature=0.5, max_tokens=100
        )

        assert response.text == "Hello from Ollama"
        assert response.model == "llama3"
        assert response.tokens_used == 70
        assert len(response.tool_calls) == 0
        assert response.finish_reason == "stop"

        mock_client.chat.assert_called_once_with(
            model="llama3",
            messages=messages,
            options={"temperature": 0.5, "num_predict": 100},
        )


@pytest.mark.asyncio
async def test_ollama_adapter_chat_with_tool_calls() -> None:
    """Test chat execution returning tool calls with Ollama."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.ollama_adapter.ollama.AsyncClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Setup mock tool calls
        mock_tc = MagicMock()
        mock_tc.id = "call_ollama"
        mock_tc.function.name = "web_search"
        mock_tc.function.arguments = {"query": "cats"}

        mock_response = MagicMock()
        mock_response.message.content = None
        mock_response.message.tool_calls = [mock_tc]
        mock_response.model = "llama3"
        mock_response.eval_count = 0
        mock_response.prompt_eval_count = 30

        mock_client.chat = AsyncMock(return_value=mock_response)

        adapter = OllamaAdapter(model="llama3")
        response = await adapter.chat(
            messages=[{"role": "user", "content": "Search for cats"}]
        )

        assert response.text == ""
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0] == {
            "id": "call_ollama",
            "name": "web_search",
            "arguments": {"query": "cats"},
        }


@pytest.mark.asyncio
async def test_ollama_adapter_embed_not_implemented() -> None:
    """Test that embed() raises NotImplementedError."""
    with patch("pnetai_chatbot.infrastructure.llm.ollama_adapter.ollama.AsyncClient"):
        adapter = OllamaAdapter(model="llama3")
        with pytest.raises(
            NotImplementedError, match="OllamaAdapter does not support embeddings"
        ):
            await adapter.embed("test text")
