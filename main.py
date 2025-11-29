import asyncio
from contextlib import asynccontextmanager
import json
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, HttpUrl
from app.graph.resources import GlobalResources
from app.graph.state import QuizState
from app.tools.submit_answer import submit_answer_tool
from app.tools.python import python_tool
from app.tools.javascript import create_javascript_tool
from app.tools.download import download_file_tool
from app.tools.call_llm import call_llm_tool, call_llm_with_multiple_files_tool

from app.utils.helpers import cleanup_temp_files, setup_temp_directory
from app.utils.logging import logger
from app.config.settings import settings
from app.graph.graph import create_quiz_graph
import hmac


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage global resources for the application lifetime."""

    global_resources = GlobalResources()
    await global_resources.initialize()  # Initialize global resources just once
    app.state.resources = (
        global_resources  # Global resources access via app.state.resources
    )

    setup_temp_directory()

    #####   Application running   #####
    yield
    #####   Application shutdown   #####

    logger.info("Application shutdown: Closing global resources...")
    await global_resources.close()  # Close global resources

    cleanup_temp_files()  # Clean up temporary files on shutdown


# Initialize FastAPI app
app = FastAPI(
    title="LLM Analysis Quiz Solver",
    description="Intelligent quiz solver using LangGraph and LLMs",
    version="0.1.0",
    lifespan=lifespan,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for invalid JSON (HTTP 400)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 400 for invalid JSON or validation errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid JSON payload", "errors": exc.errors()},
    )


class QuizRequest(BaseModel):
    email: EmailStr
    secret: str
    url: HttpUrl


class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok", message="Quiz Solver is running")


def verify_request(provided_secret: str, provided_email: str) -> bool:
    """Verify secret and email using constant-time comparison"""
    expected_secret = settings.SECRET_KEY.encode()
    provided_secret = provided_secret.encode()
    expected_email = settings.STUDENT_EMAIL.encode()
    provided_email = provided_email.encode()

    return hmac.compare_digest(
        expected_secret, provided_secret
    ) and hmac.compare_digest(expected_email, provided_email)


async def solve_quiz_task(
    email: str, secret: str, url: str, resources: GlobalResources
):
    """Background task to solve quiz"""
    try:
        javascript_tool = create_javascript_tool(resources.browser)
        initial_state: QuizState = {
            "email": email,
            "secret": secret,
            "current_url": url,
            "answer_payload": None,
            "tools": [python_tool, submit_answer_tool, javascript_tool, download_file_tool, call_llm_tool, call_llm_with_multiple_files_tool],
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

        }

        # Create and run the quiz-solving graph
        graph = create_quiz_graph()

        # Execute the graph with timeout
        try:
            result = await asyncio.wait_for(
                graph.ainvoke(initial_state, {"recursion_limit": 500}),
                timeout=60 * 60,  # 1 hour
            )

            logger.info(f"Quiz processing completed for {email}")
            logger.info(
                f"Completed Quizzes: {json.dumps(result.get('completed_quizzes', []), indent=2)}"
            )

        except asyncio.TimeoutError:
            logger.error(f"Quiz processing timed out for {email}")

    except Exception as e:
        logger.error(f"Error solving quiz: {e}")

    finally:
        cleanup_temp_files()
        logger.info(f"Background task finished for {email}")


@app.post("/quiz")
async def receive_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint to receive quiz tasks
    Returns 200 immediately and solves in background
    """
    logger.info(f"Received quiz request for {request.email}, URL: {request.url}, Secret: {request.secret}")

    success = verify_request(request.secret, request.email)

    # Verify secret and email
    if not success:
        logger.warning(f"Unauthorized access attempt for {request.email}")
        raise HTTPException(status_code=403, detail="Invalid secret or email")

    global_resources = app.state.resources

    # Spawn background task
    background_tasks.add_task(
        solve_quiz_task,
        request.email,
        request.secret,
        str(request.url),  # Convert HttpUrl to str for serialization
        global_resources,
    )

    logger.info(f"Quiz task started for {request.url}")
    return {"status": "accepted", "message": "Quiz solving started"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="debug" if settings.DEBUG else "info",
        reload=settings.DEBUG,
    )
