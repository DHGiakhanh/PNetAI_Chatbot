"""AuthMiddleware for validating optional JWT credentials."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.infrastructure.config.settings import get_settings

if TYPE_CHECKING:
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.responses import Response

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to parse and validate optional Bearer JWT authorization tokens."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Intercept and validate the Authorization header.

        Args:
            request: The incoming ASGI HTTP request.
            call_next: Next request processing step.

        Returns:
            The processed ASGI HTTP response.
        """
        # Bypass auth check for health endpoints
        if request.url.path.endswith("/health"):
            request.state.user = User.guest()
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            request.state.user = User.guest()
            return await call_next(request)

        # Validate Bearer prefix
        if not auth_header.startswith("Bearer "):
            logger.warning("Invalid authorization header format received")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
            )

        token = auth_header[7:]
        settings = get_settings()

        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            # Try to get subject/user_id from JWT payload
            user_id = payload.get("sub") or payload.get("user_id")

            if not user_id:
                logger.warning("JWT missing sub or user_id identity claims")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing identity claims in token"},
                )

            logger.info("Successfully authenticated user: %s", user_id)
            request.state.user = User.authenticated(user_id=str(user_id))

        except JWTError as e:
            logger.warning("JWT validation failed: %s", e)
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid or expired credentials: {e}"},
            )

        return await call_next(request)
