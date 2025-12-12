"""Tests for app/utils/gemini.py"""

import base64
from unittest.mock import MagicMock

import pytest

from app.utils.gemini import (
    GeminiKeyManager,
    get_gemini_client,
    get_mime_type,
    encode_file_to_base64,
    create_data_uri,
    is_text_file,
    GEMINI_BASE_URL,
)


class TestGeminiKeyManager:
    """Test cases for GeminiKeyManager class."""

    def test_init_loads_keys(self, mocker):
        """Test that initialization loads keys from settings."""
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEYS = ["key1", "key2", "key3"]
        mocker.patch("app.utils.gemini.settings", mock_settings)

        manager = GeminiKeyManager()

        assert len(manager.keys) == 3
        assert manager.current_index == 0

    def test_init_filters_empty_keys(self, mocker):
        """Test that empty keys are filtered out."""
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEYS = ["key1", "", "key2", None, "key3"]
        mocker.patch("app.utils.gemini.settings", mock_settings)

        manager = GeminiKeyManager()

        # Only non-empty, non-None keys should be kept
        # Note: None might not pass the filter, but "" should be filtered
        assert "" not in manager.keys

    def test_get_next_key_round_robin(self, mocker):
        """Test round-robin key rotation."""
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEYS = ["key1", "key2", "key3"]
        mocker.patch("app.utils.gemini.settings", mock_settings)

        manager = GeminiKeyManager()

        assert manager.get_next_key() == "key1"
        assert manager.get_next_key() == "key2"
        assert manager.get_next_key() == "key3"
        assert manager.get_next_key() == "key1"  # Wraps around

    def test_get_next_key_no_keys(self, mocker):
        """Test error when no keys are configured."""
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEYS = []
        mocker.patch("app.utils.gemini.settings", mock_settings)

        manager = GeminiKeyManager()

        with pytest.raises(ValueError, match="No Gemini API keys"):
            manager.get_next_key()

    def test_single_key(self, mocker):
        """Test with single key."""
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEYS = ["only_key"]
        mocker.patch("app.utils.gemini.settings", mock_settings)

        manager = GeminiKeyManager()

        assert manager.get_next_key() == "only_key"
        assert manager.get_next_key() == "only_key"


class TestGetGeminiClient:
    """Test cases for get_gemini_client function."""

    def test_creates_openai_client(self, mocker):
        """Test that OpenAI client is created with correct parameters."""
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEYS = ["test_key"]
        mocker.patch("app.utils.gemini.settings", mock_settings)

        mock_openai = MagicMock()
        mocker.patch("app.utils.gemini.OpenAI", return_value=mock_openai)

        # Reset the manager
        mocker.patch("app.utils.gemini.gemini_key_manager", GeminiKeyManager())

        get_gemini_client()

        from app.utils.gemini import OpenAI

        OpenAI.assert_called_once()
        call_kwargs = OpenAI.call_args.kwargs
        assert call_kwargs["base_url"] == GEMINI_BASE_URL
        assert call_kwargs["timeout"] == 30


class TestGetMimeType:
    """Test cases for get_mime_type function."""

    def test_known_extensions(self):
        """Test MIME types for known extensions."""
        test_cases = [
            ("file.png", "image/png"),
            ("file.jpg", "image/jpeg"),
            ("file.jpeg", "image/jpeg"),
            ("file.pdf", "application/pdf"),
            ("file.mp3", "audio/mpeg"),
            ("file.mp4", "video/mp4"),
            ("file.csv", "text/csv"),
            ("file.json", "application/json"),
            ("file.txt", "text/plain"),
        ]

        for filename, expected_mime in test_cases:
            result = get_mime_type(filename)
            assert result == expected_mime, f"Failed for {filename}"

    def test_unknown_extension(self):
        """Test fallback for unknown extensions."""
        result = get_mime_type("file.xyz123")
        assert result == "application/octet-stream"

    def test_case_insensitive(self):
        """Test that extension matching is case insensitive."""
        result = get_mime_type("file.PNG")
        assert result == "image/png"


class TestEncodeFileToBase64:
    """Test cases for encode_file_to_base64 function."""

    def test_encodes_file(self, tmp_path):
        """Test that file is correctly encoded to base64."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Hello, World!")

        result = encode_file_to_base64(str(test_file))

        decoded = base64.b64decode(result)
        assert decoded == b"Hello, World!"

    def test_encodes_binary_file(self, tmp_path):
        """Test encoding of binary file."""
        test_file = tmp_path / "test.bin"
        binary_data = bytes(range(256))
        test_file.write_bytes(binary_data)

        result = encode_file_to_base64(str(test_file))

        decoded = base64.b64decode(result)
        assert decoded == binary_data


class TestCreateDataUri:
    """Test cases for create_data_uri function."""

    def test_creates_valid_data_uri(self, tmp_path):
        """Test creation of valid data URI."""
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"\x89PNG\r\n")

        result = create_data_uri(str(test_file))

        assert result.startswith("data:image/png;base64,")

    def test_data_uri_format(self, tmp_path):
        """Test data URI format is correct."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')

        result = create_data_uri(str(test_file))

        assert result.startswith("data:")
        assert ";base64," in result


class TestIsTextFile:
    """Test cases for is_text_file function."""

    def test_text_files(self):
        """Test detection of text files."""
        text_files = ["file.txt", "file.csv", "file.json", "file.html", "file.xml"]

        for filename in text_files:
            assert is_text_file(filename) is True, f"Failed for {filename}"

    def test_binary_files(self):
        """Test detection of binary files."""
        binary_files = ["file.png", "file.jpg", "file.pdf", "file.mp3", "file.mp4"]

        for filename in binary_files:
            assert is_text_file(filename) is False, f"Failed for {filename}"

    def test_unknown_extension(self):
        """Test unknown extensions are treated as binary."""
        assert is_text_file("file.xyz") is False
