from app.utils.logging import logger
from app.graph.state import QuizState
from app.tools.python import reset_python_session
import time
from langchain_core.messages import HumanMessage, RemoveMessage


async def feedback_node(state: QuizState) -> dict:
    """Process submission feedback and decide next action."""
    logger.info(
        f"\n{'#' * 30}\n5. Processing feedback from submission result...\n{'#' * 30}"
    )
    result = state.get("submission_result", {})
    completed_quizzes = state.get("completed_quizzes", [])
    is_correct = result.get("correct", False)
    reason = result.get("reason") or result.get("error", "No reason provided.")
    next_url = result.get("url")

    logger.info(f"Result: correct={is_correct}, reason={reason}, next_url={next_url}")

    # --- CASE A: SUCCESS ---
    if is_correct:
        logger.info("✅ ANSWER CORRECT!")

        if not next_url:
            return {
                "is_complete": True,
                "completed_quizzes": completed_quizzes + [{
                    "url": state["current_url"],
                    "answer_payload": state.get("answer_payload", ""),
                }],
            }

        # Reset for next quiz
        messages_to_delete = [RemoveMessage(id=m.id) for m in state["messages"]]
        reset_python_session()

        return {
            "current_url": next_url,
            "attempt_count": 0,
            "start_time": time.time(),
            "screenshot_path": "",
            "completed_quizzes": completed_quizzes + [{
                "url": state["current_url"],
                "answer_payload": state.get("answer_payload", ""),
            }],
            "html": "",
            "text": "",
            "console_logs": [],
            "messages": messages_to_delete,
        }

    # --- CASE B: FAILURE - Keep context for retry ---
    current_attempts = state.get("attempt_count", 0) + 1
    elapsed = time.time() - state.get("start_time", time.time())
    logger.info(f"❌ INCORRECT (Attempt {current_attempts}, {elapsed:.0f}s elapsed)")

    # Check if we should move to next URL (time exceeded)
    if elapsed > 180 and next_url:  # 3 minutes
        logger.warning(f"Timeout! Moving to next quiz: {next_url}")
        messages_to_delete = [RemoveMessage(id=m.id) for m in state["messages"]]
        reset_python_session()
        
        return {
            "current_url": next_url,
            "attempt_count": 0,
            "submission_result": {},
            "start_time": time.time(),
            "screenshot_path": "",
            "html": "",
            "text": "",
            "console_logs": [],
            "messages": messages_to_delete,
        }

    # Retry - add feedback message but KEEP existing context
    feedback_msg = HumanMessage(
        content=f"""## ❌ INCORRECT - Attempt {current_attempts}

**Server says**: `{reason}`

**Your answer was**:
```
{state.get('answer_payload', {})}
```

**Quick fixes to try**:
- Check data type (string vs number vs list)
- Strip whitespace: `.strip()`
- Check rounding/precision for numbers
- Re-read the question carefully

**TRY AGAIN with a corrected answer!**"""
    )

    return {
        "attempt_count": current_attempts,
        "messages": [feedback_msg],  # Just append, don't delete
    }
