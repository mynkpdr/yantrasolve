---
title: Yantrasolve
emoji: 🏢
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
short_description: An automated system to solve data-driven tasks using AI.
---

# 🧩 YantraSolve – Autonomous AI Quiz Solver

[![Hugging Face Space](https://img.shields.io/badge/🤗-Space-ff5c5c?logo=huggingface)](https://huggingface.co/spaces/mynkpdriitm/yantrasolve)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-orange)](https://langchain-ai.github.io/langgraph/)

**Author:** Mayank Kumar Poddar (<23f3004197@ds.study.iitm.ac.in>)  
**GitHub:** [mayanklearns/yantrasolve](https://github.com/mayanklearns/yantrasolve)

---

## 📖 Overview

`YantraSolve` is an **AI-powered autonomous quiz-solving agent** built for the **Tools in Data Science – Project 2** of the **IITM BS Degree Programme**.

The system uses a **LangGraph state machine**, **LLMs (GPT/Gemini)**, and **Playwright headless browser** to:

1. **Fetch** quiz pages (HTML, screenshots, console logs from JS-rendered content)
2. **Reason** using an AI agent that decides which tools to use
3. **Execute** Python code, JavaScript on pages, download files, analyze with vision/audio LLMs
4. **Submit** answers and handle feedback (retry on wrong, proceed on correct)
5. **Iterate** through the entire quiz chain until completion

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

## ✨ Features & Capabilities

### 🤖 AI Agent Tools

| Tool | Description |
|------|-------------|
| `python_tool` | Execute Python code with persistent session (pre-imported: pandas, numpy) |
| `javascript_tool` | Run JavaScript on browser pages via Playwright |
| `download_file_tool` | Download files (up to 50MB) with caching |
| `call_llm_tool` | Analyze files with Gemini 2.5 Flash (images, PDFs, audio, video) |
| `call_llm_with_multiple_files_tool` | Analyze multiple files together |
| `submit_answer_tool` | Submit answers to quiz endpoints |

### 📊 Supported Task Types

Based on `project.md` requirements, the system handles:

| Category | Capabilities |
|----------|--------------|
| **Web Scraping** | JS-rendered pages, dynamic content, console logs, iframes |
| **File Processing** | PDF extraction, Excel/CSV parsing, ZIP/Gzip decoding |
| **Vision/OCR** | Image text extraction, QR codes (via cv2), chart reading, screenshots |
| **Audio** | Transcription via Gemini, waveform analysis |
| **Data Analysis** | Pandas operations, filtering, aggregation, statistics |
| **Machine Learning** | Regression, clustering, classification (via Python) |
| **Visualization** | Generate charts as base64 images |
| **Geospatial** | GeoJSON/KML analysis with networkx |
| **Encoding** | Base64, Gzip, AES decryption, hashing (MD5/SHA1) |

### 🛡️ Robustness Features

- **3-minute timeout** per quiz with automatic skip to next
- **Unlimited retries** within timeout window
- **10 max attempts** before moving on
- **Exponential backoff** on LLM errors (up to 10 retries)
- **Round-robin API key rotation** for Gemini (up to 3 keys)
- **File-based caching** with TTL for pages and downloads
- **Graceful error handling** - agent never crashes
- **Token limit protection** - skips quiz if messages exceed 25000 tokens

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (recommended via [uv](https://github.com/astral-sh/uv))
- **Docker** (optional, for deployment)
- **Playwright browsers** (auto-installed on first run)

### 1️⃣ Clone & Install
```bash
git clone https://github.com/mayanklearns/yantrasolve.git
cd yantrasolve
uv sync  # or: pip install -e .
playwright install chromium
```

### 2️⃣ Configure Environment
Create `.env` file:
```dotenv
# Required
SECRET_KEY=your-secret-key
STUDENT_EMAIL=your-email@ds.study.iitm.ac.in

# LLM Configuration (Primary reasoning model)
LLM_API_KEY=your-openai-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_PROVIDER=openai  # or google

# Gemini Keys (for file analysis - round-robin rotation)
GEMINI_API_KEY_1=your-gemini-key-1
GEMINI_API_KEY_2=your-gemini-key-2
GEMINI_API_KEY_3=your-gemini-key-3

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 3️⃣ Run
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
# or
python main.py
```

### 4️⃣ Test
```bash
# Health check
curl http://localhost:8000/health

# Submit a quiz (runs in background)
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email","secret":"your-secret","url":"https://quiz-url"}'
```

---

## 🐳 Docker Deployment

```bash
# Build
docker build -t yantrasolve .

# Run
docker run -p 8000:8000 \
  -e SECRET_KEY=xxx \
  -e STUDENT_EMAIL=xxx \
  -e LLM_API_KEY=xxx \
  -e GEMINI_API_KEY_1=xxx \
  yantrasolve
```

### HuggingFace Spaces
1. Create new Space with Docker SDK
2. Push this repository
3. Add secrets in Space settings
4. Access via `https://your-space.hf.space/quiz`

---

## 🌲 Project Structure

```
yantrasolve/
├── main.py                    # FastAPI entry point
├── app/
│   ├── config/
│   │   └── settings.py        # Pydantic settings from env
│   ├── graph/
│   │   ├── graph.py           # LangGraph workflow definition
│   │   ├── state.py           # QuizState TypedDict
│   │   └── resources.py       # GlobalResources (browser, llm)
│   ├── nodes/
│   │   ├── fetch.py           # Fetch page content node
│   │   ├── agent.py           # AI reasoning node
│   │   ├── tools.py           # Tool execution node
│   │   ├── submit.py          # Answer submission node
│   │   └── feedback.py        # Process server response node
│   ├── tools/
│   │   ├── python.py          # Python execution sandbox
│   │   ├── javascript.py      # Browser JS execution
│   │   ├── download.py        # File downloader with cache
│   │   ├── call_llm.py        # Gemini multimodal analysis
│   │   └── submit_answer.py   # HTTP POST submission
│   ├── resources/
│   │   ├── llm.py             # Multi-provider LLM client
│   │   ├── browser.py         # Playwright browser wrapper
│   │   └── api.py             # HTTP client utilities
│   └── utils/
│       ├── logging.py         # Structured logger
│       ├── cache.py           # File-based caching
│       ├── helpers.py         # Temp file management
│       └── gemini.py          # Gemini API utilities
├── tests/                     # Pytest test suite
├── Dockerfile                 # Production container
└── pyproject.toml             # Dependencies & scripts
```

---

## 📚 API Reference

### `GET /` or `GET /health`
Health check endpoint.
```json
{"status": "ok", "message": "Quiz Solver is running"}
```

### `POST /quiz`
Start quiz solving (runs in background).

**Request:**
```json
{
  "email": "student@example.com",
  "secret": "your-secret-key",
  "url": "https://example.com/quiz/1"
}
```

**Response:**
- `200` - Quiz solving started
- `400` - Invalid JSON payload
- `403` - Invalid secret or email

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | required | Authentication secret |
| `STUDENT_EMAIL` | required | Student email ID |
| `LLM_API_KEY` | required | Primary LLM API key |
| `LLM_PROVIDER` | `openai` | `openai` or `google` |
| `LLM_MODEL` | `gpt-5-mini` | Model for reasoning |
| `LLM_TEMPERATURE` | `0.1` | Sampling temperature |
| `GEMINI_API_KEY_1/2/3` | optional | Round-robin Gemini keys |
| `TEMP_DIR` | `/tmp/quiz_files` | Temporary file storage |
| `CACHE_DIR` | `/tmp/quiz_cache` | Cache storage |
| `BROWSER_PAGE_TIMEOUT` | `10000` | Playwright timeout (ms) |

---

## 🧪 Testing

```bash
uv run pytest -v
```

Test coverage includes:
- API endpoint validation
- Browser initialization
- LLM response mocking

---

## 📋 TODO: Future Improvements

> **Note:** The project statement (`project-llm-analysis-quiz.md`) itself contains TODOs and states "THIS PROJECT IS WORK IN PROGRESS. SOME DETAILS MAY CHANGE." Below are improvements that could be made with more time.

### 🔴 High Priority
- [ ] **Gemini Function Calling** - Currently it is experiencing Malformed Function Call errors
- [ ] **Dynamic Model Selection** - Allow choosing different LLMs per quiz
- [ ] **Advanced Error Handling** - More granular error categories and recovery

### 🟡 Medium Priority
- [ ] **Parallel Quiz Handling** - Process current and next URL simultaneously on wrong answers
- [ ] **Better Visualization Support** - Generate charts as images or interactive formats
- [ ] **Geo-spatial Analysis** - Improve GeoJSON/KML processing capabilities
- [ ] **Network Analysis** - Better graph/network data handling

### 🟢 Nice to Have
- [ ] **Comprehensive Test Suite** - Add more unit tests
- [ ] **Performance Metrics** - Track success rates per question type
- [ ] **Caching Optimization** - Smarter cache invalidation
- [ ] **Enhanced Logging** - More granular logs for debugging
- [ ] **User Interface** - Simple web UI for monitoring quiz progress
- [ ] **More Test Cases** - Cover edge cases in quiz solving

---

## 📝 Project Notes

### What the Project Requires (from `project-llm-analysis-quiz.md`)

1. **API Endpoint** that:
   - Accepts POST with `{email, secret, url}`
   - Returns HTTP 200 for valid requests, 400 for invalid JSON, 403 for invalid secrets
   - Solves quiz within **3 minutes** of receiving the request

2. **Quiz Solving** capabilities for:
   - Web scraping (JS-rendered pages)
   - API sourcing (with provided headers)
   - Data cleansing (text/PDF/etc.)
   - Data processing (transformation, transcription, vision)
   - Analysis (filtering, sorting, aggregating, ML models, geo-spatial, network)
   - Visualization (charts as images, narratives, slides)

3. **Answer Submission**:
   - POST to URL specified on quiz page (never hardcoded)
   - Payload: `{email, secret, url, answer}` under 1MB
   - Answer can be: boolean, number, string, base64 URI, or JSON object

4. **Prompt Testing** (separate evaluation):
   - System prompt (max 100 chars) to resist revealing a code word
   - User prompt (max 100 chars) to extract code words from other system prompts

### ⚠️ Unclear Aspects in Project Statement

The official project statement has these unresolved items:

1. **"THIS PROJECT IS WORK IN PROGRESS"** - Requirements may change
2. **Scoring weights** - "will be finalized later"
3. **Model selection** - "Which models will prompts be tested on?" marked as TODO
4. **Test pairing** - "How many other prompts will each prompt be tested against?" marked as TODO
5. **Viva format** - Only says "voice viva with LLM evaluator" without details
6. **3 minute timer** - Unclear if for a single question or entire quiz

### 💡 Design Decisions Made

Given the ambiguity, this implementation:
- Uses **LangGraph** for flexible workflow management
- Implements **multiple LLM providers** (OpenAI, Google) for redundancy
- Has **aggressive retry logic** (10 attempts, 3-min timeout per quiz)
- Uses **Gemini for multimodal** (vision, audio, PDF) analysis
- Maintains **persistent Python sessions** for stateful computations
- **Caches page content** to avoid redundant fetches

**Test endpoint provided:** `https://tds-llm-analysis.s-anand.net/demo`

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file.

---

## 📞 Contact

**Mayank Kumar Poddar**
- Email: 23f3004197@ds.study.iitm.ac.in
- GitHub: [@mayanklearns](https://github.com/mayanklearns)

---

*Built with mass frustration and determination. 🚀*
