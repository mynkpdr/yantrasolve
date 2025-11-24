from pathlib import Path
from app.config.settings import settings
import time


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
