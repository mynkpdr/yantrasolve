"""Centralized Loguru configuration for the service."""

import os
import sys
import time
from loguru import logger
from app.config.settings import settings


# Ensure log directory exists and the timezone is set once at startup.
os.makedirs(settings.LOGS_DIR, exist_ok=True)
os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

# Pick a readable, consistent level for console and file outputs.
LOG_LEVEL = "DEBUG" if settings.DEBUG else "INFO"

logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{file.path}</cyan>:<cyan>{line}</cyan> - {message}",
)
logger.add(
    str(settings.LOGS_DIR / "app_{time:YYYYMMDD_HHmmss}.log"),
    rotation="10 MB",
    retention="7 days",
    level=LOG_LEVEL,
    backtrace=settings.DEBUG,
    diagnose=settings.DEBUG,
    enqueue=True,
)
