"""Qdrant client singleton and helpers.

Provides a simple singleton `QdrantClient` wrapper, health checks,
and convenience helpers used by infrastructure tools.
"""
from __future__ import annotations

import logging
from typing import Optional, Any, List

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from src.petbot.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
_client: Optional[QdrantClient] = None


def _base_url() -> str:
    return f"http://{_settings.QDRANT_HOST}:{_settings.QDRANT_PORT}"


def get_client() -> QdrantClient:
    """Return a singleton QdrantClient configured from settings."""
    global _client
    if _client is None:
        try:
            _client = QdrantClient(url=_base_url())
        except TypeError:
            # older qdrant-client versions accept (host, port)
            _client = QdrantClient(host=_settings.QDRANT_HOST, port=_settings.QDRANT_PORT)
    return _client


def ping() -> bool:
    """Quick health check against Qdrant HTTP API.

    Returns True if the client can fetch collections, False otherwise.
    """
    try:
        client = get_client()
        client.get_collections()
        return True
    except Exception as exc:  # pragma: no cover - network error handling
        logger.debug("Qdrant ping failed: %s", exc)
        return False


def ensure_collection(collection_name: str, vector_size: int = 1536, distance: str = "COSINE") -> bool:
    """Ensure a collection exists in Qdrant.

    If the collection does not exist, attempt to create it with the given
    `vector_size` and `distance`. Returns True when created, False if it
    already existed.
    """
    client = get_client()
    try:
        cols = client.get_collections()
        names = [c.name for c in cols.collections]
        if collection_name in names:
            return False
    except Exception:
        # If we cannot list collections, proceed to try creating (will raise on failure)
        pass

    try:
        # Map distance string to enum if possible
        dist_enum = getattr(rest.Distance, distance.upper(), rest.Distance.COSINE)
        vec_params = rest.VectorParams(size=vector_size, distance=dist_enum)
        client.create_collection(collection_name=collection_name, vectors_config=vec_params)
        logger.info("Created Qdrant collection '%s' (size=%d)", collection_name, vector_size)
        return True
    except Exception as exc:  # pragma: no cover - network/op failures
        logger.exception("Failed to create Qdrant collection %s: %s", collection_name, exc)
        raise


def search(collection_name: str, query_vector: List[float], top_k: int = 5, query_filter: Optional[Any] = None, with_payload: bool = True):
    """Wrapper around Qdrant search.

    Returns the raw results from `QdrantClient.search`.
    """
    client = get_client()
    return client.search(collection_name=collection_name, query_vector=query_vector, limit=top_k, query_filter=query_filter, with_payload=with_payload)


__all__ = ["get_client", "ping", "ensure_collection", "search"]
