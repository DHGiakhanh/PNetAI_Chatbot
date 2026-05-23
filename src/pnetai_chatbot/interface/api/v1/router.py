"""V1 Router combining health, session, and chat endpoints under /v1."""

from __future__ import annotations

from fastapi import APIRouter

from pnetai_chatbot.interface.api.v1.endpoints import chat, health, session

router = APIRouter()

router.include_router(health.router)
router.include_router(chat.router)
router.include_router(session.router)
