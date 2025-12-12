"""File-based caching utilities with TTL support."""

import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Optional, Tuple
from app.config.settings import settings
from app.utils.logging import logger


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate unique cache key from prefix and arguments."""
    payload = json.dumps(
        {"args": list(args), "kwargs": kwargs}, sort_keys=True, default=str
    )
    return f"{prefix}_{hashlib.sha256(payload.encode()).hexdigest()}"


def get_cache_path(key: str, use_json: bool = True) -> Path:
    """Get file path for a cache key."""
    settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return settings.CACHE_DIR / (key + (".json" if use_json else ".pkl"))


def cache_get(
    key: str, ttl_seconds: int = 3600, use_json: bool = True
) -> Tuple[bool, Optional[Any]]:
    """Check for valid cache entry and return it.

    Returns:
        Tuple of (cache_hit, data or None)
    """
    cache_file = get_cache_path(key, use_json)
    if not cache_file.exists():
        return False, None

    age = time.time() - cache_file.stat().st_mtime
    if age >= ttl_seconds:
        cache_file.unlink(missing_ok=True)
        return False, None

    try:
        if use_json:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            with open(cache_file, "rb") as f:
                data = pickle.load(f)
        return True, data
    except Exception as e:
        logger.warning(f"[cache] Failed to read: {e}")
        cache_file.unlink(missing_ok=True)
        return False, None


def cache_set(key: str, data: Any, use_json: bool = True) -> bool:
    """Store data in cache. Returns True if successful."""
    cache_file = get_cache_path(key, use_json)
    try:
        if use_json:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        else:
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"[cache] Failed to write: {e}")
        return False


def cache_delete(key: str, use_json: bool = True) -> bool:
    """Delete a cache entry. Returns True if deleted."""
    cache_file = get_cache_path(key, use_json)
    if cache_file.exists():
        cache_file.unlink()
        return True
    return False


def cache_clear(prefix: str = None) -> int:
    """Clear cache entries, optionally by prefix. Returns count deleted."""
    if not settings.CACHE_DIR.exists():
        return 0
    count = 0
    for cache_file in settings.CACHE_DIR.iterdir():
        if cache_file.is_file() and (
            prefix is None or cache_file.stem.startswith(prefix)
        ):
            cache_file.unlink()
            count += 1
    return count
