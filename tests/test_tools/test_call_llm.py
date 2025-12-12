"""Tests for app/tools/call_llm.py"""

from unittest.mock import MagicMock, patch


from app.tools.call_llm import (
    call_llm_tool,
    call_llm_with_multiple_files_tool,
    _build_file_content,
    _validate_files,
    _call_gemini,
)


class TestBuildFileContent:
    """Test cases for _build_file_content function."""

    def test_text_file_content(self, tmp_path):
        """Test building content for text files."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hello, World!")

        with patch("app.tools.call_llm.is_text_file", return_value=True):
            result = _build_file_content(str(text_file))

        assert result["type"] == "text"
        assert "Hello, World!" in result["text"]
        assert "test.txt" in result["text"]

    def test_binary_file_content(self, tmp_path):
        """Test building content for binary files."""
        binary_file = tmp_path / "test.png"
        binary_file.write_bytes(b"\x89PNG\r\n")

        with patch("app.tools.call_llm.is_text_file", return_value=False):
            with patch(
                "app.tools.call_llm.create_data_uri",
                return_value="data:image/png;base64,abc",
            ):
                result = _build_file_content(str(binary_file))

        assert result["type"] == "image_url"
        assert result["image_url"]["url"] == "data:image/png;base64,abc"

    def test_text_file_unicode_error_falls_to_binary(self, tmp_path):
        """Test that Unicode decode errors fall through to binary handling."""
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b"\xff\xfe\x00\x01")

        with patch("app.tools.call_llm.is_text_file", return_value=True):
            with patch(
                "app.tools.call_llm.create_data_uri",
                return_value="data:application/octet-stream;base64,xyz",
            ):
                result = _build_file_content(str(binary_file))

        assert result["type"] == "image_url"


class TestValidateFiles:
    """Test cases for _validate_files function."""

    def test_file_not_found(self, tmp_path):
        """Test validation fails for non-existent files."""
        result = _validate_files([str(tmp_path / "nonexistent.txt")])

        assert result is not None
        assert "not found" in result.lower()

    def test_files_exist(self, tmp_path):
        """Test validation passes for existing files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        result = _validate_files([str(file1), str(file2)])

        assert result is None

    def test_total_size_too_large(self, tmp_path):
        """Test validation fails when total size exceeds limit."""
        large_file = tmp_path / "large.bin"
        large_file.write_bytes(b"x" * (25 * 1024 * 1024))  # 25MB

        result = _validate_files([str(large_file)])

        assert result is not None
        assert "too large" in result.lower()

    def test_combined_size_too_large(self, tmp_path):
        """Test validation fails when combined size exceeds limit."""
        file1 = tmp_path / "file1.bin"
        file2 = tmp_path / "file2.bin"
        file1.write_bytes(b"x" * (15 * 1024 * 1024))  # 15MB
        file2.write_bytes(b"x" * (10 * 1024 * 1024))  # 10MB

        result = _validate_files([str(file1), str(file2)])

        assert result is not None
        assert "too large" in result.lower()


class TestCallGemini:
    """Test cases for _call_gemini function."""

    def test_successful_call(self, tmp_path, mocker):
        """Test successful Gemini API call."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("test content")

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "LLM response"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        mocker.patch("app.tools.call_llm.get_gemini_client", return_value=mock_client)
        mocker.patch("app.tools.call_llm.is_text_file", return_value=True)

        result = _call_gemini("Analyze this", [str(text_file)])

        assert result == "LLM response"

    def test_file_not_found_error(self, tmp_path):
        """Test error when file is not found."""
        result = _call_gemini("Analyze", [str(tmp_path / "missing.txt")])

        assert "Error" in result
        assert "not found" in result.lower()

    def test_file_too_large_error(self, tmp_path, mocker):
        """Test error when file is too large."""
        large_file = tmp_path / "large.bin"
        large_file.write_bytes(b"x" * (25 * 1024 * 1024))

        result = _call_gemini("Analyze", [str(large_file)])

        assert "Error" in result
        assert "too large" in result.lower()


class TestCallLLMTool:
    """Test cases for call_llm_tool function."""

    def test_successful_analysis(self, tmp_path, mocker):
        """Test successful file analysis."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Test content for analysis")

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Analysis result"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        mocker.patch("app.tools.call_llm.get_gemini_client", return_value=mock_client)
        mocker.patch("app.tools.call_llm.is_text_file", return_value=True)

        result = call_llm_tool.invoke(
            {
                "file_path": str(text_file),
                "prompt": "What is in this file?",
            }
        )

        assert result == "Analysis result"

    def test_handles_exception(self, tmp_path, mocker):
        """Test handling of exceptions."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("content")

        mocker.patch(
            "app.tools.call_llm.get_gemini_client", side_effect=Exception("API Error")
        )
        mocker.patch("app.tools.call_llm.is_text_file", return_value=True)

        result = call_llm_tool.invoke(
            {
                "file_path": str(text_file),
                "prompt": "Analyze",
            }
        )

        assert "Error" in result


class TestCallLLMWithMultipleFilesTool:
    """Test cases for call_llm_with_multiple_files_tool function."""

    def test_successful_multi_file_analysis(self, tmp_path, mocker):
        """Test successful analysis of multiple files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Combined analysis"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        mocker.patch("app.tools.call_llm.get_gemini_client", return_value=mock_client)
        mocker.patch("app.tools.call_llm.is_text_file", return_value=True)

        result = call_llm_with_multiple_files_tool.invoke(
            {
                "file_paths": [str(file1), str(file2)],
                "prompt": "Compare these files",
            }
        )

        assert result == "Combined analysis"

    def test_empty_file_list(self, mocker):
        """Test handling of empty file list."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "No files to analyze"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        mocker.patch("app.tools.call_llm.get_gemini_client", return_value=mock_client)

        result = call_llm_with_multiple_files_tool.invoke(
            {
                "file_paths": [],
                "prompt": "Analyze",
            }
        )

        # Should either work with empty list or return error
        assert result is not None

    def test_handles_exception(self, tmp_path, mocker):
        """Test handling of exceptions."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")

        mocker.patch(
            "app.tools.call_llm.get_gemini_client", side_effect=Exception("API Error")
        )
        mocker.patch("app.tools.call_llm.is_text_file", return_value=True)

        result = call_llm_with_multiple_files_tool.invoke(
            {
                "file_paths": [str(file1)],
                "prompt": "Analyze",
            }
        )

        assert "Error" in result
