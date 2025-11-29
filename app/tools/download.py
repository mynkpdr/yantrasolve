import os
import re
import mimetypes
from urllib.parse import urlparse, unquote
import httpx

from langchain_core.tools import tool
from app.config.settings import settings
from app.utils.logging import logger
from app.utils.cache import get_cache_key, cache_get, cache_set


@tool
def download_file_tool(url: str) -> str:
    """
    Downloads a file from a URL and saves it locally in the configured temp directory.

    Args:
        url: The URL of the file to download

    Returns:
        The local file path where the file was saved, or an error message
    """
    # Check cache first
    cache_key = get_cache_key("download_file", url)
    hit, cached_data = cache_get(cache_key, ttl_seconds=3600)
    if hit:
        logger.info(f"Cache hit for file: {url}")
        return cached_data

    max_size_mb = 50
    try:
        logger.info(f"Downloading: {url}")

        with httpx.Client(timeout=60.0) as client:
            with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()

                # ----- SIZE CHECK -----
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_size_mb * 1024 * 1024:
                    return f"File too large: {int(content_length)/(1024*1024):.2f} MB (limit {max_size_mb} MB)"

                # ----- FILENAME RESOLUTION -----
                filename = None

                # Priority A: Content-Disposition header
                content_disposition = response.headers.get("Content-Disposition")
                if content_disposition:
                    match = re.search(
                        r'filename\*?=(?:UTF-8\'\')?(?:"([^"]*)"|([^;]*))',
                        content_disposition,
                    )
                    if match:
                        filename = match.group(1) or match.group(2)

                # Priority B: URL path
                if not filename:
                    parsed = urlparse(str(response.url))
                    path_name = os.path.basename(unquote(parsed.path))
                    if path_name and "." in path_name:
                        filename = path_name

                # Priority C: fallback using content-type
                if not filename:
                    content_type = response.headers.get("Content-Type", "").split(";")[
                        0
                    ]
                    ext = mimetypes.guess_extension(content_type) or ".bin"
                    filename = f"downloaded_file{ext}"

                # Sanitize
                filename = os.path.basename(
                    filename.replace("/", "_").replace("..", "__")
                )
                filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

                local_path = settings.TEMP_DIR / filename

                # ----- STREAM & WRITE -----
                downloaded_size = 0
                chunk_size = 1024 * 1024

                with open(local_path, "wb") as file:
                    for chunk in response.iter_bytes(chunk_size):
                        downloaded_size += len(chunk)
                        if downloaded_size > max_size_mb * 1024 * 1024:
                            return f"Download aborted: Exceeded {max_size_mb}MB limit."
                        file.write(chunk)

                cache_set(cache_key, str(local_path.absolute()))

                return str(local_path.absolute())

    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return f"Failed to download {url}. Error: {str(e)}"
