"""
Pytest configuration and shared fixtures.

This module provides common fixtures used across all test modules.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))


# =============================================================================
# Async Configuration
# =============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Temporary Directory Fixtures
# =============================================================================


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def mock_settings(tmp_path: Path, mocker):
    """Provide mock settings with temporary directories."""
    mock = MagicMock()
    mock.TEMP_DIR = tmp_path / "temp"
    mock.CACHE_DIR = tmp_path / "cache"
    mock.LOGS_DIR = tmp_path / "logs"
    mock.LLM_API_KEY = "test-api-key"
    mock.LLM_BASE_URL = "http://localhost:4141"
    mock.LLM_MODEL = "gpt-4.1"
    mock.LLM_PROVIDER = "openai"
    mock.LLM_TEMPERATURE = 0.1
    mock.SECRET_KEY = "test-secret"
    mock.STUDENT_EMAIL = "test@example.com"
    mock.BROWSER_PAGE_TIMEOUT = 10000
    mock.QUIZ_TIMEOUT_SECONDS = 180
    mock.GEMINI_API_KEYS = ["test-gemini-key"]
    mock.HOST = "0.0.0.0"
    mock.PORT = 8000
    mock.DEBUG = True

    # Create directories
    mock.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    mock.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    mock.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    return mock


# =============================================================================
# Mock Resource Fixtures
# =============================================================================


@pytest.fixture
def mock_api_client():
    """Provide a mock API client."""
    client = AsyncMock()
    client.initialize = AsyncMock()
    client.close = AsyncMock()
    client.call_api = AsyncMock(return_value={"data": "test"})
    return client


@pytest.fixture
def mock_browser_client():
    """Provide a mock browser client."""
    client = MagicMock()
    client.browser = MagicMock()
    client.playwright = MagicMock()
    client._initialized = False
    client.initialize = AsyncMock()
    client.close = AsyncMock()
    client.fetch_page_content = AsyncMock(
        return_value={
            "html": "<html><body>Test</body></html>",
            "text": "Test",
            "console_logs": [],
            "screenshot_path": "/tmp/test.png",
        }
    )
    return client


@pytest.fixture
def mock_llm_client():
    """Provide a mock LLM client."""
    from langchain_core.messages import AIMessage

    client = MagicMock()
    client.chat = AsyncMock(return_value=AIMessage(content="Test response"))
    client.provider = "openai"
    client.model = "gpt-4.1"
    return client


@pytest.fixture
def mock_global_resources(mock_api_client, mock_browser_client, mock_llm_client):
    """Provide mock global resources."""
    resources = MagicMock()
    resources.api_client = mock_api_client
    resources.browser = mock_browser_client
    resources.llm_client = mock_llm_client
    resources.initialize = AsyncMock()
    resources.close = AsyncMock()
    return resources


# =============================================================================
# Quiz State Fixtures
# =============================================================================


@pytest.fixture
def sample_quiz_state(mock_global_resources):
    """Provide a sample quiz state for testing."""
    import time

    return {
        "email": "test@example.com",
        "secret": "test-secret",
        "current_url": "http://example.com/quiz",
        "answer_payload": None,
        "start_time": time.time(),
        "is_complete": False,
        "completed_quizzes": [],
        "submission_result": {},
        "submitted_answers": [],
        "html": "",
        "text": "",
        "console_logs": [],
        "screenshot_path": "",
        "tools": [],
        "attempt_count": 0,
        "messages": [],
        "resources": mock_global_resources,
    }


# =============================================================================
# Mock Message Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_message():
    """Provide a mock AI message."""
    from langchain_core.messages import AIMessage

    return AIMessage(content="Test AI response")


@pytest.fixture
def mock_human_message():
    """Provide a mock human message."""
    from langchain_core.messages import HumanMessage

    return HumanMessage(content="Test human message")


@pytest.fixture
def mock_tool_message():
    """Provide a mock tool message."""
    from langchain_core.messages import ToolMessage

    return ToolMessage(content="Tool result", tool_call_id="test-id")


@pytest.fixture
def mock_message_with_tool_calls():
    """Provide a mock message with tool calls."""
    message = MagicMock()
    message.id = "msg-1"
    message.tool_calls = [
        {
            "name": "python_tool",
            "id": "call-1",
            "args": {"code": "print('test')"},
        }
    ]
    return message


# =============================================================================
# Mock Tool Fixtures
# =============================================================================


@pytest.fixture
def mock_python_tool():
    """Provide a mock Python tool."""
    tool = AsyncMock()
    tool.name = "python_tool"
    tool.ainvoke = AsyncMock(return_value="Execution result")
    return tool


@pytest.fixture
def mock_submit_tool():
    """Provide a mock submit answer tool."""
    tool = AsyncMock()
    tool.name = "submit_answer_tool"
    tool.ainvoke = AsyncMock(
        return_value={
            "correct": True,
            "url": "http://example.com/next",
        }
    )
    return tool


@pytest.fixture
def mock_download_tool():
    """Provide a mock download tool."""
    tool = AsyncMock()
    tool.name = "download_file_tool"
    tool.ainvoke = AsyncMock(return_value="/tmp/downloaded_file.csv")
    return tool


# =============================================================================
# HTTP Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_httpx_response():
    """Provide a mock httpx response."""
    response = MagicMock()
    response.json.return_value = {"status": "ok"}
    response.text = "Response text"
    response.headers = {"Content-Type": "application/json"}
    response.raise_for_status = MagicMock()
    response.status_code = 200
    return response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Provide a mock httpx client."""
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.request = AsyncMock(return_value=mock_httpx_response)
    client.post = MagicMock(return_value=mock_httpx_response)
    client.get = MagicMock(return_value=mock_httpx_response)
    return client


# =============================================================================
# File Fixtures
# =============================================================================


@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    """Create a sample text file for testing."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Sample text content for testing.")
    return file_path


@pytest.fixture
def sample_json_file(tmp_path: Path) -> Path:
    """Create a sample JSON file for testing."""
    import json

    file_path = tmp_path / "sample.json"
    file_path.write_text(json.dumps({"key": "value", "number": 42}))
    return file_path


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Create a sample CSV file for testing."""
    file_path = tmp_path / "sample.csv"
    file_path.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\n")
    return file_path


@pytest.fixture
def sample_binary_file(tmp_path: Path) -> Path:
    """Create a sample binary file for testing."""
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return file_path


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def clean_env():
    """Provide a clean environment for testing."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_env(mocker):
    """Provide a mock environment dictionary."""
    env_dict = {
        "SECRET_KEY": "test-secret",
        "STUDENT_EMAIL": "test@example.com",
        "LLM_API_KEY": "test-api-key",
        "LLM_BASE_URL": "http://localhost:4141",
        "LLM_MODEL": "gpt-4.1",
        "LLM_PROVIDER": "openai",
        "DEBUG": "true",
    }
    return env_dict
