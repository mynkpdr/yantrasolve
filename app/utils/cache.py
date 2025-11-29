import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Optional, Tuple

from app.config.settings import settings
from app.utils.logging import logger


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generates a cache key based on the prefix and arguments.

    Args:
        prefix: The prefix for the cache key (e.g., function name or identifier).
        *args: Positional arguments to consider for the cache key.
        **kwargs: Keyword arguments to consider for the cache key.

    Returns:
        A unique cache key string.
    """
    payload = json.dumps(
        {"args": list(args), "kwargs": kwargs}, sort_keys=True, default=str
    )
    hash_digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"{prefix}_{hash_digest}"


def get_cache_path(key: str, use_json: bool = True) -> Path:
    """Get the file path for a cache key."""
    settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    extension = ".json" if use_json else ".pkl"
    return settings.CACHE_DIR / (key + extension)


def cache_get(
    key: str, ttl_seconds: int = 3600, use_json: bool = True
) -> Tuple[bool, Optional[Any]]:
    """
    Check if a valid cache entry exists and return it.

    Args:
        key: The cache key to look up.
        ttl_seconds: Time-to-live in seconds (default: 1 hour).
        use_json: Use JSON format (True) or pickle (False).

    Returns:
        Tuple of (cache_hit: bool, data: Any or None)

    Usage:
        cache_key = get_cache_key("my_function", arg1, arg2)
        hit, data = cache_get(cache_key, ttl_seconds=3600)
        if hit:
            return data
        else:
            # compute result
            result = expensive_operation()
            cache_set(cache_key, result)
            return result
    """
    cache_file = get_cache_path(key, use_json)

    if not cache_file.exists():
        logger.debug(f"[cache] MISS - key not found: {key[:50]}...")
        return False, None

    # Check TTL
    age = time.time() - cache_file.stat().st_mtime
    if age >= ttl_seconds:
        logger.debug(
            f"[cache] MISS - expired ({age:.1f}s > {ttl_seconds}s): {key[:50]}..."
        )
        cache_file.unlink(missing_ok=True)
        return False, None

    # Read cached data
    try:
        if use_json:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            with open(cache_file, "rb") as f:
                data = pickle.load(f)

        logger.debug(f"[cache] HIT ({age:.1f}s old): {key[:50]}...")
        return True, data

    except Exception as e:
        logger.warning(f"[cache] Failed to read cache: {e}")
        cache_file.unlink(missing_ok=True)
        return False, None


def cache_set(key: str, data: Any, use_json: bool = True) -> bool:
    """
    Store data in the cache.

    Args:
        key: The cache key.
        data: The data to cache.
        use_json: Use JSON format (True) or pickle (False).

    Returns:
        True if successfully cached, False otherwise.

    Usage:
        cache_key = get_cache_key("my_function", arg1, arg2)
        result = expensive_operation()
        cache_set(cache_key, result)
    """
    cache_file = get_cache_path(key, use_json)

    try:
        if use_json:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        else:
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)

        logger.debug(f"[cache] SET: {key[:50]}...")
        return True

    except Exception as e:
        logger.error(f"[cache] Failed to write cache: {e}")
        return False


def cache_delete(key: str, use_json: bool = True) -> bool:
    """
    Delete a cache entry.

    Args:
        key: The cache key to delete.
        use_json: Use JSON format (True) or pickle (False).

    Returns:
        True if deleted, False if not found.
    """
    cache_file = get_cache_path(key, use_json)

    if cache_file.exists():
        cache_file.unlink()
        logger.debug(f"[cache] DELETE: {key[:50]}...")
        return True
    return False


def cache_clear(prefix: str = None) -> int:
    """
    Clear cache entries, optionally filtered by prefix.

    Args:
        prefix: If provided, only delete entries starting with this prefix.

    Returns:
        Number of entries deleted.
    """
    if not settings.CACHE_DIR.exists():
        return 0

    count = 0
    for cache_file in settings.CACHE_DIR.iterdir():
        if cache_file.is_file():
            if prefix is None or cache_file.stem.startswith(prefix):
                cache_file.unlink()
                count += 1

    logger.debug(f"[cache] CLEAR: {count} entries deleted (prefix={prefix})")
    return count
