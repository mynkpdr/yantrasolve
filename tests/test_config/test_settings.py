"""Tests for app/config/settings.py"""

import os
from pathlib import Path
from unittest.mock import patch


from app.config.settings import Config


class TestConfig:
    """Test cases for the Config settings class."""

    def test_default_values(self):
        """Test that default values are set correctly when no env vars are present."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()

            assert config.HOST == "0.0.0.0"
            assert config.PORT == 8000
            assert config.DEBUG is True
            assert config.TEMP_DIR == Path("/tmp/quiz_files")
            assert config.CACHE_DIR == Path("/tmp/quiz_cache")
            assert config.LOGS_DIR == Path("/tmp/quiz_logs")
            assert config.LLM_MODEL == "gpt-4.1"
            assert config.LLM_PROVIDER == "openai"
            assert config.LLM_TEMPERATURE == 0.1
            assert config.BROWSER_PAGE_TIMEOUT == 10000
            assert config.QUIZ_TIMEOUT_SECONDS == 180

    def test_env_variables_override(self):
        """Test that environment variables override default values."""
        env_vars = {
            "SECRET_KEY": "test-secret",
            "STUDENT_EMAIL": "test@example.com",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "DEBUG": "true",
            "TEMP_DIR": "/custom/temp",
            "CACHE_DIR": "/custom/cache",
            "LOGS_DIR": "/custom/logs",
            "LLM_API_KEY": "test-api-key",
            "LLM_BASE_URL": "https://custom-api.com/v1",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()

            assert config.SECRET_KEY == "test-secret"
            assert config.STUDENT_EMAIL == "test@example.com"
            assert config.HOST == "127.0.0.1"
            assert config.PORT == 9000
            assert config.DEBUG is True
            assert config.TEMP_DIR == Path("/custom/temp")
            assert config.CACHE_DIR == Path("/custom/cache")
            assert config.LOGS_DIR == Path("/custom/logs")
            assert config.LLM_API_KEY == "test-api-key"
            assert config.LLM_BASE_URL == "https://custom-api.com/v1"

    def test_debug_flag_true_variations(self):
        """Test various truthy values for DEBUG flag."""
        for value in ["true", "True", "TRUE", "1", "t"]:
            with patch.dict(os.environ, {"DEBUG": value}, clear=True):
                config = Config()
                assert config.DEBUG is True, f"DEBUG should be True for '{value}'"

    def test_debug_flag_false_variations(self):
        """Test various falsy values for DEBUG flag."""
        # Note: pydantic-settings only accepts specific boolean strings
        for value in ["false", "False", "FALSE", "0", "off", "no"]:
            with patch.dict(os.environ, {"DEBUG": value}, clear=True):
                config = Config()
                assert config.DEBUG is False, f"DEBUG should be False for '{value}'"

    def test_port_integer_conversion(self):
        """Test that PORT is correctly converted to integer."""
        with patch.dict(os.environ, {"PORT": "8080"}, clear=True):
            config = Config()
            assert config.PORT == 8080
            assert isinstance(config.PORT, int)

    def test_path_types(self):
        """Test that directory paths are Path objects."""
        config = Config()

        assert isinstance(config.TEMP_DIR, Path)
        assert isinstance(config.CACHE_DIR, Path)
        assert isinstance(config.LOGS_DIR, Path)

    def test_gemini_api_keys_list(self):
        """Test GEMINI_API_KEYS parsing."""
        # Test with JSON array format
        with patch.dict(
            os.environ, {"GEMINI_API_KEYS": '["key1","key2","key3"]'}, clear=True
        ):
            config = Config()
            assert config.GEMINI_API_KEYS == ["key1", "key2", "key3"]

    def test_default_llm_settings(self):
        """Test default LLM configuration values."""
        config = Config()

        assert config.LLM_MODEL == "gpt-4.1"
        assert config.LLM_PROVIDER == "openai"
        assert config.LLM_TEMPERATURE == 0.1

    def test_timeout_settings(self):
        """Test timeout configuration values."""
        config = Config()

        assert config.BROWSER_PAGE_TIMEOUT == 10000
        assert config.QUIZ_TIMEOUT_SECONDS == 180

    def test_config_model_config(self):
        """Test that model_config is properly set for pydantic-settings."""
        config = Config()

        # Check that the config class has proper pydantic settings
        assert hasattr(config, "model_config")
