"""Create MongoDB indexes for PetBot chat collections.

This module is intended to be executed from the project root with the
activated virtualenv, e.g.:

  python -m src.petbot.infrastructure.persistence.mongodb.create_indexes --dry-run

It reuses the project's Motor client (see `client.py`) to create useful
indexes for `messages` and `sessions` collections.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Dict, List

try:
    from pymongo import ASCENDING, DESCENDING, TEXT
except Exception:  # pragma: no cover - dependency error path
    print("Missing dependency 'pymongo'. Install with 'pip install pymongo' or 'poetry install'", file=sys.stderr)
    raise

from src.petbot.infrastructure.persistence.mongodb.client import connect, close_client, get_database

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


INDEX_DEFS_DEFAULT: Dict[str, List[Dict]] = {
    "messages": [
        {"keys": [("session_id", ASCENDING), ("timestamp", ASCENDING)], "name": "idx_session_timestamp", "unique": False},
        {"keys": [("id", ASCENDING)], "name": "uq_message_id", "unique": True},
        {"keys": [("content", TEXT)], "name": "idx_content_text", "unique": False},
    ],
    "sessions": [
        {"keys": [("user_id", ASCENDING), ("updated_at", DESCENDING)], "name": "idx_user_updated", "unique": False},
        {"keys": [("id", ASCENDING)], "name": "uq_session_id", "unique": True},
    ],
}


async def ensure_indexes(db_name: str | None, collections_map: Dict[str, List[Dict]], dry_run: bool = False, force: bool = False) -> int:
    """Ensure indexes exist for provided collections.

    Returns 0 on success, non-zero on error.
    """
    ok = await connect(retries=5, backoff=1.0)
    if not ok:
        logger.error("Could not connect to MongoDB; aborting")
        return 2

    db = get_database(name=db_name) if db_name else get_database()

    for coll_name, idx_list in collections_map.items():
        coll = db[coll_name]
        try:
            existing = await coll.index_information()
        except Exception as exc:  # pragma: no cover - network/authorization
            logger.exception("Failed to fetch index information for '%s': %s", coll_name, exc)
            return 3

        logger.info("Collection '%s' existing indexes: %s", coll_name, list(existing.keys()))

        for idx in idx_list:
            name = idx.get("name")
            keys = idx["keys"]
            unique = idx.get("unique", False)

            if name in existing:
                if force:
                    logger.info("Dropping existing index '%s' on '%s' (force)", name, coll_name)
                    try:
                        await coll.drop_index(name)
                    except Exception as exc:
                        logger.exception("Failed to drop index '%s' on '%s': %s", name, coll_name, exc)
                        return 4
                else:
                    logger.info("Index '%s' already exists on '%s'; skipping", name, coll_name)
                    continue

            logger.info("Creating index '%s' on '%s' keys=%s unique=%s", name, coll_name, keys, unique)
            if dry_run:
                continue

            try:
                idx_name = await coll.create_index(keys, name=name, unique=unique)
                logger.info("Created index '%s' on '%s'", idx_name, coll_name)
            except Exception as exc:
                logger.exception("Failed to create index '%s' on '%s': %s", name, coll_name, exc)
                return 5

    close_client()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create MongoDB indexes for PetBot chat collections.")
    parser.add_argument("--db", help="Database name (defaults to DB in MONGODB_CHAT_URI)", default=None)
    parser.add_argument("--messages", help="Messages collection name", default="messages")
    parser.add_argument("--sessions", help="Sessions collection name", default="sessions")
    parser.add_argument("--dry-run", action="store_true", help="Print planned indexes but don't create them")
    parser.add_argument("--force", action="store_true", help="Drop and recreate indexes when a name already exists")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    collections_map = {
        args.messages: INDEX_DEFS_DEFAULT.get("messages", []),
        args.sessions: INDEX_DEFS_DEFAULT.get("sessions", []),
    }

    try:
        rc = asyncio.run(ensure_indexes(args.db, collections_map, dry_run=args.dry_run, force=args.force))
        sys.exit(rc if rc is not None else 0)
    except KeyboardInterrupt:
        logger.info("Aborted by user")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Index creation failed: %s", exc)
        sys.exit(2)


if __name__ == "__main__":
    main()
