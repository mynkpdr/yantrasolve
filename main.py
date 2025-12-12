"""YantraSolve - LLM-powered quiz solver using LangGraph."""

import asyncio
import hmac
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, HttpUrl

from app.config.settings import settings
from app.graph.graph import create_quiz_graph
from app.graph.resources import GlobalResources
from app.graph.state import QuizState
from app.tools.call_llm import call_llm_tool, call_llm_with_multiple_files_tool
from app.tools.download import download_file_tool
from app.tools.javascript import create_javascript_tool
from app.tools.python import python_tool
from app.tools.submit_answer import submit_answer_tool
from app.utils.helpers import cleanup_temp_files, setup_temp_directory
from app.utils.logging import logger


# =============================================================================
# Lifespan & App Setup
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage global resources lifecycle."""
    resources = GlobalResources()
    await resources.initialize()
    app.state.resources = resources
    setup_temp_directory()
    yield
    logger.info("Shutdown: Closing resources...")
    await resources.close()
    cleanup_temp_files()


app = FastAPI(
    title="LLM Analysis Quiz Solver",
    description="Intelligent quiz solver using LangGraph and LLMs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Models & Handlers
# =============================================================================


class QuizRequest(BaseModel):
    email: EmailStr
    secret: str
    url: HttpUrl


class HealthResponse(BaseModel):
    status: str
    message: str


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 400 for invalid JSON or validation errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid JSON payload", "errors": exc.errors()},
    )


# =============================================================================
# Endpoints
# =============================================================================


@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", message="Quiz Solver is running")


@app.post("/quiz")
async def receive_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Receive quiz task and solve in background.
    
    This endpoint accepts a quiz request, verifies the credentials,
    and starts a background task to solve the quiz using the LangGraph workflow.
    """
    logger.info(f"Quiz request: {request.email}, URL: {request.url}")

    if not _verify_request(request.secret, request.email):
        logger.warning(f"Unauthorized: {request.email}")
        raise HTTPException(status_code=403, detail="Invalid secret or email")

    background_tasks.add_task(
        _solve_quiz_task,
        request.email,
        request.secret,
        str(request.url),
        app.state.resources,
    )
    logger.info(f"Quiz task started for {request.url}")
    return {"status": "accepted", "message": "Quiz solving started"}


# =============================================================================
# Helpers
# =============================================================================


def _verify_request(secret: str, email: str) -> bool:
    """Verify credentials using constant-time comparison."""
    return hmac.compare_digest(
        settings.SECRET_KEY.encode(), secret.encode()
    ) and hmac.compare_digest(settings.STUDENT_EMAIL.encode(), email.encode())


async def _solve_quiz_task(
    email: str, secret: str, url: str, resources: GlobalResources
):
    """Background task to solve quiz using LangGraph workflow."""
    try:
        initial_state: QuizState = {
            "email": email,
            "secret": secret,
            "current_url": url,
            "answer_payload": None,
            "attempt_count": 0,
            "resources": resources,
            "start_time": time.time(),
            "is_complete": False,
            "messages": [],
            "screenshot_path": "",
            "html": "",
            "text": "",
            "console_logs": [],
            "completed_quizzes": [],
            "submission_result": {},
            "submitted_answers": [],
            "tools": [
                python_tool,
                submit_answer_tool,
                create_javascript_tool(resources.browser),
                download_file_tool,
                call_llm_tool,
                call_llm_with_multiple_files_tool,
            ],
        }

        graph = create_quiz_graph()
        result = await asyncio.wait_for(
            graph.ainvoke(initial_state, {"recursion_limit": 5000}), timeout=3600
        )
        completed = result.get("completed_quizzes", [])
        logger.info(
            f"Quiz completed for {email} (completed={len(completed)} quizzes)"
        )

    except asyncio.TimeoutError:
        logger.error(f"Quiz timed out for {email}")
    except Exception as e:
        logger.error(f"Quiz error: {e}")
    finally:
        cleanup_temp_files()
        logger.info(f"Background task finished for {email}")


# =============================================================================
# Entry Point
# =============================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="debug" if settings.DEBUG else "info",
        reload=settings.DEBUG,
    )
