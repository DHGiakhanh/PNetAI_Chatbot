"""Unit tests for MongoDB query validator, generator, and executor."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from pnetai_chatbot.application.ports.llm_port import ILLMAdapter, LLMResponse
from pnetai_chatbot.infrastructure.tools.mongo_query_tool import (
    MongoQueryGenerator,
    MongoQueryTool,
    MongoQueryValidator,
)


# ==========================================
# 1. MongoQueryValidator Tests
# ==========================================
def test_validator_whitelist_collections() -> None:
    """Test that validator allows whitelisted collections and rejects others."""
    validator = MongoQueryValidator()

    # Allowed
    filter_q, proj_q, limit_q = validator.validate(
        collection="products", filter_query={"is_active": True}
    )
    assert filter_q == {"is_active": True}
    assert proj_q is None
    assert limit_q == 20

    # Disallowed
    with pytest.raises(ValueError, match="Querying collection 'users' is not allowed"):
        validator.validate(collection="users", filter_query={})


def test_validator_forbidden_operators() -> None:
    """Test that validator detects and rejects forbidden operators recursively."""
    validator = MongoQueryValidator()

    # Reject forbidden operator in top-level filter
    with pytest.raises(
        ValueError, match="Use of forbidden MongoDB operator '\\$where' is detected"
    ):
        validator.validate(
            collection="products",
            filter_query={"$where": "this.price > 10"},
        )

    # Reject forbidden operator in nested filter
    with pytest.raises(
        ValueError, match="Use of forbidden MongoDB operator '\\$eval' is detected"
    ):
        validator.validate(
            collection="products",
            filter_query={
                "price": {"$gte": 100},
                "metadata": {"$eval": "code()"},
            },
        )

    # Reject forbidden operator in list
    with pytest.raises(
        ValueError,
        match="Use of forbidden MongoDB operator '\\$function' is detected",
    ):
        validator.validate(
            collection="products",
            filter_query={
                "$and": [
                    {"category": "dog_food"},
                    {"$function": "func"},
                ]
            },
        )


def test_validator_limit_bounds() -> None:
    """Test that limit is bounded between 1 and 50."""
    validator = MongoQueryValidator()

    _, _, limit1 = validator.validate("products", {}, limit=100)
    assert limit1 == 50

    _, _, limit2 = validator.validate("products", {}, limit=-5)
    assert limit2 == 1

    _, _, limit3 = validator.validate("products", {}, limit=25)
    assert limit3 == 25


def test_validator_orders_collection_security() -> None:
    """Test that orders collection queries enforce user scoping."""
    validator = MongoQueryValidator()

    # 1. Unauthenticated -> Reject
    with pytest.raises(
        ValueError,
        match="Access to 'orders' collection is denied",
    ):
        validator.validate(collection="orders", filter_query={})

    # 2. Authenticated -> Inject user
    filter_q, _, _ = validator.validate(
        collection="orders", filter_query={"status": "delivered"}, user_id="user123"
    )
    assert filter_q == {"status": "delivered", "user": "user123"}

    # 3. Inject overwrites LLM generated user for security
    filter_q2, _, _ = validator.validate(
        collection="orders",
        filter_query={"user": "malicious_user", "status": "pending"},
        user_id="legit_user",
    )
    assert filter_q2 == {"status": "pending", "user": "legit_user"}


def test_validator_projection_validation() -> None:
    """Test that projection values are validated properly."""
    validator = MongoQueryValidator()

    # Valid
    _, proj, _ = validator.validate(
        "products", {}, projection={"name": 1, "price": 1, "_id": 0}
    )
    assert proj == {"name": 1, "price": 1, "_id": 0}

    # Invalid
    with pytest.raises(ValueError, match="Invalid projection value"):
        validator.validate("products", {}, projection={"name": "include"})


# ==========================================
# 2. MongoQueryGenerator Tests
# ==========================================
@pytest.mark.asyncio
async def test_query_generator_success() -> None:
    """Test that MongoQueryGenerator successfully calls LLM and parses JSON query."""
    mock_llm = MagicMock(spec=ILLMAdapter)
    mock_response = MagicMock(spec=LLMResponse)
    mock_response.text = """
    ```json
    {
      "collection": "products",
      "filter": {"price": {"$lte": 100000}},
      "projection": {"name": 1, "price": 1},
      "sort": {"price": 1},
      "limit": 5
    }
    ```
    """
    mock_llm.chat = AsyncMock(return_value=mock_response)

    generator = MongoQueryGenerator(llm=mock_llm)
    result = await generator.generate_query(
        user_query="thức ăn dưới 100k",
        collection="products",
        schema_context="Mock Schema Context",
    )

    # Verify LLM was called with temperature 0.0
    mock_llm.chat.assert_called_once()
    call_kwargs = mock_llm.chat.call_args[1]
    assert call_kwargs["temperature"] == 0.0

    # Verify parsed JSON structure
    assert result["collection"] == "products"
    assert result["filter"] == {"price": {"$lte": 100000}}
    assert result["projection"] == {"name": 1, "price": 1}
    assert result["sort"] == {"price": 1}
    assert result["limit"] == 5


@pytest.mark.asyncio
async def test_query_generator_invalid_json() -> None:
    """Test that generator raises ValueError when LLM output is not JSON."""
    mock_llm = MagicMock(spec=ILLMAdapter)
    mock_response = MagicMock(spec=LLMResponse)
    mock_response.text = "This is not JSON text at all."
    mock_llm.chat = AsyncMock(return_value=mock_response)

    generator = MongoQueryGenerator(llm=mock_llm)
    with pytest.raises(ValueError, match="LLM generated invalid JSON query"):
        await generator.generate_query("query", "products", "schema")


# ==========================================
# 3. Result Serializer & MongoQueryTool Tests
# ==========================================
@pytest.mark.asyncio
async def test_query_tool_get_schema_context() -> None:
    """Test that get_schema_context formats schema definitions correctly."""
    mock_db = MagicMock(spec=AsyncIOMotorDatabase)
    tool = MongoQueryTool(db=mock_db)

    # Success
    context = await tool.get_schema_context("products")
    assert "Collection: products" in context
    assert "name: str" in context
    assert "Indexes: category, tags" in context

    # Disallowed Collection raises ValueError
    with pytest.raises(ValueError, match="is not allowed or does not exist"):
        await tool.get_schema_context("non_existent")


@pytest.mark.asyncio
async def test_query_tool_serialization() -> None:
    """Test results serialization, ObjectId, datetime, and truncation."""
    mock_db = MagicMock(spec=AsyncIOMotorDatabase)
    tool = MongoQueryTool(db=mock_db)

    obj_id = ObjectId()
    dt = datetime(2026, 5, 22, 12, 0, 0)
    long_desc = "A" * 600

    raw_docs = [
        {
            "_id": obj_id,
            "created_at": dt,
            "description": long_desc,
            "nested": {
                "id": obj_id,
                "dates": [dt],
            },
        }
    ]

    serialized = tool._serialize_results(raw_docs)

    assert len(serialized) == 1
    doc = serialized[0]
    assert doc["_id"] == str(obj_id)
    assert doc["created_at"] == dt.isoformat()
    assert doc["description"] == ("A" * 500) + "..."
    assert doc["nested"]["id"] == str(obj_id)
    assert doc["nested"]["dates"][0] == dt.isoformat()


@pytest.mark.asyncio
async def test_query_tool_execute_generated_query() -> None:
    """Test full query execution, validation, cursor calls, and serialization."""
    mock_db = MagicMock(spec=AsyncIOMotorDatabase)

    # Mock Collection Reference & Find Cursor
    mock_collection = MagicMock()
    mock_cursor = MagicMock()

    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor

    # Return raw results
    obj_id = ObjectId()
    mock_cursor.to_list = AsyncMock(
        return_value=[{"_id": obj_id, "name": "Standard Product", "price": 50000}]
    )

    tool = MongoQueryTool(db=mock_db)

    results = await tool.execute_generated_query(
        collection="products",
        filter_query={"name": "Standard Product"},
        projection={"name": 1, "price": 1},
        limit=10,
        sort={"price": 1},
    )

    # Verify db call
    mock_db.__getitem__.assert_called_once_with("products")
    mock_collection.find.assert_called_once_with(
        {"name": "Standard Product"}, {"name": 1, "price": 1}
    )
    mock_cursor.sort.assert_called_once_with([("price", 1)])
    mock_cursor.limit.assert_called_once_with(10)
    mock_cursor.to_list.assert_called_once_with(length=10)

    # Verify serialization
    assert len(results) == 1
    assert results[0]["_id"] == str(obj_id)
    assert results[0]["name"] == "Standard Product"
    assert results[0]["price"] == 50000
