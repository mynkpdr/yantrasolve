"""Helper utilities for file management and async operations."""

import hashlib
import time
import asyncio
import random
from pathlib import Path
from typing import Any
from app.config.settings import settings
from app.utils.logging import logger


def setup_temp_directory() -> None:
    """Create temporary directory if it doesn't exist."""
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)


def cleanup_temp_files(older_than: int = 3600) -> int:
    """Remove temp files older than specified seconds. Returns count removed."""
    temp_dir = Path(settings.TEMP_DIR)
    if not temp_dir.exists():
        return 0

    current_time = time.time()
    removed = 0
    for file_path in temp_dir.rglob("*"):
        if (
            file_path.is_file()
            and (current_time - file_path.stat().st_mtime) > older_than
        ):
            try:
                file_path.unlink()
                removed += 1
            except Exception:
                pass
    return removed


async def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    exceptions: tuple = (Exception,),
):
    """Retry async function with exponential backoff and jitter."""
    attempt = 0
    while True:
        try:
            return await func()
        except exceptions as e:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Max retries reached: {e}")
                raise
            delay = min(max_delay, base_delay * 2 ** (attempt - 1))
            total_delay = delay + random.uniform(0, delay * 0.1)
            logger.warning(
                f"Retry {attempt}/{max_retries} after {total_delay:.2f}s: {e}"
            )
            await asyncio.sleep(total_delay)


def hash_content(content: Any) -> str:
    """Generate SHA256 hash from content."""
    if isinstance(content, bytes):
        content_bytes = content
    elif isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = str(content).encode("utf-8")
    return hashlib.sha256(content_bytes).hexdigest()
