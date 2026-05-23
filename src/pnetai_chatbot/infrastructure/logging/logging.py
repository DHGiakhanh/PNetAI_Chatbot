"""Logging configuration using structlog for structured and standard JSON formats."""

from __future__ import annotations

import logging
import logging.config
import sys
from typing import Any

import structlog

from pnetai_chatbot.infrastructure.config.settings import get_settings


def setup_logging() -> None:
    """Configure structlog dynamically based on app_env settings.

    Integrates Python standard library logging with structlog processors.
    Production environment logs structured JSON to stdout.
    Development environment logs user-friendly colored text.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.is_production:
        # JSON logs for Production
        renderer = structlog.processors.JSONRenderer()
    else:
        # Console output for Development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure standard library logging handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )
    )

    # Reset existing loggers
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress verbose third-party loggers
    for verbose_logger in ["uvicorn.access", "httpx", "motor", "pymongo"]:
        logging.getLogger(verbose_logger).setLevel(logging.WARNING)

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger(__name__)
    logger.info(
        "Structured logging initialized.",
        env=settings.app_env,
        log_level=settings.log_level,
    )
