<div align="center">

# 🧩 YantraSolve

**AI-Powered Autonomous Quiz Solver**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0-FF6B35?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Hugging Face Space](https://img.shields.io/badge/🧩-Space-ff5c5c?logo=huggingface)](https://huggingface.co/spaces/mynkpdr/yantrasolve)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [API](#-api-reference) • [Architecture](#-architecture) • [Configuration](#-configuration) • [Testing](#-testing)

</div>

<img src="https://github.com/user-attachments/assets/c33187f4-eb1a-4101-82d4-4e6c9acf9647" width="100%">

## 📖 Overview

YantraSolve is an **autonomous AI agent** that solves data-driven quizzes using a state machine workflow. Built for the **Tools in Data Science – Project 2** (IITM BS Degree Programme).

### 🔄 Workflow

The application uses a **LangGraph** state machine to orchestrate the solving process:

1.  **Fetch Context**: The agent visits the quiz URL using a headless browser (Playwright) to capture HTML, text, console logs, and a screenshot.
2.  **Agent Reasoning**: An LLM (GPT-4o or similar) analyzes the page context and decides the next step.
3.  **Tool Execution**: If the agent needs to calculate something, download a file, or analyze an image, it calls the appropriate tool.
4.  **Submission**: Once the answer is determined, the agent submits it to the server.
5.  **Feedback Loop**: The system checks the submission result.
    *   **Correct**: The agent proceeds to the next quiz URL.
    *   **Incorrect**: The agent retries with the error feedback (up to 10 attempts).
    *   **Timeout**: If the quiz takes too long, it skips to the next one.


```
┌─────────────┐     ┌─────────────────┐     ┌───────────────┐
│ fetch_context│────▶│ agent_reasoning │◀───▶│ execute_tools │
└─────────────┘     └────────┬────────┘     └───────────────┘
                             │
                    ┌────────▼────────┐
                    │  submit_answer  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐     ┌──────────────┐
                    │process_feedback │────▶│ next quiz/END│
                    └─────────────────┘     └──────────────┘
```

---

## ✨ Features

### Agent Tools

| Tool | Description |
|------|-------------|
| `python_tool` | Execute Python with persistent session (pandas, numpy pre-loaded) |
| `javascript_tool` | Run JavaScript on browser pages via Playwright |
| `download_file_tool` | Download files (≤5MB) with caching |
| `call_llm_tool` | Analyze files with Gemini 2.5 Flash Lite (images, PDFs, audio, video) |
| `call_llm_with_multiple_files_tool` | Multi-file analysis |
| `submit_answer_tool` | Submit answers to quiz endpoints |

### Capabilities

| Category | What it can do |
|----------|----------------|
| **Web** | JS-rendered pages, dynamic content, console logs, iframes |
| **Files** | PDF extraction, Excel/CSV, ZIP/Gzip decoding |
| **Vision** | OCR, QR codes, chart reading, screenshots |
| **Audio** | Transcription via Gemini |
| **Data** | Pandas operations, filtering, aggregation, statistics |
| **ML** | Regression, clustering, classification |
| **Geo** | GeoJSON/KML with networkx |

### Reliability

- ⏱️ **3-minute timeout** per quiz with auto-skip
- 🔄 **10 retry attempts** before moving on
- 🔑 **Round-robin API key rotation** for Gemini
- 💾 **File-based caching** with TTL
- 🛡️ **Graceful error handling** - agent never crashes

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker (optional, for containerized run)

### Installation (Local)

```bash
# Clone repository
git clone https://github.com/mynkpdr/yantrasolve.git
cd yantrasolve

# Install dependencies
uv sync  # or: pip install -e .

# Install browser
playwright install chromium --with-deps
```

### Installation (Docker)

```bash
# Build image
docker build -t yantrasolve .

# Run container
docker run --env-file .env -p 8000:8000 yantrasolve
```

### Run

```bash
# Development
uv run python main.py

# Production
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📡 API Reference

### Health Check

```http
GET /
GET /health
```

**Response:** `200 OK`
```json
{"status": "ok", "message": "Quiz Solver is running"}
```

### Submit Quiz

```http
POST /quiz
Content-Type: application/json
```

**Request:**
```json
{
  "email": "student@example.com",
  "secret": "your-secret-key",
  "url": "https://example.com/quiz/1"
}
```

**Response:**
| Status | Description |
|--------|-------------|
| `200` | Quiz solving started (background) |
| `400` | Invalid JSON payload |
| `403` | Invalid secret or email |

---

## 🏭 Architecture

```
yantrasolve/
├── main.py                 # FastAPI application
├── app/
│   ├── config/
│   │   └── settings.py     # Pydantic settings
│   ├── graph/
│   │   ├── graph.py        # LangGraph workflow
│   │   ├── state.py        # QuizState TypedDict
│   │   └── resources.py    # Global resources
│   ├── nodes/
│   │   ├── fetch.py        # Page fetching
│   │   ├── agent.py        # AI reasoning
│   │   ├── tools.py        # Tool execution
│   │   ├── submit.py       # Answer submission
│   │   └── feedback.py     # Response handling
│   ├── tools/
│   │   ├── python.py       # Python sandbox
│   │   ├── javascript.py   # Browser JS
│   │   ├── download.py     # File downloader
│   │   ├── call_llm.py     # Gemini multimodal
│   │   └── submit_answer.py
│   ├── resources/
│   │   ├── llm.py          # Multi-provider LLM
│   │   ├── browser.py      # Playwright wrapper
│   │   └── api.py          # HTTP client
│   └── utils/
|       ├── answers.py      # Save correct answers
│       ├── cache.py        # File-based caching
│       ├── gemini.py       # Gemini utilities
│       ├── helpers.py      # Temp file management
│       └── logging.py      # Loguru setup
├── tests/                  # Pytest suite
├── Dockerfile
└── pyproject.toml
```

---

## 🧰 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *required* | Authentication secret |
| `STUDENT_EMAIL` | *required* | Student email |
| `LLM_API_KEY` | *required* | Primary LLM API key |
| `LLM_PROVIDER` | `openai` | `openai` or `google` |
| `LLM_MODEL` | `gpt-4.1` | Reasoning model |
| `LLM_TEMPERATURE` | `0.1` | Sampling temperature |
| `GEMINI_API_KEYS` | — | Comma-separated Gemini keys |
| `GEMINI_BASE_URL` | `https://aipipe.org/openrouter/v1` | Gemini API endpoint (OpenRouter-compatible) |
| `GEMINI_MODEL` | `google/gemini-2.5-flash-lite` | Gemini model for file analysis |
| `TEMP_DIR` | `/tmp/quiz_files` | Temp file storage |
| `CACHE_DIR` | `/tmp/quiz_cache` | Cache storage |
| `BROWSER_PAGE_TIMEOUT` | `10000` | Playwright timeout (ms) |
| `QUIZ_TIMEOUT_SECONDS` | `180` | Per-quiz timeout |

---

## 🐳 Docker

```bash
# Build
docker build -t yantrasolve .

# Run
docker run -p 8000:8000 \
  -e SECRET_KEY=xxx \
  -e STUDENT_EMAIL=xxx \
  -e LLM_API_KEY=xxx \
  -e GEMINI_API_KEYS=xxx \
  yantrasolve
```

### Hugging Face Spaces

1. Create a new Space with Docker SDK
2. Push this repository
3. Add secrets in Space settings
4. Access via `https://your-space.hf.space/quiz`

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific module
uv run pytest tests/test_tools/ -v
```

**Test coverage:** 225 tests covering all modules.

---

## 🗺️ Roadmap

- [ ] Dynamic model selection per quiz type
- [ ] Parallel quiz processing
- [ ] Web UI for monitoring progress
- [ ] Performance metrics dashboard
- [ ] Enhanced geo-spatial analysis

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file.

---

## 👤 Author

**Mayank Kumar Poddar**

- 📧 Email: [23f3004197@ds.study.iitm.ac.in](mailto:23f3004197@ds.study.iitm.ac.in)
- 🐙 GitHub: [@mynkpdr](https://github.com/mynkpdr)

---

<div align="center">

*Built with ☕ and determination*

</div>
