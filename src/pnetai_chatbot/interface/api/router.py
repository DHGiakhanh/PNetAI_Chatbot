"""Primary API Router aggregating all versions under the /api prefix."""

from __future__ import annotations

from fastapi import APIRouter

from pnetai_chatbot.interface.api.v1.router import router as v1_router

router = APIRouter()

router.include_router(v1_router, prefix="/v1")
# Support direct /api/chat path mappings for website upstream compatibility
router.include_router(v1_router)
