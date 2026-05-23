"""Shared fixtures for integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

from pnetai_chatbot.infrastructure.persistence.mongodb.client import (
    get_chat_client,
    get_website_client,
)


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Provide a clean isolated test database instance, dropped before and after use.

    Clears caching to avoid closed loop issues with Motor singletons.
    """
    # Clear client caches so a fresh client is created for this test's event loop
    get_chat_client.cache_clear()
    get_website_client.cache_clear()

    chat_client = get_chat_client()
    db_name = "pnetai_chat_test"
    db = chat_client.client[db_name]

    # Clean up any leftover data
    await chat_client.client.drop_database(db_name)

    yield db

    # Clean up after the test runs
    await chat_client.client.drop_database(db_name)

    # Explicitly close and clear to clean up resources
    await chat_client.close()
    get_chat_client.cache_clear()
    get_website_client.cache_clear()
