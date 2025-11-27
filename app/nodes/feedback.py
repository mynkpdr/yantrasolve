from app.utils.logging import logger
from app.graph.state import QuizState
import time
from langchain_core.messages import HumanMessage, RemoveMessage


async def feedback_node(state: QuizState) -> dict:
    # Implementation of processing feedback from submission result
    # TODO: Add actual feedback processing logic here
    logger.info(
        f"\n{'#' * 30}\n5. Processing feedback from submission result...\n{'#' * 30}"
    )
    result = state["submission_result"]
    # 1. Safe extraction of result
    completed_quizzes = state.get("completed_quizzes", [])
    is_correct = result.get("correct", False)
    reason = result.get("reason", "No reason provided by server.")
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

        # Construct a feedback message to guide the Agent
        feedback_msg = HumanMessage(
            [
                {
                    "type": "text",
                    "text": f"SYSTEM NOTIFICATION: Your submission was INCORRECT.\n"
                    f"Server Reason: '{reason}'\n\n"
                    f"Action Required: Analyze your previous steps, fix the error described above, "
                    f"and try submitting again.",
                }
            ]
        )
        # Update state: Increment counter and append the feedback message
        return {
            "attempt_count": current_attempts,
            "messages": messages_to_delete + [feedback_msg],
        }
