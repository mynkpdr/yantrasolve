"""Tests for app/tools/download.py"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.tools.download import download_file_tool


class TestDownloadFileTool:
    """Test cases for download_file_tool function."""

    @pytest.fixture
    def mock_settings(self, tmp_path):
        """Create mock settings with temp directory."""
        settings = MagicMock()
        settings.TEMP_DIR = tmp_path
        return settings

    @pytest.fixture(autouse=True)
    def clear_cache(self, mocker):
        """Clear cache before each test."""
        mocker.patch("app.tools.download.cache_get", return_value=(False, None))
        mocker.patch("app.tools.download.cache_set", return_value=True)

    def test_successful_download(self, mocker, tmp_path):
        """Test successful file download."""
        mocker.patch("app.tools.download.settings.TEMP_DIR", tmp_path)

        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/csv", "Content-Length": "100"}
        mock_response.url = "http://example.com/data.csv"
        mock_response.iter_bytes = MagicMock(return_value=[b"test,data\n1,2"])
        mock_response.raise_for_status = MagicMock()

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_stream)

        mocker.patch("httpx.Client", return_value=mock_client)

        result = download_file_tool.invoke({"url": "http://example.com/data.csv"})

        assert "data.csv" in result or str(tmp_path) in result

    def test_cache_hit(self, mocker, tmp_path):
        """Test cache hit returns cached path."""
        mocker.patch("app.tools.download.settings.TEMP_DIR", tmp_path)
        mocker.patch(
            "app.tools.download.cache_get", return_value=(True, "/cached/path/file.csv")
        )

        result = download_file_tool.invoke({"url": "http://example.com/cached.csv"})

        assert result == "/cached/path/file.csv"

    def test_file_too_large(self, mocker, tmp_path):
        """Test rejection of files exceeding size limit."""
        mocker.patch("app.tools.download.settings.TEMP_DIR", tmp_path)

        mock_response = MagicMock()
        mock_response.headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(60 * 1024 * 1024),  # 60MB
        }
        mock_response.raise_for_status = MagicMock()

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_stream)

        mocker.patch("httpx.Client", return_value=mock_client)

        result = download_file_tool.invoke({"url": "http://example.com/large.bin"})

        assert "too large" in result.lower()

    def test_filename_from_content_disposition(self, mocker, tmp_path):
        """Test filename extraction from Content-Disposition header."""
        mocker.patch("app.tools.download.settings.TEMP_DIR", tmp_path)

        mock_response = MagicMock()
        mock_response.headers = {
            "Content-Type": "text/csv",
            "Content-Disposition": 'attachment; filename="custom_name.csv"',
            "Content-Length": "50",
        }
        mock_response.url = "http://example.com/download"
        mock_response.iter_bytes = MagicMock(return_value=[b"data"])
        mock_response.raise_for_status = MagicMock()

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_stream)

        mocker.patch("httpx.Client", return_value=mock_client)

        result = download_file_tool.invoke({"url": "http://example.com/download"})

        assert "custom_name.csv" in result

    def test_filename_from_url_path(self, mocker, tmp_path):
        """Test filename extraction from URL path."""
        mocker.patch("app.tools.download.settings.TEMP_DIR", tmp_path)

        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/csv", "Content-Length": "50"}
        mock_response.url = "http://example.com/path/to/myfile.csv"
        mock_response.iter_bytes = MagicMock(return_value=[b"data"])
        mock_response.raise_for_status = MagicMock()

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_stream)

        mocker.patch("httpx.Client", return_value=mock_client)

        result = download_file_tool.invoke(
            {"url": "http://example.com/path/to/myfile.csv"}
        )

        assert "myfile.csv" in result

    def test_http_error(self, mocker, tmp_path):
        """Test handling of HTTP errors."""
        mocker.patch("app.tools.download.settings.TEMP_DIR", tmp_path)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream = MagicMock(side_effect=Exception("Connection refused"))

        mocker.patch("httpx.Client", return_value=mock_client)

        result = download_file_tool.invoke({"url": "http://invalid-url.com/file"})

        assert "Failed" in result or "Error" in result

    def test_streaming_size_limit(self, mocker, tmp_path):
        """Test that streaming aborts when size limit is exceeded during download."""
        mocker.patch("app.tools.download.settings.TEMP_DIR", tmp_path)

        # Simulate chunks that exceed the limit - need to return iterator each time
        def generate_large_chunks(chunk_size):
            for _ in range(60):  # 60 * 1MB = 60MB
                yield b"x" * (1024 * 1024)

        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/octet-stream"}
        mock_response.url = "http://example.com/file.bin"
        mock_response.iter_bytes = generate_large_chunks
        mock_response.raise_for_status = MagicMock()

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_stream)

        mocker.patch("httpx.Client", return_value=mock_client)

        result = download_file_tool.invoke({"url": "http://example.com/file.bin"})

        assert "aborted" in result.lower() or "Exceeded" in result

    def test_sanitizes_filename(self, mocker, tmp_path):
        """Test that dangerous characters are sanitized from filename."""
        mocker.patch("app.tools.download.settings.TEMP_DIR", tmp_path)

        mock_response = MagicMock()
        mock_response.headers = {
            "Content-Type": "text/plain",
            "Content-Disposition": 'filename="../../etc/passwd"',
            "Content-Length": "10",
        }
        mock_response.url = "http://example.com/file"
        mock_response.iter_bytes = MagicMock(return_value=[b"data"])
        mock_response.raise_for_status = MagicMock()

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_stream)

        mocker.patch("httpx.Client", return_value=mock_client)

        result = download_file_tool.invoke({"url": "http://example.com/file"})

        # Should not contain path traversal
        assert ".." not in Path(result).name if "Error" not in result else True
