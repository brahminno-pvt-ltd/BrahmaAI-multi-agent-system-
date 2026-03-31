"""
BrahmaAI Configuration
Centralized settings with environment variable support.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "BrahmaAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "brahmaai-secret-change-in-production"

    # LLM
    LLM_PROVIDER: str = "openai"   # openai | anthropic | ollama
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 4096

    # Agent loop
    MAX_ITERATIONS: int = 10
    MAX_RETRIES: int = 3
    STEP_TIMEOUT_SECONDS: int = 60

    # Memory
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    SHORT_TERM_MAX_MESSAGES: int = 50
    LONG_TERM_TOP_K: int = 5

    # Tools
    SERPAPI_KEY: str = ""
    SANDBOX_TIMEOUT_SECONDS: int = 10

    # Auth
    JWT_SECRET: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
