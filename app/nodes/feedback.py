from app.utils.logging import logger
from app.graph.state import QuizState
from app.tools.python import reset_python_session
import time
from langchain_core.messages import HumanMessage, RemoveMessage


async def feedback_node(state: QuizState) -> dict:
    # Implementation of processing feedback from submission result
    logger.info(
        f"\n{'#' * 30}\n5. Processing feedback from submission result...\n{'#' * 30}"
    )
    result = state["submission_result"]
    # 1. Safe extraction of result
    completed_quizzes = state.get("completed_quizzes", [])
    is_correct = result.get("correct", False)
    reason = result.get("reason") or result.get("error", "No reason provided.")

    next_url = result.get("url")

    logger.info("Processing submission result in feedback node.")
    logger.info(f"Submission result: {result}")
    logger.info(f"Is Correct: {is_correct}, Next URL: {next_url}, Reason: {reason}")
    # --- CASE A: SUCCESS ---
    if is_correct:
        logger.info("✅ ANSWER CORRECT! Moving to next quiz.")

        # If no next_url is provided, the entire challenge is finished.
        if not next_url:
            return {
                "is_complete": True,
                "completed_quizzes": completed_quizzes
                + [
                    {
                        "url": state["current_url"],
                        "answer_payload": state.get("answer_payload", ""),
                    }
                ],
            }

        # CRITICAL: Full State Reset for the next question
        # We return a dict of keys we want to OVERWRITE in the state.
        messages_to_delete = [RemoveMessage(id=m.id) for m in state["messages"]]

        # Reset Python session for new quiz
        reset_python_session()

        return {
            "current_url": next_url,  # Point to new quiz
            "attempt_count": 0,  # Reset retries
            "submission_result": {},  # Clear old result
            "start_time": time.time(),  # Reset start time
            "screenshot_path": "",  # Clear old screenshot
            "completed_quizzes": completed_quizzes
            + [
                {
                    "url": state["current_url"],
                    "answer_payload": state.get("answer_payload", ""),
                }
            ],
            "html": "",  # Clear old HTML content
            "text": "",  # Clear old text content
            "console_logs": [],  # Clear old console logs
            # We clear the message history because the previous context
            # (old PDF, old question) is irrelevant and confusing for the new quiz.
            "messages": messages_to_delete,
        }

    # --- CASE B: FAILURE ---
    else:
        current_attempts = state.get("attempt_count", 0) + 1
        logger.info(
            f"❌ ANSWER INCORRECT (Attempt {current_attempts}). Reason: {reason}"
        )
        messages_to_delete = [RemoveMessage(id=m.id) for m in state["messages"]]

        # Construct a detailed feedback message to guide the Agent
        feedback_msg = HumanMessage(
            content=f"""## ❌ SUBMISSION INCORRECT - RETRY REQUIRED

**Attempt**: {current_attempts} of 5
**Server Response**: `{reason}`
**Error**: `{result.get("error", "N/A")}`

### Your Submitted Answer:
```json
{state.get('answer_payload', {})}
```

---

### 🔍 DEBUGGING CHECKLIST

1. **Data Type**: Is your answer the correct type? (string vs number vs list)
2. **Format**: Check for extra whitespace, quotes, or encoding issues
3. **Precision**: For numbers, check decimal places or rounding
4. **Completeness**: Did you process ALL the data, not just a sample?
5. **Logic**: Re-read the question - did you answer what was actually asked?

### 💡 COMMON FIXES

- Strip whitespace: `answer.strip()`
- Check type: `type(answer)`, convert if needed
- Round numbers: `round(answer, 2)` or `int(answer)`
- List issues: Check order, duplicates, or missing items
- String case: Sometimes case-sensitive (`"Yes"` vs `"yes"`)

### ⚡ ACTION REQUIRED

1. Re-analyze the original page content
2. Review your calculation/extraction logic
3. Fix the issue based on the server feedback
4. Submit the corrected answer

**TRY AGAIN NOW!**"""
        )
        # Update state: Increment counter and append the feedback message
        return {
            "attempt_count": current_attempts,
            "messages": messages_to_delete + [feedback_msg],
        }
