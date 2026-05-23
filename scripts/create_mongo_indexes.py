#!/usr/bin/env python3
"""Create MongoDB indexes for chat collections.

Usage:
    uv run python scripts/create_mongo_indexes.py

Collections:
    - chat_sessions: session storage
    - chat_messages: message history

Indexes follow the system-spec.md definition.
"""

from __future__ import annotations

import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

INDEXES = {
    "chat_sessions": [
        {
            "keys": [("user_id", 1)],
            "name": "idx_sessions_user_id",
            "background": True,
        },
        {
            "keys": [("created_at", -1)],
            "name": "idx_sessions_created_at",
            "background": True,
        },
    ],
    "chat_messages": [
        {
            "keys": [("session_id", 1), ("timestamp", 1)],
            "name": "idx_messages_session_timestamp",
            "background": True,
        },
        {
            "keys": [("session_id", 1), ("role", 1)],
            "name": "idx_messages_session_role",
            "background": True,
        },
    ],
}


async def create_indexes(uri: str, db_name: str) -> None:
    """Ensure all required indexes exist."""
    client = AsyncIOMotorClient(uri)
    db = client[db_name]

    for collection_name, indexes in INDEXES.items():
        collection = db[collection_name]
        existing = await collection.index_information()

        for index_def in indexes:
            index_name = index_def["name"]
            if index_name in existing:
                logger.info("SKIP: %s.%s already exists", collection_name, index_name)
                continue

            await collection.create_index(
                keys=index_def["keys"],
                name=index_name,
                background=index_def.get("background", True),
            )
            logger.info("CREATED: %s.%s %s", collection_name, index_name, index_def["keys"])

    client.close()
    logger.info("Index creation complete.")


def main() -> None:
    """Entry point."""
    import os
    import sys

    # Allow override via env or command line
    uri = os.getenv(
        "MONGODB_CHAT_URI",
        "mongodb://petbot:petbot_secret@localhost:27017/pnetai_chat?authSource=admin",
    )

    # Extract database name from URI
    db_name = uri.rsplit("/", 1)[-1].split("?")[0] if "/" in uri else "pnetai_chat"

    logger.info("Connecting to MongoDB: %s (db=%s)", "***@***", db_name)
    asyncio.run(create_indexes(uri, db_name))


if __name__ == "__main__":
    main()
