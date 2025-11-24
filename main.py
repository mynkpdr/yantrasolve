import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, HttpUrl
from app.utils.helpers import cleanup_temp_files, setup_temp_directory
from app.utils.logging import logger
from app.config.settings import settings
import hmac



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup and shutdown tasks"""
    setup_temp_directory()
    yield
    cleanup_temp_files()


# Initialize FastAPI app
app = FastAPI(
    title="LLM Analysis Quiz Solver",
    description="Intelligent quiz solver using LangGraph and LLMs",
    version="1.0.0",
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
    return hmac.compare_digest(expected_secret, provided_secret) and hmac.compare_digest(expected_email, provided_email)


async def solve_quiz_task(
    email: str, secret: str, url: str
):
    """Background task to solve quiz"""
    # TODO: Implement quiz solving logic here
    logger.info("LOGIC")
    await asyncio.sleep(5)
    logger.info(f"Quiz solved for {email} at {url} with secret {secret}")

@app.post("/quiz")
async def receive_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint to receive quiz tasks
    Returns 200 immediately and solves in background
    """
    logger.info(f"Received quiz request for {request.email}")

    success = verify_request(request.secret, request.email)

    # Verify secret and email
    if not success:
        logger.warning(f"Unauthorized access attempt for {request.email}")
        raise HTTPException(status_code=403, detail="Invalid secret or email")

    # Spawn background task
    background_tasks.add_task(
        solve_quiz_task, request.email, request.secret, request.url
    )

    logger.info(f"Quiz task started for {request.url}")
    return {"status": "accepted", "message": "Quiz solving started"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, log_level="debug" if settings.DEBUG else "info", reload=settings.DEBUG)