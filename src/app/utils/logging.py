from loguru import logger
import sys
from app.config.settings import settings
import os

# Ensure logs directory exists
os.makedirs(settings.LOGS_DIR, exist_ok=True)

# Remove default handler
logger.remove()

logger.level("INFO", icon="ℹ️ ")
logger.level("DEBUG", icon="🤓")

# Console output
logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:HH:mm:ss}</green> | "
    "<level>{level.icon}</level> | <cyan>{file.path}</cyan>:<cyan>{line}</cyan> - {message}",
)

# File output with rotation and retention
# logger.add(
#     f"{settings.LOGS_DIR}/app_{time()}.log",
#     rotation="10 MB",
#     retention="7 days",
#     level="INFO",
#     backtrace=True,
#     diagnose=True,
# )
