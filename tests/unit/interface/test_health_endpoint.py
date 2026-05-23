"""Unit tests for the health diagnostic endpoint."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from pnetai_chatbot.interface.api.app import create_app


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Test that the health endpoint returns a successful healthy status."""
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
