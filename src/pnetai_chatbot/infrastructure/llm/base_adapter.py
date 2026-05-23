"""Base LLM adapter with retry logic.

Provides a shared retry decorator and abstract base for all LLM adapters.
"""

from __future__ import annotations

import logging
from typing import Any

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter

logger = logging.getLogger(__name__)

RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT = 1  # seconds
RETRY_MAX_WAIT = 10  # seconds


def llm_retry(func):
    """Retry decorator for LLM API calls with exponential backoff.

    3 attempts, exponential backoff: 1s → 2s → 4s.
    Retries on: ConnectionError, TimeoutError, and HTTP 429/5xx.
    """
    return retry(
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_exponential(
            multiplier=1,
            min=RETRY_MIN_WAIT,
            max=RETRY_MAX_WAIT,
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )(func)


class BaseLLMAdapter(ILLMAdapter):
    """Abstract base for all LLM adapters with shared retry logic.

    Subclasses must implement:
        - chat()
        - embed()
        - model_name (property)
    """

    def __init__(self, model: str, **kwargs: Any) -> None:
        self._model = model
        self._extra_config = kwargs

    @property
    def model_name(self) -> str:
        """Return the model name used by this adapter."""
        return self._model
