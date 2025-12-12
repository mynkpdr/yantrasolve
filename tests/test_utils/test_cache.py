"""Tests for app/utils/cache.py"""

import json
import pickle
import time
from unittest.mock import MagicMock

from app.utils.cache import (
    get_cache_key,
    get_cache_path,
    cache_get,
    cache_set,
    cache_delete,
    cache_clear,
)


class TestGetCacheKey:
    """Test cases for get_cache_key function."""

    def test_generates_key_with_prefix(self):
        """Test that key includes the prefix."""
        key = get_cache_key("my_function", "arg1", "arg2")
        assert key.startswith("my_function_")

    def test_different_args_different_keys(self):
        """Test that different arguments produce different keys."""
        key1 = get_cache_key("func", "arg1")
        key2 = get_cache_key("func", "arg2")
        assert key1 != key2

    def test_same_args_same_keys(self):
        """Test that same arguments produce same keys."""
        key1 = get_cache_key("func", "arg1", kwarg="value")
        key2 = get_cache_key("func", "arg1", kwarg="value")
        assert key1 == key2

    def test_kwargs_order_independent(self):
        """Test that kwargs order doesn't affect key."""
        key1 = get_cache_key("func", a=1, b=2)
        key2 = get_cache_key("func", b=2, a=1)
        assert key1 == key2

    def test_handles_complex_args(self):
        """Test handling of complex arguments."""
        key = get_cache_key("func", {"nested": "dict"}, [1, 2, 3])
        assert isinstance(key, str)
        assert key.startswith("func_")

    def test_key_is_valid_filename(self):
        """Test that key is valid for use as filename."""
        key = get_cache_key("func", "arg with spaces", special="chars!@#")
        # Key should be hex characters after prefix
        assert "_" in key
        prefix, hash_part = key.rsplit("_", 1)
        assert all(c in "0123456789abcdef" for c in hash_part)


class TestGetCachePath:
    """Test cases for get_cache_path function."""

    def test_returns_json_path(self, mocker, tmp_path):
        """Test that JSON extension is used by default."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        path = get_cache_path("test_key", use_json=True)

        assert path.suffix == ".json"
        assert path.stem == "test_key"

    def test_returns_pickle_path(self, mocker, tmp_path):
        """Test that pickle extension is used when specified."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        path = get_cache_path("test_key", use_json=False)

        assert path.suffix == ".pkl"

    def test_creates_cache_directory(self, mocker, tmp_path):
        """Test that cache directory is created if it doesn't exist."""
        cache_dir = tmp_path / "new_cache_dir"
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = cache_dir
        mocker.patch("app.utils.cache.settings", mock_settings)

        get_cache_path("test_key")

        assert cache_dir.exists()


class TestCacheGet:
    """Test cases for cache_get function."""

    def test_cache_miss_no_file(self, mocker, tmp_path):
        """Test cache miss when file doesn't exist."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        hit, data = cache_get("nonexistent_key")

        assert hit is False
        assert data is None

    def test_cache_hit_valid(self, mocker, tmp_path):
        """Test cache hit with valid, non-expired data."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        # Create cache file
        cache_file = tmp_path / "test_key.json"
        cache_file.write_text(json.dumps({"data": "value"}))

        hit, data = cache_get("test_key", ttl_seconds=3600)

        assert hit is True
        assert data == {"data": "value"}

    def test_cache_expired(self, mocker, tmp_path):
        """Test cache miss when data is expired."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        # Create cache file with old modification time
        cache_file = tmp_path / "test_key.json"
        cache_file.write_text(json.dumps({"data": "old"}))

        # Set file mtime to 2 hours ago
        old_time = time.time() - 7200
        import os

        os.utime(cache_file, (old_time, old_time))

        hit, data = cache_get("test_key", ttl_seconds=3600)

        assert hit is False
        assert data is None
        # Expired file should be deleted
        assert not cache_file.exists()

    def test_cache_pickle(self, mocker, tmp_path):
        """Test cache with pickle format."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        # Create pickle cache file
        cache_file = tmp_path / "test_key.pkl"
        with open(cache_file, "wb") as f:
            pickle.dump({"complex": [1, 2, 3]}, f)

        hit, data = cache_get("test_key", use_json=False)

        assert hit is True
        assert data == {"complex": [1, 2, 3]}

    def test_cache_corrupted_file(self, mocker, tmp_path):
        """Test handling of corrupted cache file."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        # Create corrupted cache file
        cache_file = tmp_path / "test_key.json"
        cache_file.write_text("not valid json {{{")

        hit, data = cache_get("test_key")

        assert hit is False
        assert data is None
        # Corrupted file should be deleted
        assert not cache_file.exists()


class TestCacheSet:
    """Test cases for cache_set function."""

    def test_set_json_data(self, mocker, tmp_path):
        """Test setting JSON-serializable data."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        result = cache_set("test_key", {"key": "value"})

        assert result is True

        cache_file = tmp_path / "test_key.json"
        assert cache_file.exists()

        with open(cache_file) as f:
            data = json.load(f)
        assert data == {"key": "value"}

    def test_set_pickle_data(self, mocker, tmp_path):
        """Test setting data with pickle format."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        result = cache_set("test_key", {"key": "value"}, use_json=False)

        assert result is True

        cache_file = tmp_path / "test_key.pkl"
        assert cache_file.exists()

        with open(cache_file, "rb") as f:
            data = pickle.load(f)
        assert data == {"key": "value"}

    def test_set_overwrites_existing(self, mocker, tmp_path):
        """Test that setting overwrites existing cache."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        cache_set("test_key", {"version": 1})
        cache_set("test_key", {"version": 2})

        hit, data = cache_get("test_key")
        assert data == {"version": 2}


class TestCacheDelete:
    """Test cases for cache_delete function."""

    def test_delete_existing(self, mocker, tmp_path):
        """Test deleting existing cache entry."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        cache_file = tmp_path / "test_key.json"
        cache_file.write_text("{}")

        result = cache_delete("test_key")

        assert result is True
        assert not cache_file.exists()

    def test_delete_nonexistent(self, mocker, tmp_path):
        """Test deleting nonexistent cache entry."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        result = cache_delete("nonexistent_key")

        assert result is False


class TestCacheClear:
    """Test cases for cache_clear function."""

    def test_clear_all(self, mocker, tmp_path):
        """Test clearing all cache entries."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        # Create multiple cache files
        (tmp_path / "key1.json").write_text("{}")
        (tmp_path / "key2.json").write_text("{}")
        (tmp_path / "key3.pkl").write_bytes(b"")

        count = cache_clear()

        assert count == 3
        assert len(list(tmp_path.iterdir())) == 0

    def test_clear_with_prefix(self, mocker, tmp_path):
        """Test clearing cache entries with prefix."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        # Create cache files with different prefixes
        (tmp_path / "fetch_key1.json").write_text("{}")
        (tmp_path / "fetch_key2.json").write_text("{}")
        (tmp_path / "download_key1.json").write_text("{}")

        count = cache_clear(prefix="fetch")

        assert count == 2
        assert (tmp_path / "download_key1.json").exists()

    def test_clear_empty_cache(self, mocker, tmp_path):
        """Test clearing empty cache directory."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path
        mocker.patch("app.utils.cache.settings", mock_settings)

        count = cache_clear()

        assert count == 0

    def test_clear_nonexistent_directory(self, mocker, tmp_path):
        """Test clearing nonexistent cache directory."""
        mock_settings = MagicMock()
        mock_settings.CACHE_DIR = tmp_path / "nonexistent"
        mocker.patch("app.utils.cache.settings", mock_settings)

        count = cache_clear()

        assert count == 0
