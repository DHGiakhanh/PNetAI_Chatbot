"""Unit tests for BaseLLMAdapter and retry decorator."""

from __future__ import annotations

import pytest

from pnetai_chatbot.application.ports.llm_port import LLMResponse
from pnetai_chatbot.infrastructure.llm.base_adapter import BaseLLMAdapter, llm_retry


class MockLLMAdapter(BaseLLMAdapter):
    """Concrete implementation of BaseLLMAdapter for testing."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Mock chat implementation."""
        return LLMResponse(text="test response", model=self._model)

    async def embed(self, text: str) -> list[float]:
        """Mock embed implementation."""
        return [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_base_llm_adapter_properties() -> None:
    """Test standard BaseLLMAdapter properties."""
    adapter = MockLLMAdapter(model="test-model", extra_param="extra")
    assert adapter.model_name == "test-model"
    assert adapter._extra_config == {"extra_param": "extra"}


@pytest.mark.asyncio
async def test_llm_retry_success() -> None:
    """Test that llm_retry returns successfully when no exception occurs."""
    call_count = 0

    @llm_retry
    async def successful_func() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = await successful_func()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_llm_retry_on_connection_error() -> None:
    """Test that llm_retry retries on ConnectionError and eventually succeeds."""
    call_count = 0

    @llm_retry
    async def failing_then_succeeding_func() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Connection lost")
        return "success"

    result = await failing_then_succeeding_func()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_llm_retry_on_timeout_error() -> None:
    """Test that llm_retry retries on TimeoutError and eventually succeeds."""
    call_count = 0

    @llm_retry
    async def failing_then_succeeding_func() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TimeoutError("Request timed out")
        return "success"

    result = await failing_then_succeeding_func()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_llm_retry_max_attempts_reached() -> None:
    """Test that llm_retry raises exception after max retry attempts are exhausted."""
    call_count = 0

    @llm_retry
    async def failing_func() -> None:
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Always fail")

    with pytest.raises(ConnectionError, match="Always fail"):
        await failing_func()

    # BaseLLMAdapter has RETRY_ATTEMPTS = 3
    assert call_count == 3


@pytest.mark.asyncio
async def test_llm_retry_no_retry_on_value_error() -> None:
    """Test that llm_retry does not retry on non-retryable exceptions."""
    call_count = 0

    @llm_retry
    async def invalid_args_func() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("Invalid parameters")

    with pytest.raises(ValueError, match="Invalid parameters"):
        await invalid_args_func()

    assert call_count == 1
