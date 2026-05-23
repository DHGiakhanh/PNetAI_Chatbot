"""FastAPI Dependency Injection providers for V1 endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, Request

from pnetai_chatbot.application.services.permission_service import PermissionService
from pnetai_chatbot.application.use_cases.chat.chat_orchestrator_use_case import (
    ChatOrchestratorUseCase,
)
from pnetai_chatbot.application.use_cases.chat.create_session import (
    CreateSessionUseCase,
)
from pnetai_chatbot.application.use_cases.chat.get_session_history import (
    GetSessionHistoryUseCase,
)
from pnetai_chatbot.application.use_cases.session.resolve_user_context import (
    ResolveUserContextUseCase,
)
from pnetai_chatbot.application.use_cases.session.summarize_session import (
    SummarizeSessionUseCase,
)
from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.infrastructure.agent.orchestrator import AgentOrchestrator
from pnetai_chatbot.infrastructure.config.settings import get_settings
from pnetai_chatbot.infrastructure.llm.llm_factory import LLMFactory
from pnetai_chatbot.infrastructure.persistence.mongodb.client import (
    get_chat_client,
    get_website_client,
)
from pnetai_chatbot.infrastructure.persistence.mongodb.history_repo import (
    HistoryRepository,
)
from pnetai_chatbot.infrastructure.persistence.mongodb.session_repo import (
    SessionRepository,
)
from pnetai_chatbot.infrastructure.persistence.qdrant.client import get_qdrant_client
from pnetai_chatbot.infrastructure.tools.mongo_query_tool import MongoQueryTool
from pnetai_chatbot.infrastructure.tools.tavily_tool import TavilyWebSearchTool
from pnetai_chatbot.infrastructure.tools.tool_registry import ToolRegistry
from pnetai_chatbot.infrastructure.tools.vector_search_tool import (
    QdrantVectorSearchTool,
)


def get_current_user(request: Request) -> User:
    """Extract user entity from the request state.

    Falls back to guest if unauthenticated.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The extracted User domain entity.
    """
    return getattr(request.state, "user", User.guest())


def get_session_repository() -> SessionRepository:
    """Provide the SessionRepository database port."""
    chat_client = get_chat_client()
    return SessionRepository(chat_client.db)


def get_history_repository() -> HistoryRepository:
    """Provide the HistoryRepository database port."""
    chat_client = get_chat_client()
    return HistoryRepository(chat_client.db)


def get_permission_service() -> PermissionService:
    """Provide the PermissionService domain policy validator."""
    return PermissionService()


def get_llm_adapter() -> Any:
    """Provide the primary LLM adapter class."""
    return LLMFactory.create_from_settings()


def get_tool_registry() -> ToolRegistry:
    """Build and provide the agent's ToolRegistry."""
    settings = get_settings()

    web_search = TavilyWebSearchTool(settings.tavily_api_key)

    qdrant_manager = get_qdrant_client()
    vector_search = QdrantVectorSearchTool(
        client=qdrant_manager.client,
        collection_name=settings.qdrant_collection,
    )

    website_db = get_website_client()
    mongo_search = MongoQueryTool(db=website_db.db)

    return ToolRegistry(
        web_search_tool=web_search,
        vector_store_tool=vector_search,
        mongo_query_executor=mongo_search,
    )


def get_agent_orchestrator(
    registry: ToolRegistry = Depends(get_tool_registry),
    llm: Any = Depends(get_llm_adapter),
) -> Any:
    """Compile and provide the executable LangGraph state graph."""
    orchestrator = AgentOrchestrator(registry=registry, llm=llm)
    return orchestrator.build_agent_graph()


def get_create_session_use_case(
    repo: SessionRepository = Depends(get_session_repository),
) -> CreateSessionUseCase:
    """Provide the CreateSessionUseCase."""
    return CreateSessionUseCase(repo)


def get_get_history_use_case(
    history_repo: HistoryRepository = Depends(get_history_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> GetSessionHistoryUseCase:
    """Provide the GetSessionHistoryUseCase."""
    return GetSessionHistoryUseCase(session_repo, history_repo)


def get_resolve_context_use_case(
    session_repo: SessionRepository = Depends(get_session_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
    permissions: PermissionService = Depends(get_permission_service),
) -> ResolveUserContextUseCase:
    """Provide the ResolveUserContextUseCase."""
    return ResolveUserContextUseCase(
        session_repository=session_repo,
        history_repository=history_repo,
        permission_service=permissions,
    )


def get_summarize_session_use_case(
    history_repo: HistoryRepository = Depends(get_history_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    llm: Any = Depends(get_llm_adapter),
) -> SummarizeSessionUseCase:
    """Provide the SummarizeSessionUseCase."""
    return SummarizeSessionUseCase(session_repo, history_repo, llm)


def get_chat_orchestrator(
    graph: Any = Depends(get_agent_orchestrator),
    session_repo: SessionRepository = Depends(get_session_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
    summarize: SummarizeSessionUseCase = Depends(get_summarize_session_use_case),
) -> ChatOrchestratorUseCase:
    """Provide the main ChatOrchestratorUseCase."""
    return ChatOrchestratorUseCase(
        compiled_graph=graph,
        session_repository=session_repo,
        history_repository=history_repo,
        summarize_use_case=summarize,
    )
