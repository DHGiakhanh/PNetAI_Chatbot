
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # App
    APP_ENV: str = Field("development", env="APP_ENV")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # LLM
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")
    LLM_MODEL: str = Field("gpt-4o-mini", env="LLM_MODEL")
    LLM_TEMPERATURE: float = Field(0.3, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(2048, env="LLM_MAX_TOKENS")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    GEMINI_API_KEY: Optional[str] = Field(None, env="GEMINI_API_KEY")

    # Tavily
    TAVILY_API_KEY: Optional[str] = Field(None, env="TAVILY_API_KEY")

    # MongoDB
    MONGODB_CHAT_URI: str = Field("mongodb://localhost:27017/petbot_chat", env="MONGODB_CHAT_URI")
    MONGODB_WEBSITE_URI: Optional[str] = Field(None, env="MONGODB_WEBSITE_URI")

    # Qdrant
    QDRANT_HOST: str = Field("localhost", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(6333, env="QDRANT_PORT")
    QDRANT_COLLECTION: str = Field("pet_knowledge_base", env="QDRANT_COLLECTION")

    # Auth
    JWT_SECRET: Optional[str] = Field(None, env="JWT_SECRET")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")

    # Session / Behaviour
    MAX_HISTORY_MESSAGES: int = Field(20, env="MAX_HISTORY_MESSAGES")
    SUMMARY_TRIGGER_EVERY: int = Field(10, env="SUMMARY_TRIGGER_EVERY")
    MAX_TOOL_ITERATIONS: int = Field(5, env="MAX_TOOL_ITERATIONS")

    class Config:
        # Use .env by default; developers can copy .env.example -> .env
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
