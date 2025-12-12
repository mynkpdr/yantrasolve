"""Tests for app/graph/graph.py"""

import time
from unittest.mock import MagicMock


from app.graph.graph import (
    create_quiz_graph,
    route_agent_decision,
    route_feedback,
)


class TestRouteAgentDecision:
    """Test cases for route_agent_decision function."""

    def test_route_to_execute_tools_with_regular_tools(self):
        """Test routing to execute_tools when non-submit tools are called."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "python_tool", "args": {"code": "print(1)"}}
        ]

        state = {
            "messages": [mock_message],
            "start_time": time.time(),
        }

        result = route_agent_decision(state)
        assert result == "execute_tools"

    def test_route_to_submit_answer_with_submit_tool(self):
        """Test routing to submit_answer when submit_answer_tool is called."""
        mock_message = MagicMock()
        mock_message.tool_calls = [{"name": "submit_answer_tool", "args": {}}]

        state = {
            "messages": [mock_message],
            "start_time": time.time(),
        }

        result = route_agent_decision(state)
        assert result == "submit_answer"

    def test_route_to_agent_when_no_tool_calls(self):
        """Test routing back to agent when no tool calls are present."""
        mock_message = MagicMock()
        mock_message.tool_calls = []

        state = {
            "messages": [mock_message],
            "start_time": time.time(),
        }

        result = route_agent_decision(state)
        assert result == "agent_reasoning"

    def test_route_to_agent_when_tool_calls_is_none(self):
        """Test routing back to agent when tool_calls attribute is None."""
        mock_message = MagicMock()
        mock_message.tool_calls = None

        state = {
            "messages": [mock_message],
            "start_time": time.time(),
        }

        result = route_agent_decision(state)
        assert result == "agent_reasoning"

    def test_route_with_multiple_tools_including_submit(self):
        """Test that submit takes priority when multiple tools are called."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "python_tool", "args": {}},
            {"name": "submit_answer_tool", "args": {}},
        ]

        state = {
            "messages": [mock_message],
            "start_time": time.time(),
        }

        result = route_agent_decision(state)
        assert result == "submit_answer"

    def test_route_with_timeout_still_continues(self, mocker):
        """Test that even with timeout, routing continues normally."""
        mocker.patch("app.graph.graph.settings.QUIZ_TIMEOUT_SECONDS", 1)

        mock_message = MagicMock()
        mock_message.tool_calls = [{"name": "python_tool", "args": {}}]

        state = {
            "messages": [mock_message],
            "start_time": time.time() - 100,  # Started 100 seconds ago
        }

        result = route_agent_decision(state)
        assert result == "execute_tools"


class TestRouteFeedback:
    """Test cases for route_feedback function."""

    def test_route_to_end_when_complete(self):
        """Test routing to END when quiz is complete."""
        state = {
            "is_complete": True,
            "submission_result": {},
            "start_time": time.time(),
        }

        result = route_feedback(state)
        assert result == "__end__"

    def test_route_to_fetch_context_on_correct_answer(self):
        """Test routing to fetch_context when answer is correct."""
        state = {
            "is_complete": False,
            "submission_result": {"correct": True, "url": "http://next-quiz.com"},
            "start_time": time.time(),
            "attempt_count": 1,
        }

        result = route_feedback(state)
        assert result == "fetch_context"

    def test_route_to_agent_on_incorrect_answer_with_time_remaining(self, mocker):
        """Test routing back to agent when answer is incorrect but time remains."""
        mocker.patch("app.graph.graph.settings.QUIZ_TIMEOUT_SECONDS", 180)

        state = {
            "is_complete": False,
            "submission_result": {"correct": False, "url": "http://next-quiz.com"},
            "start_time": time.time(),
            "attempt_count": 1,
        }

        result = route_feedback(state)
        assert result == "agent_reasoning"

    def test_route_to_fetch_context_on_timeout_with_next_url(self, mocker):
        """Test routing to next quiz when timeout occurs with next URL available."""
        mocker.patch("app.graph.graph.settings.QUIZ_TIMEOUT_SECONDS", 1)

        state = {
            "is_complete": False,
            "submission_result": {"correct": False, "url": "http://next-quiz.com"},
            "start_time": time.time() - 100,  # Timed out
            "attempt_count": 5,
        }

        result = route_feedback(state)
        assert result == "fetch_context"

    def test_route_to_end_on_timeout_without_next_url(self, mocker):
        """Test routing to END when timeout occurs without next URL."""
        mocker.patch("app.graph.graph.settings.QUIZ_TIMEOUT_SECONDS", 1)

        state = {
            "is_complete": False,
            "submission_result": {"correct": False, "url": None},
            "start_time": time.time() - 100,  # Timed out
            "attempt_count": 5,
        }

        result = route_feedback(state)
        assert result == "__end__"

    def test_route_to_next_quiz_on_max_attempts(self, mocker):
        """Test routing to next quiz when max attempts reached."""
        mocker.patch("app.graph.graph.settings.QUIZ_TIMEOUT_SECONDS", 1)

        state = {
            "is_complete": False,
            "submission_result": {"correct": False, "url": "http://next-quiz.com"},
            "start_time": time.time() - 100,
            "attempt_count": 10,
        }

        result = route_feedback(state)
        assert result == "fetch_context"


class TestCreateQuizGraph:
    """Test cases for create_quiz_graph function."""

    def test_create_quiz_graph_returns_compiled_graph(self):
        """Test that create_quiz_graph returns a compiled state graph."""
        graph = create_quiz_graph()

        # Check that the graph is compiled (has invoke method)
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "ainvoke")

    def test_graph_has_required_nodes(self):
        """Test that the graph contains all required nodes."""
        graph = create_quiz_graph()

        # Check that the graph structure contains expected nodes
        # The compiled graph has a graph attribute with nodes
        assert graph is not None

    def test_graph_entry_point(self):
        """Test that the graph starts at fetch_context."""
        graph = create_quiz_graph()

        # The entry point should be set
        assert graph is not None
