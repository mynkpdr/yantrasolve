"""Tests for app/utils/helpers.py"""

import time
from unittest.mock import MagicMock

import pytest

from app.utils.helpers import (
    setup_temp_directory,
    cleanup_temp_files,
    retry_with_backoff,
    hash_content,
)


class TestSetupTempDirectory:
    """Test cases for setup_temp_directory function."""

    def test_creates_directory(self, mocker, tmp_path):
        """Test that temp directory is created."""
        mock_settings = MagicMock()
        mock_settings.TEMP_DIR = tmp_path / "new_temp"
        mocker.patch("app.utils.helpers.settings", mock_settings)

        setup_temp_directory()

        assert mock_settings.TEMP_DIR.exists()

    def test_handles_existing_directory(self, mocker, tmp_path):
        """Test that existing directory is handled gracefully."""
        mock_settings = MagicMock()
        mock_settings.TEMP_DIR = tmp_path
        mocker.patch("app.utils.helpers.settings", mock_settings)

        # Should not raise exception
        setup_temp_directory()

        assert tmp_path.exists()

    def test_creates_nested_directories(self, mocker, tmp_path):
        """Test creation of nested directories."""
        mock_settings = MagicMock()
        mock_settings.TEMP_DIR = tmp_path / "level1" / "level2" / "temp"
        mocker.patch("app.utils.helpers.settings", mock_settings)

        setup_temp_directory()

        assert mock_settings.TEMP_DIR.exists()


class TestCleanupTempFiles:
    """Test cases for cleanup_temp_files function."""

    def test_removes_old_files(self, mocker, tmp_path):
        """Test that old files are removed."""
        mock_settings = MagicMock()
        mock_settings.TEMP_DIR = tmp_path
        mocker.patch("app.utils.helpers.settings", mock_settings)

        # Create an old file
        old_file = tmp_path / "old_file.txt"
        old_file.write_text("old content")

        # Set modification time to 2 hours ago
        import os

        old_time = time.time() - 7200
        os.utime(old_file, (old_time, old_time))

        removed = cleanup_temp_files(older_than=3600)

        assert removed == 1
        assert not old_file.exists()

    def test_keeps_recent_files(self, mocker, tmp_path):
        """Test that recent files are kept."""
        mock_settings = MagicMock()
        mock_settings.TEMP_DIR = tmp_path
        mocker.patch("app.utils.helpers.settings", mock_settings)

        # Create a recent file
        recent_file = tmp_path / "recent_file.txt"
        recent_file.write_text("recent content")

        removed = cleanup_temp_files(older_than=3600)

        assert removed == 0
        assert recent_file.exists()

    def test_handles_nonexistent_directory(self, mocker, tmp_path):
        """Test handling of nonexistent directory."""
        mock_settings = MagicMock()
        mock_settings.TEMP_DIR = tmp_path / "nonexistent"
        mocker.patch("app.utils.helpers.settings", mock_settings)

        removed = cleanup_temp_files()

        assert removed == 0

    def test_removes_files_in_subdirectories(self, mocker, tmp_path):
        """Test that files in subdirectories are also cleaned."""
        mock_settings = MagicMock()
        mock_settings.TEMP_DIR = tmp_path
        mocker.patch("app.utils.helpers.settings", mock_settings)

        # Create subdirectory with old file
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        old_file = subdir / "old_file.txt"
        old_file.write_text("content")

        # Set modification time to 2 hours ago
        import os

        old_time = time.time() - 7200
        os.utime(old_file, (old_time, old_time))

        removed = cleanup_temp_files(older_than=3600)

        assert removed == 1
        assert not old_file.exists()


class TestRetryWithBackoff:
    """Test cases for retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Test successful execution on first try."""
        call_count = 0

        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_with_backoff(success_func)

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry behavior on failure."""
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await retry_with_backoff(
            fail_then_succeed,
            max_retries=3,
            base_delay=0.01,
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries."""

        async def always_fail():
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            await retry_with_backoff(
                always_fail,
                max_retries=2,
                base_delay=0.01,
            )

    @pytest.mark.asyncio
    async def test_specific_exceptions(self):
        """Test retry only on specific exceptions."""
        call_count = 0

        async def fail_with_type_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TypeError("Type error")
            raise ValueError("Value error")

        # Should not retry on TypeError if only catching ValueError
        with pytest.raises(TypeError):
            await retry_with_backoff(
                fail_with_type_error,
                max_retries=3,
                base_delay=0.01,
                exceptions=(ValueError,),
            )

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_backoff_delay_increases(self):
        """Test that delay increases with each retry."""
        call_times = []

        async def track_timing():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Error")
            return "success"

        await retry_with_backoff(
            track_timing,
            max_retries=3,
            base_delay=0.05,
            max_delay=1.0,
        )

        # Check that delays are increasing
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Second delay should be roughly double the first (with jitter)
            assert delay2 >= delay1 * 1.5  # Allow for jitter


class TestHashContent:
    """Test cases for hash_content function."""

    def test_string_content(self):
        """Test hashing string content."""
        result = hash_content("test string")

        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length

    def test_same_content_same_hash(self):
        """Test that same content produces same hash."""
        hash1 = hash_content("identical content")
        hash2 = hash_content("identical content")

        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Test that different content produces different hash."""
        hash1 = hash_content("content 1")
        hash2 = hash_content("content 2")

        assert hash1 != hash2

    def test_handles_complex_types(self):
        """Test hashing of complex types."""
        result = hash_content({"key": "value", "nested": [1, 2, 3]})

        assert isinstance(result, str)
        assert len(result) == 64

    def test_handles_none(self):
        """Test hashing None value."""
        result = hash_content(None)

        assert isinstance(result, str)
        assert len(result) == 64
