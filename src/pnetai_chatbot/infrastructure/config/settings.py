"""Application configuration via Pydantic BaseSettings.

Loads from .env file and environment variables.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ---- App ----
    app_env: str = "development"
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ---- LLM (Primary) ----
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048
    openai_api_key: str = ""

    # ---- LLM (Fallback) ----
    llm_fallback_provider: str = "anthropic"
    llm_fallback_model: str = "claude-haiku-4-5"
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # ---- LLM (Response / Final Answer) ----
    # Khi được cấu hình, adapter này sẽ thay thế LLM chính CHỈ tại bước
    # response_generator (sinh câu trả lời cuối). Để trống -> dùng llm_provider.
    response_llm_provider: str = ""  # vd: "selfhosted", "ollama", "openai"
    response_llm_model: str = ""     # Tên model; để trống -> dùng llm_model

    # ---- Self-Hosted LLM (OpenAI-compatible server) ----
    selfhosted_base_url: str = "http://localhost:8080/v1"
    selfhosted_api_key: str = "not-required"
    selfhosted_timeout: float = 60.0

    # ---- Ollama (Local Dev) ----
    ollama_host: str = "http://localhost:11434"

    # ---- Tavily ----
    tavily_api_key: str = ""

    # ---- MongoDB (Chat DB) ----
    mongodb_chat_uri: str = "mongodb://localhost:27017/pnetai_chat"

    # ---- MongoDB (Website DB — existing, read-only) ----
    mongodb_website_uri: str = "mongodb://localhost:27017/pet_website"

    # ---- Qdrant (Vector DB) ----
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "pet_knowledge_base"

    # ---- Auth ----
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # ---- Session ----
    max_history_messages: int = 20
    summary_trigger_every: int = 10
    max_tool_iterations: int = 5

    # ---- Rate Limiting ----
    rate_limit_guest: int = 30  # Requests per minute for guest users
    rate_limit_member: int = 100  # Requests per minute for authenticated members

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()
