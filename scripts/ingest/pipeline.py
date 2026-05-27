#!/usr/bin/env python3
"""Unified Data Ingestion Pipeline for Qdrant.

Integrates modular parser and text splitting algorithms to securely clean,
embed, and index JSON blogs and PDF manuals.

Prerequisites:
    uv add pypdf langchain-text-splitters
Usage:
    uv run python scripts/ingest/pipeline.py --data-dir ./data
"""

import argparse
import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

# Import modular ingestion components
try:
    from scripts.ingest.splitter import get_splitter
    from scripts.ingest.parser import parse_json_faq, parse_pdf_disease_manual
except ModuleNotFoundError:
    from splitter import get_splitter
    from parser import parse_json_faq, parse_pdf_disease_manual

# Load settings from root .env
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Constants matching active Qdrant setup
VECTOR_DIM = 1536
BATCH_SIZE = 16


class IngestionPipeline:
    """Handles orchestrating the chunking, embedding, and batch upserting to Qdrant."""

    def __init__(self, data_dir: Path, collection_name: str, limit_json: int | None = None):
        self.data_dir = data_dir
        self.collection_name = collection_name
        self.limit_json = limit_json
        self.qdrant_client = AsyncQdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        
        # Initialize splitter module
        self.splitter = get_splitter(chunk_size=900, chunk_overlap=120)

    async def initialize_collection(self) -> None:
        """Create Qdrant collection if not already existing."""
        collections = await self.qdrant_client.get_collections()
        names = [c.name for c in collections.collections]

        if self.collection_name not in names:
            await self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=VECTOR_DIM,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
            logger.info("Created new collection: '%s'", self.collection_name)
        else:
            logger.info("Target collection '%s' is ready.", self.collection_name)

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings using OpenAI embeddings model."""
        response = await self.openai_client.embeddings.create(
            input=texts,
            model="text-embedding-ada-002"
        )
        # Sort values based on index to ensure direct mapping matches
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    async def process_batch(self, batch: list[dict[str, Any]]) -> None:
        """Embed and upsert a batch of documents/chunks into Qdrant."""
        texts_to_embed = [f"{doc['title']}\n{doc['content']}" for doc in batch]
        embeddings = await self.get_embeddings(texts_to_embed)
        
        points = []
        for doc, embedding in zip(batch, embeddings):
            # Generate a stable UUIDv5 from the ID base to ensure idempotency
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc["id_base"]))
            
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
                        "source": doc["source"],
                        "page": doc["page"],
                    }
                )
            )
            
        await self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    async def run(self) -> None:
        """Main execution flow scanning for all target data formats."""
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("Missing OPENAI_API_KEY. Ingestion cancelled.")
            return

        await self.initialize_collection()
        
        all_docs = []
        
        # 1. Scan, clean, and parse files stage
        logger.info("[INGESTION] Scanning and parsing files in directory: %s", self.data_dir.absolute())
        
        for ext in ["*.json", "*.pdf"]:
            for file_path in self.data_dir.rglob(ext):
                if file_path.suffix == ".json":
                    all_docs.extend(parse_json_faq(file_path, self.splitter, self.limit_json))
                elif file_path.suffix == ".pdf":
                    all_docs.extend(parse_pdf_disease_manual(file_path, self.splitter))
                    
        total_docs = len(all_docs)
        logger.info("[INGESTION] Total parsed & cleaned text chunks prepared: %d", total_docs)
        
        if total_docs == 0:
            logger.warning("[INGESTION] No JSON or PDF files found in directory: %s", self.data_dir)
            return
            
        # 2. Batch process embeddings and ingestion stage
        logger.info("[INGESTION] Generating embeddings and upserting points in batches of %d...", BATCH_SIZE)
        
        for i in range(0, total_docs, BATCH_SIZE):
            batch = all_docs[i : i + BATCH_SIZE]
            try:
                await self.process_batch(batch)
                logger.info(
                    "[INGESTION] Successfully ingested batch %d/%d (%d points uploaded)",
                    (i // BATCH_SIZE) + 1,
                    (total_docs + BATCH_SIZE - 1) // BATCH_SIZE,
                    len(batch)
                )
            except Exception as e:
                logger.error("[INGESTION] Failed to ingest batch starting at index %d: %s", i, e)

        # Close clients
        await self.qdrant_client.close()
        await self.openai_client.close()
        logger.info("[INGESTION] Pipeline Execution Completed Successfully!")


def main():
    parser = argparse.ArgumentParser(description="PNetAI Qdrant Ingestion Pipeline")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Directory containing the target PDF and JSON files."
    )
    parser.add_argument(
        "--limit-json",
        type=int,
        default=None,
        help="Limit the number of FAQ/Blog JSON records parsed (useful for trials/testing)."
    )
    args = parser.parse_args()
    
    data_path = Path(args.data_dir)
    if not data_path.exists():
        logger.error("Data directory does not exist: %s", data_path.absolute())
        return

    collection = os.getenv("QDRANT_COLLECTION", "pet_knowledge_base")
    pipeline = IngestionPipeline(data_dir=data_path, collection_name=collection, limit_json=args.limit_json)
    
    # Run pipeline asynchronously
    asyncio.run(pipeline.run())


if __name__ == "__main__":
    main()
