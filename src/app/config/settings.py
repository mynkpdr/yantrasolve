import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    STUDENT_EMAIL: str = os.getenv("STUDENT_EMAIL", "your-email@example.com")

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "/tmp/quiz_files"))
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", "/tmp/quiz_cache"))
    LOGS_DIR: Path = Path(os.getenv("LOGS_DIR", "/tmp/quiz_logs"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Config()
