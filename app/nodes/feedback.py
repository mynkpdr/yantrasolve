"""Feedback node for processing submission results."""

import json
import time
from langchain_core.messages import HumanMessage, RemoveMessage
from app.config.settings import settings
from app.graph.state import QuizState
from app.tools.python import reset_python_session
from app.utils.answers import save_correct_answer
from app.utils.logging import logger


def _create_reset_state(next_url: str, completed_quizzes: list, messages: list) -> dict:
    """Create state dict for moving to next quiz."""
    return {
        "answer_payload": {},
        "current_url": next_url,
        "attempt_count": 0,
        "start_time": time.time(),
        "screenshot_path": "",
        "completed_quizzes": completed_quizzes,
        "html": "",
        "text": "",
        "console_logs": [],
        "messages": [RemoveMessage(id=m.id) for m in messages],
        "is_complete": False,
        "submitted_answers": [],
    }


async def feedback_node(state: QuizState) -> dict:
    """Process submission feedback and decide next action."""

    result = state.get("submission_result", {})
    completed_quizzes = state.get("completed_quizzes", [])
    is_correct = result.get("correct", False)
    reason = result.get("reason") or result.get("error", "No reason provided.")
    next_url = result.get("url")

    logger.info("\n" + json.dumps(result, indent=2))

    # Handle correct answer
    if is_correct:
        logger.info("✅ ANSWER CORRECT!")
        try:
            # Save answer for future reference
            save_correct_answer(
                state.get("current_url", ""), state.get("answer_payload")
            )
        except Exception as e:
            logger.error(f"Failed to save correct answer: {e}")
        completed_quizzes = completed_quizzes + [
            {
                "url": state["current_url"],
                "answer_payload": state.get("answer_payload"),
            }
        ]
        if not next_url:
            return {"is_complete": True, "completed_quizzes": completed_quizzes}
        reset_python_session()
        return _create_reset_state(next_url, completed_quizzes, state["messages"])

    # Handle incorrect answer
    current_attempts = state.get("attempt_count", 0) + 1
    elapsed = time.time() - state.get("start_time", time.time())
    logger.info(
        f"❌ ANSWER INCORRECT (Attempt {current_attempts}, {elapsed:.0f}s elapsed)"
    )

    # Timeout: move to next quiz or end
    if elapsed > settings.QUIZ_TIMEOUT_SECONDS:
        if next_url:
            logger.warning(f"⏰ Timeout! Moving to next quiz: {next_url}")
            reset_python_session()
            return _create_reset_state(next_url, completed_quizzes, state["messages"])
        logger.warning("⏰ Timeout! No more quizzes, marking complete.")
        return {"is_complete": True, "completed_quizzes": completed_quizzes}

    # Retry with feedback message
    feedback_msg = HumanMessage(
        content=f"""## ❌ INCORRECT - Attempt {current_attempts}

**Server says**: `{reason}`

**Your previous submissions were:**
```
{json.dumps(state.get('submitted_answers', []), indent=2)}
```

**Quick fixes to try**:
- Check rounding/precision for numbers
- Re-read the question carefully
- Ensure correct data formats (e.g., JSON structure)

**TRY AGAIN with a corrected answer!**"""
    )

    return {
        "attempt_count": current_attempts,
        "messages": [feedback_msg],
    }
