"""File download tool with caching and streaming support."""

import os
import re
import mimetypes
from urllib.parse import urlparse, unquote
import httpx
from langchain_core.tools import tool
from app.config.settings import settings
from app.utils.logging import logger
from app.utils.cache import get_cache_key, cache_get, cache_set

CHUNK_SIZE = 1024 * 1024  # 1MB


def _get_filename(response: httpx.Response) -> str:
    """Extract filename from response headers or URL."""
    # Try Content-Disposition header
    content_disposition = response.headers.get("Content-Disposition")
    if content_disposition:
        match = re.search(
            r'filename\*?=(?:UTF-8\'\')?(?:"([^"]*)"|([^;]*))', content_disposition
        )
        if match:
            return match.group(1) or match.group(2)

    # Try URL path
    parsed = urlparse(str(response.url))
    path_name = os.path.basename(unquote(parsed.path))
    if path_name and "." in path_name:
        return path_name

    # Fallback: use content-type
    content_type = response.headers.get("Content-Type", "").split(";")[0]
    ext = mimetypes.guess_extension(content_type) or ".bin"
    return f"downloaded_file{ext}"


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem use."""
    filename = os.path.basename(filename.replace("/", "_").replace("..", "__"))
    return re.sub(r'[<>:"/\\|?*]', "_", filename)


@tool
def download_file_tool(url: str) -> str:
    """Download a file from URL to temp directory.

    Args:
        url: The URL of the file to download

    Returns:
        Local file path where file was saved, or error message
    """
    # Check cache
    cache_key = get_cache_key("download_file", url)
    hit, cached_data = cache_get(cache_key, ttl_seconds=3600)
    if hit:
        logger.info(f"Cache hit for file: {url}")
        return cached_data

    try:
        logger.info(f"Downloading: {url}")
        with httpx.Client(timeout=60.0) as client:
            with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()

                # Check size limit
                content_length = response.headers.get("Content-Length")
                if (
                    content_length
                    and int(content_length) > settings.MAX_FILE_SIZE_MB * 1024 * 1024
                ):
                    return f"File too large: {int(content_length) / (1024 * 1024):.2f} MB (limit {settings.MAX_FILE_SIZE_MB} MB)"

                filename = _sanitize_filename(_get_filename(response))
                local_path = settings.TEMP_DIR / filename

                # Stream and write
                downloaded_size = 0
                with open(local_path, "wb") as file:
                    for chunk in response.iter_bytes(CHUNK_SIZE):
                        downloaded_size += len(chunk)
                        if downloaded_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                            return f"Download aborted: Exceeded {settings.MAX_FILE_SIZE_MB}MB limit."
                        file.write(chunk)

                cache_set(cache_key, str(local_path.absolute()))
                return str(local_path.absolute())

    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return f"Failed to download {url}. Error: {str(e)}"
