"""Tests for app/tools/submit_answer.py"""

from unittest.mock import MagicMock

import httpx

from app.tools.submit_answer import submit_answer_tool


class TestSubmitAnswerTool:
    """Test cases for submit_answer_tool function."""

    def test_successful_submission(self, mocker):
        """Test successful answer submission."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"correct": True, "url": "http://next.com"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post = MagicMock(return_value=mock_response)

        mocker.patch("httpx.Client", return_value=mock_client)

        result = submit_answer_tool.invoke(
            {
                "post_endpoint_url": "https://api.example.com/submit",
                "payload": {
                    "email": "test@example.com",
                    "secret": "secret",
                    "url": "http://quiz.com",
                    "answer": "42",
                },
            }
        )

        assert result["correct"] is True
        assert result["url"] == "http://next.com"

    def test_incorrect_answer_response(self, mocker):
        """Test handling of incorrect answer response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "correct": False,
            "reason": "Expected 42, got 41",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post = MagicMock(return_value=mock_response)

        mocker.patch("httpx.Client", return_value=mock_client)

        result = submit_answer_tool.invoke(
            {
                "post_endpoint_url": "https://api.example.com/submit",
                "payload": {"answer": "41"},
            }
        )

        assert result["correct"] is False
        assert "Expected 42" in result["reason"]

    def test_invalid_endpoint_url(self):
        """Test rejection of non-HTTP URLs."""
        result = submit_answer_tool.invoke(
            {
                "post_endpoint_url": "ftp://invalid.com/submit",
                "payload": {"answer": "42"},
            }
        )

        assert "error" in result
        assert "http" in result["error"].lower()

    def test_invalid_payload_url(self, mocker):
        """Test rejection of non-HTTP URLs in payload."""
        result = submit_answer_tool.invoke(
            {
                "post_endpoint_url": "https://api.example.com/submit",
                "payload": {
                    "url": "ftp://invalid.com",
                    "answer": "42",
                },
            }
        )

        assert "error" in result
        assert "url" in result["error"].lower()

    def test_http_error(self, mocker):
        """Test handling of HTTP errors."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post = MagicMock(side_effect=httpx.HTTPError("Connection failed"))

        mocker.patch("httpx.Client", return_value=mock_client)

        result = submit_answer_tool.invoke(
            {
                "post_endpoint_url": "https://api.example.com/submit",
                "payload": {"answer": "42"},
            }
        )

        assert "error" in result
        assert "failed" in result["error"].lower()

    def test_unexpected_error(self, mocker):
        """Test handling of unexpected errors."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post = MagicMock(side_effect=Exception("Unexpected error"))

        mocker.patch("httpx.Client", return_value=mock_client)

        result = submit_answer_tool.invoke(
            {
                "post_endpoint_url": "https://api.example.com/submit",
                "payload": {"answer": "42"},
            }
        )

        assert "error" in result
        assert "Unexpected" in result["error"]

    def test_sends_correct_headers(self, mocker):
        """Test that correct headers are sent."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"correct": True}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post = MagicMock(return_value=mock_response)

        mocker.patch("httpx.Client", return_value=mock_client)

        submit_answer_tool.invoke(
            {
                "post_endpoint_url": "https://api.example.com/submit",
                "payload": {"answer": "42"},
            }
        )

        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["headers"] == {"Content-Type": "application/json"}

    def test_sends_correct_payload(self, mocker):
        """Test that correct payload is sent."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"correct": True}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post = MagicMock(return_value=mock_response)

        mocker.patch("httpx.Client", return_value=mock_client)

        payload = {
            "email": "test@example.com",
            "secret": "my-secret",
            "url": "http://quiz.example.com",
            "answer": {"value": 42},
        }

        submit_answer_tool.invoke(
            {
                "post_endpoint_url": "https://api.example.com/submit",
                "payload": payload,
            }
        )

        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["json"] == payload

    def test_various_answer_types(self, mocker):
        """Test submission with various answer types."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"correct": True}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post = MagicMock(return_value=mock_response)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Test different answer types
        answer_types = [
            42,  # Number
            "text answer",  # String
            True,  # Boolean
            {"nested": "object"},  # Object
            [1, 2, 3],  # Array
        ]

        for answer in answer_types:
            result = submit_answer_tool.invoke(
                {
                    "post_endpoint_url": "https://api.example.com/submit",
                    "payload": {"answer": answer},
                }
            )
            assert result["correct"] is True
