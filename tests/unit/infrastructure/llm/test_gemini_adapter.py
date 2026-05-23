"""Unit tests for GeminiAdapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pnetai_chatbot.infrastructure.llm.gemini_adapter import GeminiAdapter


@pytest.mark.asyncio
async def test_gemini_adapter_init() -> None:
    """Test that GeminiAdapter initializes correctly."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.gemini_adapter.genai.Client"
    ) as mock_client_cls:
        adapter = GeminiAdapter(model="gemini-1.5-flash", api_key="test-key")
        assert adapter.model_name == "gemini-1.5-flash"
        mock_client_cls.assert_called_once_with(api_key="test-key")


def test_gemini_adapter_convert_messages() -> None:
    """Test standard messages format conversion for Gemini API."""
    with patch("pnetai_chatbot.infrastructure.llm.gemini_adapter.genai.Client"):
        adapter = GeminiAdapter(model="gemini-1.5-flash", api_key="test-key")
        messages = [
            {"role": "system", "content": "Instruction"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        converted = adapter._convert_messages(messages)

        assert len(converted) == 4
        assert converted[0] == {
            "role": "user",
            "parts": [{"text": "[SYSTEM]\nInstruction"}],
        }
        assert converted[1] == {
            "role": "model",
            "parts": [{"text": "Understood."}],
        }
        assert converted[2] == {
            "role": "user",
            "parts": [{"text": "Hello"}],
        }
        assert converted[3] == {
            "role": "model",
            "parts": [{"text": "Hi there"}],
        }


@pytest.mark.asyncio
async def test_gemini_adapter_chat_success() -> None:
    """Test standard chat completion with Gemini adapter."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.gemini_adapter.genai.Client"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Setup mock candidate content parts
        mock_part = MagicMock()
        mock_part.text = "Hello from Gemini"
        mock_part.function_call = None

        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]

        mock_usage = MagicMock()
        mock_usage.total_token_count = 120

        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = mock_usage

        mock_client.models.generate_content.return_value = mock_response

        adapter = GeminiAdapter(model="gemini-1.5-flash", api_key="test-key")
        messages = [{"role": "user", "content": "Hello"}]

        response = await adapter.chat(
            messages=messages, temperature=0.7, max_tokens=100
        )

        assert response.text == "Hello from Gemini"
        assert response.model == "gemini-1.5-flash"
        assert response.tokens_used == 120
        assert len(response.tool_calls) == 0
        assert response.finish_reason == "stop"

        mock_client.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_adapter_chat_with_tool_calls() -> None:
    """Test chat execution returning tool calls."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.gemini_adapter.genai.Client"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Setup mock function call part
        mock_part = MagicMock()
        mock_part.text = None
        mock_part.function_call.id = "call_gemini"
        mock_part.function_call.name = "web_search"
        mock_part.function_call.args = {"query": "Vietnam pets"}

        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]

        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = None

        mock_client.models.generate_content.return_value = mock_response

        adapter = GeminiAdapter(model="gemini-1.5-flash", api_key="test-key")
        tools = [{"name": "web_search"}]
        response = await adapter.chat(
            messages=[{"role": "user", "content": "Search for Vietnam pets"}],
            tools=tools,
        )

        assert response.text == ""
        assert response.finish_reason == "tool_calls"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0] == {
            "id": "call_gemini",
            "name": "web_search",
            "arguments": {"query": "Vietnam pets"},
        }


@pytest.mark.asyncio
async def test_gemini_adapter_embed() -> None:
    """Test embedding generation with Gemini Adapter."""
    with patch(
        "pnetai_chatbot.infrastructure.llm.gemini_adapter.genai.Client"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_emb = MagicMock()
        mock_emb.values = [0.1, 0.2, 0.3]

        mock_response = MagicMock()
        mock_response.embeddings = [mock_emb]

        mock_client.models.embed_content.return_value = mock_response

        adapter = GeminiAdapter(model="gemini-1.5-flash", api_key="test-key")
        vector = await adapter.embed("test text")

        assert vector == [0.1, 0.2, 0.3]
        mock_client.models.embed_content.assert_called_once_with(
            model="text-embedding-004",
            contents=["test text"],
        )
