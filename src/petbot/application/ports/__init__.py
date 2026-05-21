"""Application ports (interfaces) for PetBot.

These are the abstract interfaces (ports) the application layer depends on.
Concrete adapters live in `infrastructure` and implement these interfaces.
"""

from .llm_port import ILLMAdapter
from .vector_store_port import IVectorStore
from .mongo_query_port import IMongoQueryExecutor
from .web_search_port import IWebSearchTool
from .session_repo_port import ISessionRepository
from .history_repo_port import IHistoryRepository

__all__ = [
    "ILLMAdapter",
    "IVectorStore",
    "IMongoQueryExecutor",
    "IWebSearchTool",
    "ISessionRepository",
    "IHistoryRepository",
]
# src/petbot/application/ports package
