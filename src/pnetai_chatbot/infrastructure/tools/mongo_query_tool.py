"""MongoDB query executor tool with validation and query generation."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter
from pnetai_chatbot.application.ports.mongo_query_port import IMongoQueryExecutor
from pnetai_chatbot.infrastructure.agent.prompts.mongo_gen_prompt import (
    MONGO_QUERY_GEN_SYSTEM_PROMPT,
)
from pnetai_chatbot.infrastructure.config.mongo_db_schema import (
    ALLOWED_COLLECTIONS,
    FORBIDDEN_OPERATORS,
    WEBSITE_DB_SCHEMA,
)

logger = logging.getLogger(__name__)


class MongoQueryValidator:
    """Validator for LLM-generated MongoDB queries.

    Prevents SQL-injection style bypasses and unauthorized access.
    """

    def validate(
        self,
        collection: str,
        filter_query: dict[str, Any],
        projection: dict[str, int] | None = None,
        limit: int = 20,
        user_id: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, int] | None, int]:
        """Validate a query's collection, operators, limits, and inject user scope.

        Args:
            collection: The target collection name.
            filter_query: MongoDB filter dict.
            projection: Optional field projection.
            limit: Limit on returned documents.
            user_id: Optional authenticated user's ID.

        Returns:
            Validated and secured (filter_query, projection, limit) tuple.

        Raises:
            ValueError: If any validation rule is violated.
        """
        # 1. Collection whitelist validation
        if collection not in ALLOWED_COLLECTIONS:
            raise ValueError(f"Querying collection '{collection}' is not allowed.")

        # 2. Forbidden operators check
        self._check_forbidden_operators(filter_query)

        # 3. Limit validation
        max_limit = 50
        validated_limit = min(max(1, limit), max_limit)

        # 4. Security constraint for 'orders' collection
        if collection == "orders":
            if not user_id:
                raise ValueError(
                    "Access to 'orders' collection is denied for unauthenticated users."
                )
            # Force the authenticated user's user_id into the filter
            filter_query["user_id"] = user_id

        # 5. Projection validation
        if projection:
            self._check_forbidden_operators(projection)
            for key, val in projection.items():
                if not isinstance(val, int) or val not in (0, 1):
                    raise ValueError(
                        f"Invalid projection value '{val}' for field '{key}'."
                    )

        return filter_query, projection, validated_limit

    def _check_forbidden_operators(self, document: Any) -> None:
        """Recursively check for forbidden operators in query filters or projections.

        Args:
            document: The query document component to check.

        Raises:
            ValueError: If a forbidden operator is found.
        """
        if isinstance(document, dict):
            for key, value in document.items():
                if key in FORBIDDEN_OPERATORS:
                    raise ValueError(
                        f"Use of forbidden MongoDB operator '{key}' is detected."
                    )
                self._check_forbidden_operators(value)
        elif isinstance(document, list):
            for item in document:
                self._check_forbidden_operators(item)


class MongoQueryGenerator:
    """Generates MongoDB queries using an LLM based on user queries and schemas."""

    def __init__(self, llm: ILLMAdapter) -> None:
        """Initialize the MongoQueryGenerator.

        Args:
            llm: Concrete implementation of ILLMAdapter.
        """
        self._llm = llm

    async def generate_query(
        self,
        user_query: str,
        collection: str,
        schema_context: str,
    ) -> dict[str, Any]:
        """Generate a MongoDB query using the LLM.

        Args:
            user_query: The raw query from the user.
            collection: The target collection name.
            schema_context: The schema context for the collection.

        Returns:
            A dictionary containing 'collection', 'filter', 'projection',
            'sort', and 'limit'.
        """
        prompt = MONGO_QUERY_GEN_SYSTEM_PROMPT.format(
            schema_context=schema_context,
            user_query=user_query,
        )

        # Call the LLM with temperature=0 for maximum deterministic output
        response = await self._llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            query_json = json.loads(text)
            return query_json
        except json.JSONDecodeError as e:
            logger.error(
                "LLM failed to generate valid JSON query: %s. Output: %s", e, text
            )
            raise ValueError(f"LLM generated invalid JSON query: {e}") from e


class MongoQueryTool(IMongoQueryExecutor):
    """MongoDB query tool implementation.

    Handles execution of generated MongoDB queries against the website database
    with strict security checks, query validation, and result formatting.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize the MongoQueryTool.

        Args:
            db: Motor database instance for the website database.
        """
        self._db = db
        self._validator = MongoQueryValidator()

    async def get_schema_context(self, collection: str) -> str:
        """Get the schema description for a collection.

        Used to inject schema info into LLM prompts for query generation.

        Args:
            collection: Collection name.

        Returns:
            Human-readable schema description string.

        Raises:
            ValueError: If collection is not allowed or does not exist.
        """
        if collection not in WEBSITE_DB_SCHEMA:
            raise ValueError(
                f"Collection '{collection}' is not allowed or does not exist."
            )

        schema_info = WEBSITE_DB_SCHEMA[collection]
        lines = [
            f"Collection: {collection}",
            f"Description: {schema_info.get('description', '')}",
            "Fields:",
        ]
        for field, desc in schema_info.get("fields", {}).items():
            lines.append(f"  - {field}: {desc}")

        if "indexes" in schema_info:
            lines.append(f"Indexes: {', '.join(schema_info['indexes'])}")

        if "security_note" in schema_info:
            lines.append(f"Security Note: {schema_info['security_note']}")

        return "\n".join(lines)

    async def execute_generated_query(
        self,
        collection: str,
        filter_query: dict[str, Any],
        projection: dict[str, int] | None = None,
        limit: int = 20,
        sort: list[tuple[str, int]] | dict[str, int] | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a generated query with security validation.

        Queries the website MongoDB database.

        Args:
            collection: Target collection name.
            filter_query: MongoDB filter document.
            projection: Optional field projection.
            limit: Maximum documents to return.
            sort: Optional sorting options.
            user_id: Optional authenticated user ID.

        Returns:
            List of sanitized and serialized result documents.
        """
        logger.info(
            "Executing query on collection '%s' (limit=%d, user_id=%s)",
            collection,
            limit,
            user_id,
        )

        # 1. Validate and secure the parameters
        secured_filter, secured_proj, secured_limit = self._validator.validate(
            collection=collection,
            filter_query=filter_query,
            projection=projection,
            limit=limit,
            user_id=user_id,
        )

        # 2. Build the query cursor
        coll_ref = self._db[collection]
        cursor = coll_ref.find(secured_filter, secured_proj)

        if sort:
            # Pymongo/Motor requires list of tuples for sorting
            sort_list = list(sort.items()) if isinstance(sort, dict) else sort
            cursor = cursor.sort(sort_list)

        cursor = cursor.limit(secured_limit)
        raw_results = await cursor.to_list(length=secured_limit)

        # 3. Clean and serialize the results
        return self._serialize_results(raw_results)

    def _serialize_results(self, docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Serialize and sanitize MongoDB result documents.

        Converts ObjectIds to strings, datetimes to ISO strings, and truncates
        very long descriptions to 500 characters.
        """
        sanitized = []
        for doc in docs:
            clean_doc = {}
            for k, v in doc.items():
                if isinstance(v, ObjectId):
                    clean_doc[k] = str(v)
                elif isinstance(v, datetime):
                    clean_doc[k] = v.isoformat()
                elif k == "description" and isinstance(v, str) and len(v) > 500:
                    clean_doc[k] = v[:500] + "..."
                elif isinstance(v, dict):
                    clean_doc[k] = self._serialize_dict(v)
                elif isinstance(v, list):
                    clean_doc[k] = self._serialize_list(v)
                else:
                    clean_doc[k] = v
            sanitized.append(clean_doc)
        return sanitized

    def _serialize_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        """Recursively serialize a dictionary."""
        res = {}
        for k, v in d.items():
            if isinstance(v, ObjectId):
                res[k] = str(v)
            elif isinstance(v, datetime):
                res[k] = v.isoformat()
            elif isinstance(v, dict):
                res[k] = self._serialize_dict(v)
            elif isinstance(v, list):
                res[k] = self._serialize_list(v)
            else:
                res[k] = v
        return res

    def _serialize_list(self, lst: list[Any]) -> list[Any]:
        """Recursively serialize a list."""
        res = []
        for v in lst:
            if isinstance(v, ObjectId):
                res.append(str(v))
            elif isinstance(v, datetime):
                res.append(v.isoformat())
            elif isinstance(v, dict):
                res.append(self._serialize_dict(v))
            elif isinstance(v, list):
                res.append(self._serialize_list(v))
            else:
                res.append(v)
        return res
