import hashlib
import json
import pickle
import time
from functools import wraps
from typing import Callable

from app.config.settings import settings
from app.utils.logging import logger

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    payload = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    hash_digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"{prefix}_{hash_digest}"

def disk_cache(ttl_seconds: int = 3600, use_json: bool = True, prefix: str = None):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Ensure cache directory exists
            if not settings.CACHE_DIR.exists():
                settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Generate cache key and file path
            key_prefix = prefix or func.__name__
            key = get_cache_key(key_prefix, *args, **kwargs)
            extension = ".json" if use_json else ".pkl"
            cache_file = settings.CACHE_DIR / (key + extension)

            # Check if cache exists and is valid based on TTL
            if cache_file.exists():
                file_age = time.time() - cache_file.stat().st_mtime
                if file_age < ttl_seconds:
                    try:
                        logger.debug(f"Cache HIT for {key_prefix}")
                        if use_json:
                            with open(cache_file, "r", encoding="utf-8") as f:
                                return json.load(f)
                        else:
                            with open(cache_file, "rb") as f:
                                return pickle.load(f)
                    except Exception as e:
                        logger.warning(f"Cache read failed, regenerating: {e}")
                else:
                    logger.debug(f"Cache expired for {key_prefix}")
                    try:
                        cache_file.unlink()
                        logger.debug(f"Removed expired cache file: {cache_file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to remove expired cache file {cache_file.name}: {e}")
            # Call the actual function if cache miss or read fails
            result = await func(*args, **kwargs)

            # Save the result to cache
            try:
                if use_json:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False)
                else:
                    with open(cache_file, "wb") as f:
                        pickle.dump(result, f)
            except Exception as e:
                logger.error(f"Failed to write cache: {e}")

            return result
        return wrapper
    return decorator
