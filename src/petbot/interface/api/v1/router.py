from fastapi import FastAPI
import logging

from src.petbot.interface.api.v1.endpoints.health import router as health_router
from src.petbot.interface.api.v1.endpoints.chat import router as chat_router
from src.petbot.interface.api.v1.endpoints.session import router as session_router

from src.petbot.infrastructure.persistence.mongodb.client import connect, close_client

logger = logging.getLogger(__name__)

app = FastAPI(title="PetBot API")

app.include_router(health_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(session_router, prefix="/api/v1")


@app.get("/")
async def root():
	return {"service": "pnetai-chatbot", "status": "ok"}


@app.on_event("startup")
async def _on_startup():
	ok = await connect()
	if not ok:
		logger.warning("MongoDB connection failed during startup")
	else:
		logger.info("Connected to MongoDB")


@app.on_event("shutdown")
def _on_shutdown():
	close_client()
	logger.info("MongoDB client closed on shutdown")
