"""Application configuration using pydantic-settings."""

import os
from pathlib import Path
from typing import List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    STUDENT_EMAIL: str = os.getenv("STUDENT_EMAIL", "your-email@example.com")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

    # Directories
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "/tmp/quiz_files"))
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", "/tmp/quiz_cache"))
    LOGS_DIR: Path = Path(os.getenv("LOGS_DIR", "/tmp/quiz_logs"))

    # LLM Config
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "your-openai-api-key")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    LLM_PROVIDER: str = "openai"
    LLM_TEMPERATURE: float = 0.1

    # Gemini Config for File Analysis
    GEMINI_API_KEYS: List[str] = (
        os.getenv("GEMINI_API_KEYS", "").split(",")
        if os.getenv("GEMINI_API_KEYS")
        else []
    )
    GEMINI_MODEL: str = "google/gemini-2.5-flash-lite"
    GEMINI_BASE_URL: str = os.getenv(
        "GEMINI_BASE_URL", "https://aipipe.org/openrouter/v1"
    )

    # Timeouts & Limits
    BROWSER_PAGE_TIMEOUT: int = 10000  # milliseconds
    QUIZ_TIMEOUT_SECONDS: int = 180
    TOOL_TIMEOUT: int = 120  # seconds
    MAX_FILE_SIZE_MB: int = 5

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Config()
