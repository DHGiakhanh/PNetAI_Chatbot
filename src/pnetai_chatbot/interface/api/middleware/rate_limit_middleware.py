"""Rate Limiting middleware utilizing a thread-safe Token Bucket algorithm."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from pnetai_chatbot.infrastructure.config.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token Bucket rate limiting middleware protecting endpoints from abuse.

    Limits are applied differently based on Guest vs Member roles:
    - Guests: rate_limit_guest per minute
    - Members: rate_limit_member per minute
    """

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._settings = get_settings()
        self._lock = Lock()
        # Storage format: client_id -> (tokens, last_update_timestamp)
        self._buckets: dict[str, tuple[float, float]] = defaultdict(lambda: (0.0, 0.0))

    def _get_client_identifier(self, request: Request) -> tuple[str, bool]:
        """Resolve client identifier and authentication status.

        Args:
            request: The incoming FastAPI request.

        Returns:
            A tuple of (client_id_string, is_authenticated_bool).
        """
        user = getattr(request.state, "user", None)
        if user and user.is_authenticated and user.id:
            return f"member:{user.id}", True

        # Fallback to client host IP
        client_ip = request.client.host if request.client else "unknown"
        return f"guest:{client_ip}", False

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Inspect bucket tokens and enforce rate limits.

        Args:
            request: The incoming FastAPI request.
            call_next: Next request processing endpoint.

        Returns:
            The standard HTTP response or a 429 Too Many Requests response.
        """
        # Bypass rate limits for healthcheck endpoint
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        client_id, is_auth = self._get_client_identifier(request)
        limit = (
            self._settings.rate_limit_member
            if is_auth
            else self._settings.rate_limit_guest
        )

        current_time = time.time()
        with self._lock:
            tokens, last_update = self._buckets[client_id]

            if last_update == 0.0:
                # First request from this client, initialize full bucket
                tokens = float(limit)
            else:
                # Refill bucket based on elapsed time (fill rate per second = limit / 60)
                elapsed = current_time - last_update
                refill_rate = limit / 60.0
                tokens = min(float(limit), tokens + (elapsed * refill_rate))

            if tokens >= 1.0:
                # Allow request and consume one token
                tokens -= 1.0
                self._buckets[client_id] = (tokens, current_time)
                remaining_tokens = int(tokens)
            else:
                # Rate limit exceeded
                self._buckets[client_id] = (tokens, current_time)
                retry_after = int(60.0 / (limit / 60.0)) if limit > 0 else 60
                response = JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Tần suất yêu cầu quá nhanh. Vui lòng thử lại sau."
                    },
                )
                response.headers["Retry-After"] = str(retry_after)
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = "0"
                return response

        # Proceed to next handler
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining_tokens)
        return response
