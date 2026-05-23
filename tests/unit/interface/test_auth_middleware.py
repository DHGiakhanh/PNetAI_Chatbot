"""Unit tests for the AuthMiddleware verifying optional Bearer JWT handling."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from jose import jwt

from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.infrastructure.config.settings import get_settings
from pnetai_chatbot.interface.api.middleware.auth_middleware import AuthMiddleware


@pytest.fixture
def test_app() -> FastAPI:
    """Create a temporary FastAPI app wired with AuthMiddleware for isolation."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/test-auth")
    async def get_auth_state(request: Request) -> dict[str, str | bool | None]:
        """Expose request.state.user attributes to test client."""
        user: User = getattr(request.state, "user", User.guest())
        return {
            "id": user.id,
            "is_authenticated": user.is_authenticated,
        }

    return app


@pytest.mark.asyncio
async def test_auth_middleware_missing_token(test_app: FastAPI) -> None:
    """Test that missing authorization headers default request state to guest."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        response = await ac.get("/test-auth")

    assert response.status_code == 200
    assert response.json() == {
        "id": None,
        "is_authenticated": False,
    }


@pytest.mark.asyncio
async def test_auth_middleware_valid_token(test_app: FastAPI) -> None:
    """Test that a valid Bearer token is parsed and injects Member context."""
    settings = get_settings()
    payload = {
        "sub": "user_12345",
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        response = await ac.get("/test-auth", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": "user_12345",
        "is_authenticated": True,
    }


@pytest.mark.asyncio
async def test_auth_middleware_invalid_format(test_app: FastAPI) -> None:
    """Test that non-Bearer authorization header formats are rejected with 401."""
    headers = {"Authorization": "Basic dGVzdDp0ZXN0"}

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        response = await ac.get("/test-auth", headers=headers)

    assert response.status_code == 401
    assert "Invalid authorization header format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_middleware_expired_token(test_app: FastAPI) -> None:
    """Test that expired credentials trigger a strict 401 Unauthorized block."""
    settings = get_settings()
    payload = {
        "sub": "user_12345",
        "exp": datetime.utcnow() - timedelta(minutes=1),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        response = await ac.get("/test-auth", headers=headers)

    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
