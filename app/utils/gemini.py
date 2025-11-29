"""
Shared Gemini utilities - API key management and file handling.
"""

import base64
import mimetypes
import os
from pathlib import Path
from typing import List

from openai import OpenAI

from app.config.settings import settings
from app.utils.logging import logger


# Gemini API configuration
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_MODEL = "gemini-2.5-flash-lite"


class GeminiKeyManager:
    """Manages multiple Gemini API keys with round-robin rotation."""

    def __init__(self):
        self.keys = self._load_keys()
        self.current_index = 0

    def _load_keys(self) -> List[str]:
        """Load Gemini API keys from environment variables."""
        keys = []
        # Check for GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3
        for i in range(1, 4):
            key = getattr(settings, f"GEMINI_API_KEY_{i}", None)
            if key and key != "your-gemini-api-key":
                keys.append(key)
                logger.debug(f"Loaded GEMINI_API_KEY_{i}")

        # Fallback to single key if no numbered keys found
        if not keys:
            single_key = os.getenv("GEMINI_API_KEY") or settings.LLM_API_KEY
            if single_key and single_key not in (
                "your-gemini-api-key",
                "your-openai-api-key",
            ):
                keys.append(single_key)

        logger.info(f"Loaded {len(keys)} Gemini API key(s) for round-robin")
        return keys

    def get_next_key(self) -> str:
        """Get the next API key in round-robin fashion."""
        if not self.keys:
            raise ValueError("No Gemini API keys configured")

        key = self.keys[self.current_index]
        logger.debug(f"Using Gemini key index: {self.current_index}")
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key


# Global singleton instance
gemini_key_manager = GeminiKeyManager()


def get_gemini_client() -> OpenAI:
    """Create and return a Gemini client using OpenAI-compatible API with round-robin key."""
    api_key = gemini_key_manager.get_next_key()
    return OpenAI(base_url=GEMINI_BASE_URL, api_key=api_key, timeout=30)


# =============================================================================
# File utilities for multimodal LLM
# =============================================================================

# MIME type fallback mappings
MIME_TYPE_FALLBACKS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".pdf": "application/pdf",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".opus": "audio/opus",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".csv": "text/csv",
    ".json": "application/json",
    ".txt": "text/plain",
    ".html": "text/html",
    ".xml": "text/xml",
}


def get_mime_type(file_path: str) -> str:
    """
    Determine the MIME type of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        MIME type string (e.g., 'image/png', 'application/pdf')
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type

    ext = Path(file_path).suffix.lower()
    return MIME_TYPE_FALLBACKS.get(ext, "application/octet-stream")


def encode_file_to_base64(file_path: str) -> str:
    """
    Read a file and encode its contents to base64.

    Args:
        file_path: Path to the file

    Returns:
        Base64 encoded string of file contents
    """
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def create_data_uri(file_path: str) -> str:
    """
    Create a data URI from a file for use with Gemini API.

    Args:
        file_path: Path to the file

    Returns:
        Data URI string (e.g., 'data:image/png;base64,...')
    """
    mime_type = get_mime_type(file_path)
    base64_data = encode_file_to_base64(file_path)
    return f"data:{mime_type};base64,{base64_data}"


def is_text_file(file_path: str) -> bool:
    """Check if file is a text-based file that should be read as text."""
    mime_type = get_mime_type(file_path)
    text_types = ["text/", "application/json", "application/xml"]
    return any(mime_type.startswith(t) or mime_type == t for t in text_types)
