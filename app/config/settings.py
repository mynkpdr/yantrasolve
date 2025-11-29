import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Config(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    STUDENT_EMAIL: str = os.getenv("STUDENT_EMAIL", "your-email@example.com")

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "/tmp/quiz_files"))
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", "/tmp/quiz_cache"))
    LOGS_DIR: Path = Path(os.getenv("LOGS_DIR", "/tmp/quiz_logs"))

    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "your-openai-api-key")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = "gpt-5-mini"
    LLM_PROVIDER: str = "openai"  # or anthropic or google
    LLM_TEMPERATURE: float = 0.1

    GEMINI_API_KEY_1: str = os.getenv("GEMINI_API_KEY_1", "your-gemini-api-key")
    GEMINI_API_KEY_2: str = os.getenv("GEMINI_API_KEY_2", "your-gemini-api-key")
    GEMINI_API_KEY_3: str = os.getenv("GEMINI_API_KEY_3", "your-gemini-api-key")

    BROWSER_PAGE_TIMEOUT: int = 10000  # in milliseconds

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Config()
