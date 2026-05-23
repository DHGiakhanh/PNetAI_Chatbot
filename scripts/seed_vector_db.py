#!/usr/bin/env python3
"""Seed Qdrant with Vietnamese pet knowledge base documents.

Usage:
    uv run python scripts/seed_vector_db.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid

from dotenv import load_dotenv
from qdrant_client.http import models as qdrant_models
from openai import AsyncOpenAI

from pnetai_chatbot.infrastructure.config.seed_data import PET_KNOWLEDGE_DOCUMENTS

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

VECTOR_DIM = 1536
BATCH_SIZE = 10


async def embed_texts(
    client: AsyncOpenAI, texts: list[str], model: str = "text-embedding-ada-002"
) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    response = await client.embeddings.create(input=texts, model=model)
    embeddings = sorted(response.data, key=lambda x: x.index)
    return [e.embedding for e in embeddings]


async def seed_qdrant(
    qdrant_host: str,
    qdrant_port: int,
    collection_name: str,
    openai_api_key: str,
) -> None:
    """Embed and upsert all documents to Qdrant."""
    from qdrant_client import AsyncQdrantClient

    openai_client = AsyncOpenAI(api_key=openai_api_key)
    qdrant_client = AsyncQdrantClient(host=qdrant_host, port=qdrant_port)

    try:
        collections = await qdrant_client.get_collections()
        names = [c.name for c in collections.collections]

        if collection_name not in names:
            await qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=VECTOR_DIM,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
            logger.info("Created collection '%s'", collection_name)
        else:
            logger.info("Collection '%s' already exists", collection_name)

        docs = PET_KNOWLEDGE_DOCUMENTS
        total = len(docs)

        for i in range(0, total, BATCH_SIZE):
            batch = docs[i : i + BATCH_SIZE]
            texts = [f"{d['title']}\n{d['content']}" for d in batch]
            embeddings = await embed_texts(openai_client, texts)

            points = []
            for doc, embedding in zip(batch, embeddings):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc["id"]))
                points.append(
                    qdrant_models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "title": doc["title"],
                            "content": doc["content"],
                            "category": doc["category"],
                            "species": doc["species"],
                            "tags": doc["tags"],
                        },
                    )
                )

            await qdrant_client.upsert(
                collection_name=collection_name,
                points=points,
            )
            logger.info(
                "Upserted batch %d/%d (%d documents)",
                i // BATCH_SIZE + 1,
                (total + BATCH_SIZE - 1) // BATCH_SIZE,
                len(points),
            )

        logger.info("Seed complete: %d documents in '%s'", total, collection_name)

    finally:
        await qdrant_client.close()
        await openai_client.close()


def main() -> None:
    """Entry point."""
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    collection_name = os.getenv("QDRANT_COLLECTION", "pet_knowledge_base")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")

    if not openai_api_key:
        logger.error("OPENAI_API_KEY not set in .env")
        return

    logger.info(
        "Seeding Qdrant: host=%s:%d collection=%s",
        qdrant_host,
        qdrant_port,
        collection_name,
    )
    asyncio.run(
        seed_qdrant(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name=collection_name,
            openai_api_key=openai_api_key,
        )
    )


if __name__ == "__main__":
    main()
