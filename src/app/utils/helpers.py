from pathlib import Path
from app.config.settings import settings
import time
import asyncio
import random
from app.utils.logging import logger


def setup_temp_directory() -> None:
    """
    Create temporary directory for file storage if it doesn't exist.
    """
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)


def cleanup_temp_files(older_than: int = 3600) -> int:
    """
    Remove old temporary files.

    Args:
        older_than: Remove files older than this many seconds (default 1 hour)

    Returns:
        Number of files removed
    """
    temp_dir = Path(settings.TEMP_DIR)
    if not temp_dir.exists():
        return 0

    current_time = time.time()
    removed_count = 0

    for file_path in temp_dir.rglob("*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > older_than:
                try:
                    file_path.unlink()
                    removed_count += 1
                except Exception:
                    pass

    return removed_count


async def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    exceptions: tuple = (Exception,),
):
    """
    Retry an async function with exponential backoff and jitter.

    Args:
        func: The async function to call.
        max_retries: Maximum number of retries.
        base_delay: Initial delay between retries.
        max_delay: Maximum delay between retries.
        exceptions: Exception types to catch and retry on.

    Returns:
        Result of func() if successful.

    Raises:
        Last exception raised by func() if all retries fail.
    """
    attempt = 0
    while True:
        try:
            return await func()
        except exceptions as e:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Max retries reached: {e}")
                raise
            # exponential backoff with jitter
            delay = min(max_delay, base_delay * 2 ** (attempt - 1))
            jitter = random.uniform(0, delay * 0.1)  # small random jitter
            total_delay = delay + jitter
            logger.warning(
                f"Retry {attempt}/{max_retries} after {total_delay:.2f}s due to: {e}"
            )
            await asyncio.sleep(total_delay)
