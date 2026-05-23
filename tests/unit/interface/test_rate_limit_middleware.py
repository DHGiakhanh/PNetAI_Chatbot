"""Unit tests for the RateLimitMiddleware."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from httpx import ASGITransport, AsyncClient
from starlette.middleware.base import BaseHTTPMiddleware

from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.infrastructure.config.settings import get_settings
from pnetai_chatbot.interface.api.middleware import RateLimitMiddleware


class DummyGuestAuthMiddleware(BaseHTTPMiddleware):
    """Dummy middleware to inject guest user context."""

    async def dispatch(self, request: Request, call_next):
        request.state.user = User.guest()
        return await call_next(request)


class DummyMemberAuthMiddleware(BaseHTTPMiddleware):
    """Dummy middleware to inject member user context."""

    async def dispatch(self, request: Request, call_next):
        request.state.user = User.authenticated("member_123")
        return await call_next(request)


@pytest.mark.asyncio
async def test_rate_limiting_guest() -> None:
    """Test that RateLimitMiddleware blocks guest requests exceeding the limit."""
    settings = get_settings()
    original_guest_limit = settings.rate_limit_guest

    # Set guest limit to 2 per minute for testing
    settings.rate_limit_guest = 2

    try:
        app = FastAPI()

        # Add RateLimitMiddleware first (inner), then Guest auth (outer)
        # So on request: Guest auth runs -> RateLimit runs
        app.add_middleware(RateLimitMiddleware)
        app.add_middleware(DummyGuestAuthMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return PlainTextResponse("OK")

        @app.get("/api/v1/health")
        async def health_endpoint():
            return PlainTextResponse("OK")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. First request -> OK
            r1 = await client.get("/test")
            assert r1.status_code == 200
            assert r1.headers["X-RateLimit-Limit"] == "2"
            assert r1.headers["X-RateLimit-Remaining"] == "1"

            # 2. Second request -> OK
            r2 = await client.get("/test")
            assert r2.status_code == 200
            assert r2.headers["X-RateLimit-Limit"] == "2"
            assert r2.headers["X-RateLimit-Remaining"] == "0"

            # 3. Third request -> Blocked (429)
            r3 = await client.get("/test")
            assert r3.status_code == 429
            assert "Tần suất yêu cầu quá nhanh" in r3.json()["detail"]
            assert r3.headers["Retry-After"] is not None

            # 4. Healthcheck request -> Bypassed (200)
            r4 = await client.get("/api/v1/health")
            assert r4.status_code == 200

    finally:
        # Restore settings
        settings.rate_limit_guest = original_guest_limit


@pytest.mark.asyncio
async def test_rate_limiting_member() -> None:
    """Test that RateLimitMiddleware uses member limits for authenticated users."""
    settings = get_settings()
    original_member_limit = settings.rate_limit_member

    # Set member limit to 1 per minute for testing
    settings.rate_limit_member = 1

    try:
        app = FastAPI()

        # Add RateLimitMiddleware first (inner), then Member auth (outer)
        # So on request: Member auth runs -> RateLimit runs
        app.add_middleware(RateLimitMiddleware)
        app.add_middleware(DummyMemberAuthMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return PlainTextResponse("OK")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. First request -> OK
            r1 = await client.get("/test")
            assert r1.status_code == 200
            assert r1.headers["X-RateLimit-Limit"] == "1"
            assert r1.headers["X-RateLimit-Remaining"] == "0"

            # 2. Second request -> Blocked (429)
            r2 = await client.get("/test")
            assert r2.status_code == 429

    finally:
        # Restore settings
        settings.rate_limit_member = original_member_limit
