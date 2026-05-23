"""Health diagnostic API endpoint."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Diagnostic"])
async def health_check() -> dict[str, str]:
    """Expose application health and diagnostic connection status.

    Returns:
        A dictionary containing the status description of the API.
    """
    return {"status": "healthy"}
