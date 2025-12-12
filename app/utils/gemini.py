"""Gemini API utilities - key management and file handling for multimodal LLM."""

import base64
import mimetypes
from pathlib import Path
from openai import OpenAI
from app.config.settings import settings
from app.utils.logging import logger

# Gemini API configuration
GEMINI_BASE_URL = settings.GEMINI_BASE_URL

# MIME type fallbacks for common file types
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


class GeminiKeyManager:
    """Round-robin API key rotation for Gemini."""

    def __init__(self):
        self.keys = [k for k in settings.GEMINI_API_KEYS if k]
        self.current_index = 0
        logger.info(f"Loaded {len(self.keys)} Gemini API key(s)")

    def get_next_key(self) -> str:
        """Get next API key in round-robin fashion."""
        if not self.keys:
            raise ValueError("No Gemini API keys configured")
        key = self.keys[self.current_index]
        logger.debug(f"Using Gemini key index: {self.current_index}")
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key


gemini_key_manager = GeminiKeyManager()


def get_gemini_client() -> OpenAI:
    """Create Gemini client using OpenAI-compatible API with round-robin key."""
    return OpenAI(
        base_url=GEMINI_BASE_URL, api_key=gemini_key_manager.get_next_key(), timeout=30
    )


def get_mime_type(file_path: str) -> str:
    """Determine MIME type from file extension."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    return MIME_TYPE_FALLBACKS.get(
        Path(file_path).suffix.lower(), "application/octet-stream"
    )


def encode_file_to_base64(file_path: str) -> str:
    """Read and encode file to base64."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def create_data_uri(file_path: str) -> str:
    """Create data URI from file for Gemini API."""
    return f"data:{get_mime_type(file_path)};base64,{encode_file_to_base64(file_path)}"


def is_text_file(file_path: str) -> bool:
    """Check if file should be read as text."""
    mime_type = get_mime_type(file_path)
    return any(
        mime_type.startswith(t) or mime_type == t
        for t in ["text/", "application/json", "application/xml"]
    )
