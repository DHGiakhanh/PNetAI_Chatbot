import logging
import time
import asyncio
from typing import Optional, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.petbot.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()

_client: Optional[AsyncIOMotorClient] = None


def _client_kwargs() -> dict[str, Any]:
	kw = {
		"serverSelectionTimeoutMS": int(getattr(_settings, "MONGODB_SERVER_SELECTION_TIMEOUT_MS", 5000)),
		"connectTimeoutMS": int(getattr(_settings, "MONGODB_CONNECT_TIMEOUT_MS", 10000)),
	}
	max_pool = getattr(_settings, "MONGODB_MAX_POOL_SIZE", None)
	if max_pool:
		kw["maxPoolSize"] = int(max_pool)
	return kw


def get_client() -> AsyncIOMotorClient:
	"""Return a singleton AsyncIOMotorClient.

	This is a lightweight factory; use `connect()` at application startup to
	validate the connection and fail fast if the server is unreachable.
	"""
	global _client
	if _client is None:
		_client = AsyncIOMotorClient(_settings.MONGODB_CHAT_URI, **_client_kwargs())
	return _client


async def connect(retries: int = 3, backoff: float = 1.0) -> bool:
	"""Try to connect to MongoDB with simple retry/backoff.

	Returns True when ping succeeds, False otherwise.
	"""
	client = get_client()
	for attempt in range(1, retries + 1):
		try:
			await client.admin.command("ping")
			logger.info("MongoDB connection OK (attempt %d)", attempt)
			return True
		except Exception as exc:
			logger.warning("MongoDB ping failed (attempt %d/%d): %s", attempt, retries, exc)
			if attempt < retries:
				await asyncio.sleep(backoff * attempt)
	return False


async def wait_until_available(timeout: int = 30) -> bool:
	"""Wait until MongoDB becomes available or timeout (seconds) is reached."""
	client = get_client()
	start = time.time()
	while time.time() - start < timeout:
		try:
			await client.admin.command("ping")
			return True
		except Exception:
			await asyncio.sleep(0.5)
	return False


def get_database(name: Optional[str] = None) -> AsyncIOMotorDatabase:
	"""Get a Motor database instance.

	If `name` is omitted, attempt to use the default database from the URI,
	otherwise fall back to `petbot_chat`.
	"""
	client = get_client()
	if name:
		return client[name]
	try:
		default_db = client.get_default_database()
		if default_db is not None:
			return default_db
	except Exception:
		pass
	return client["petbot_chat"]


def get_collection(name: str, db_name: Optional[str] = None):
	"""Convenience helper to access a collection by name."""
	db = get_database(db_name)
	return db[name]


def start_session(**kwargs):
	"""Return a client session (use `async with start_session(): ...`)."""
	return get_client().start_session(**kwargs)


async def ping() -> bool:
	"""Backward-compatible ping helper."""
	return await connect(retries=1, backoff=0)


def close_client() -> None:
	"""Close the motor client and reset singleton."""
	global _client
	if _client is not None:
		try:
			_client.close()
			logger.info("MongoDB client closed")
		finally:
			_client = None


__all__ = [
	"get_client",
	"connect",
	"wait_until_available",
	"get_database",
	"get_collection",
	"start_session",
	"ping",
	"close_client",
]
