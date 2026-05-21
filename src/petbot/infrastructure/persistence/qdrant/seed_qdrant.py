"""Seed data into Qdrant (pet knowledge base).

This script supports two modes:
- `--sample N` : create N sample records with random vectors (useful for local testing)
- `--file PATH` : read JSONL file where each line is a JSON object with keys
  `id` (optional), `text` (required), `payload` (optional dict), and optionally
  `vector` (list of floats). If `vector` is missing the record will be skipped
  unless `--allow-random-vectors` is passed.

Run from project root with the activated venv:

  python -m src.petbot.infrastructure.persistence.qdrant.seed_qdrant --sample 10

Dependencies: `qdrant-client` and `pydantic` (for settings). Install via
`pip install qdrant-client` or `poetry install`.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from typing import Any, Dict, Iterable, List, Optional

from qdrant_client.http import models as rest

from src.petbot.infrastructure.config.settings import get_settings
from src.petbot.infrastructure.persistence.qdrant.client import get_client, ensure_collection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def random_vector(size: int) -> List[float]:
    return [random.random() for _ in range(size)]


def read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def build_points_from_records(records: Iterable[Dict[str, Any]], vector_size: int, allow_random: bool = False) -> List[rest.PointStruct]:
    points: List[rest.PointStruct] = []
    for i, rec in enumerate(records):
        text = rec.get("text") or rec.get("content")
        if not text:
            logger.warning("Skipping record without 'text' field: %s", rec)
            continue
        vec = rec.get("vector")
        if vec is None:
            if allow_random:
                vec = random_vector(vector_size)
            else:
                logger.warning("Skipping record without vector (id=%s); pass --allow-random-vectors to generate random vectors", rec.get("id"))
                continue

        pid = rec.get("id") or f"auto-{i}"
        payload = rec.get("payload") or {"text": text}
        points.append(rest.PointStruct(id=str(pid), vector=vec, payload=payload))
    return points


def sample_points(n: int, vector_size: int) -> List[rest.PointStruct]:
    samples = [
        "How do I stop my dog from chewing shoes?",
        "My cat keeps coughing, what should I do?",
        "Best food for a 2-year-old golden retriever",
        "How often should I bathe my rabbit?",
        "Symptoms of flea infestation on pets",
        "How to introduce two dogs safely",
        "Vitamins recommended for senior cats",
        "How to trim a cat's nails without stress",
        "What vaccines does a puppy need?",
        "Traveling with a parrot: checklist",
    ]
    points: List[rest.PointStruct] = []
    for i in range(n):
        text = samples[i % len(samples)]
        vec = random_vector(vector_size)
        payload = {"text": text, "source": "sample"}
        points.append(rest.PointStruct(id=f"sample-{i}", vector=vec, payload=payload))
    return points


def chunked(iterable: List[Any], size: int) -> Iterable[List[Any]]:
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def upsert_points(client, collection_name: str, points: List[rest.PointStruct], batch_size: int = 64) -> None:
    if not points:
        logger.info("No points to upsert")
        return
    for batch in chunked(points, batch_size):
        logger.info("Upserting batch of %d points into '%s'...", len(batch), collection_name)
        client.upsert(collection_name=collection_name, points=batch)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed Qdrant pet knowledge base")
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--sample", type=int, help="Create N sample records with random vectors")
    grp.add_argument("--file", type=str, help="Path to JSONL file with records")
    p.add_argument("--collection", type=str, default=None, help="Collection name (defaults to QDRANT_COLLECTION)")
    p.add_argument("--vector-size", type=int, default=1536, help="Vector size when generating random vectors")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--allow-random-vectors", action="store_true", help="Allow generating random vectors for records without vector field")
    p.add_argument("--force-create", action="store_true", help="Create collection if missing")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    collection = args.collection or settings.QDRANT_COLLECTION
    client = get_client()

    if args.force_create:
        logger.info("Ensuring collection '%s' exists (vector_size=%d)", collection, args.vector_size)
        ensure_collection(collection_name=collection, vector_size=args.vector_size)

    points: List[rest.PointStruct] = []
    if args.sample:
        points = sample_points(args.sample, vector_size=args.vector_size)
    elif args.file:
        recs = list(read_jsonl(args.file))
        points = build_points_from_records(recs, vector_size=args.vector_size, allow_random=args.allow_random_vectors)

    if not points:
        logger.info("No points prepared; exiting")
        return

    upsert_points(client, collection, points, batch_size=args.batch_size)
    logger.info("Upsert complete. Seeded %d points into '%s'", len(points), collection)


if __name__ == "__main__":
    main()
