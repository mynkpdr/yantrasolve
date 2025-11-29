---
title: Yantrasolve
emoji: 🏢
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
short_description: An automated system that to solve data-driven quizzes.
---

# 🧩 YantraSolve – Automated Quiz Solver

[![Hugging Face Space](https://img.shields.io/badge/🤗-Space-ff5c5c?logo=huggingface)](https://huggingface.co/spaces/mynkpdriitm/yantrasolve)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)

**Author:** Mayank Kumar Poddar (<23f3004197@ds.study.iitm.ac.in>)  
**GitHub:** [mayanklearns/yantrasolve](https://github.com/mayanklearns/yantrasolve)

---

## 📖 Overview

`YantraSolve` is a **FastAPI‑based micro‑service** that automatically solves the *LLM Analysis Quiz* used in the **Tools in Data Science – Project 2** of the **IITM BS Degree Programme**.  
The system leverages **LangGraph**, **large language models**, and a **headless Chromium browser** to:

1. **Fetch** each quiz page (HTML, screenshots, console logs).  
2. **Reason** about the next action using an LLM‑driven agent.  
3. **Execute** Python or JavaScript snippets, download auxiliary files, and finally **submit** the answer payload.
4. **Iterate** until the whole quiz chain is completed.

All heavy lifting happens in a **background task**, allowing the API to respond instantly while the solver works asynchronously.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- **Python 3.11+** (recommended via `uv` – a fast, modern Python package manager).
- **Docker** (optional, for containerised deployment).
- **Playwright** browsers – they are installed automatically when you run the app for the first time.

### 1️⃣ Clone the repository
```bash
git clone https://github.com/mayanklearns/yantrasolve.git
cd yantrasolve
```

### 2️⃣ Install dependencies with **uv**
```bash
uv sync   # reads pyproject.toml and installs exact versions
```
> `uv sync` creates a virtual environment in `.venv` (by default) and locks the dependency graph, guaranteeing reproducible builds.

### 3️⃣ Configure environment variables
Create a `.env` file in the project root (or export variables in your shell). Example:
```dotenv
SECRET_KEY=your-secret-key
STUDENT_EMAIL=23f3004197@ds.study.iitm.ac.in
LLM_API_KEY=your-openai-or-google-api-key
LLM_PROVIDER=google   # or anthropic, openai, etc.
HOST=0.0.0.0
PORT=8000
DEBUG=true
```
> The `settings` module (`app/config/settings.py`) reads these variables via **pydantic‑settings**.

### 4️⃣ Run the server
```bash
uv run python -m uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

### 5️⃣ Health check
```bash
curl http://127.0.0.1:8000/health
```
You should receive a JSON response confirming the service is up.

---

## 📦 Docker & HuggingFace Space Deployment

### Dockerfile (already in the repo)
The repository ships a production‑ready `Dockerfile`. Build and run it locally:
```bash
docker build -t yantrasolve .

docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e STUDENT_EMAIL=23f3004197@ds.study.iitm.ac.in \
  -e LLM_API_KEY=your-llm-key \
  -e LLM_PROVIDER=google \
  yantrasolve
```
The container starts the FastAPI app automatically.

### Deploy as a HuggingFace Space (FastAPI template)
1. **Create a new Space** on HuggingFace and select the *FastAPI* template.
2. **Push the repository** to the Space (or use the UI to upload files). The existing `Dockerfile` will be used by HuggingFace to build the container.
3. **Add the required secrets** in the Space settings under *Variables* (`SECRET_KEY`, `STUDENT_EMAIL`, `LLM_API_KEY`, `LLM_PROVIDER`).
4. The Space will automatically start the server on the port defined by the `PORT` env variable (default `8000`).
5. Once the build finishes, you can interact with the API via the Space URL, e.g., `https://mynkpdriitm-yantrasolve.hf.space/quiz`.

> **Note:** HuggingFace Spaces enforce a 12‑hour timeout for background tasks. The solver is designed to finish well within this limit (default 1‑hour timeout per quiz chain).

---

## 🌲 Project Structure
```
.
├── app/                     # Core application package
│   ├── config/              # Settings (pydantic)
│   ├── graph/               # LangGraph construction
│   ├── nodes/               # Graph nodes (fetch, agent, submit, …)
│   ├── resources/           # Browser, LLM, API helpers
│   ├── tools/               # Sandbox tools (python, js, download, submit)
│   └── utils/               # Helpers & logging
├── tests/                   # pytest suite
├── Dockerfile               # Multi‑stage build for production
├── pyproject.toml           # Build system, dependencies, uv scripts
├── README.md                # You are reading it!
└── main.py                  # FastAPI entry point
```

### `pyproject.toml`
The **pyproject.toml** defines the build backend, dependencies, and a convenient `uv run` script:
```toml
[project]
name = "yantrasolve"
version = "0.1.0"
description = "Automated quiz solver for IITM Data Science project"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [{name = "Mayank Kumar Poddar", email = "23f3004197@ds.study.iitm.ac.in"}]

[project.dependencies]
fastapi = "^0.115"
uvicorn = "^0.30"
langgraph = "^0.0.30"
playwright = "^1.45"
pydantic-settings = "^2.5"
# … other runtime deps …

[tool.uv]
# uv specific configuration (optional)

[tool.uv.scripts]
start = "python -m uvicorn main:app --host $HOST --port $PORT"
```
Running `uv sync` reads this file, creates a lockfile (`uv.lock`) and installs the exact versions, guaranteeing reproducibility across environments.

---

## 📚 API Specification

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| `GET` | `/` or `/health` | Health check | – | `{ "status": "ok", "message": "Quiz Solver is running" }` |
| `POST` | `/quiz` | Submit a quiz‑solving job (runs in background) | `QuizRequest` (see below) | `{ "status": "accepted", "message": "Quiz solving started" }` |

### `QuizRequest` model
```json
{
  "email": "student@example.com",
  "secret": "your-secret-key",
  "url": "https://tdsbasictest.vercel.app/quiz/1"
}
```
The request is validated against the **Pydantic** model defined in `main.py`.

---

## 🛠️ Core Components (high‑level)
- **`app.graph.graph`** – builds the LangGraph workflow (`create_quiz_graph`).
- **`app.nodes.*`** – individual graph nodes (`fetch`, `agent`, `submit`, `feedback`).
- **`app.tools.*`** – sandboxed tools (`python_tool`, `javascript_tool`, `download_file_tool`, `submit_answer_tool`).
- **`app.resources.browser`** – Playwright wrapper for headless Chromium interactions.
- **`app.resources.llm`** – provider‑agnostic LLM client (Google, Anthropic, OpenAI, …).
- **`app.utils.helpers`** – temporary‑directory management and cleanup utilities.
- **`app.utils.logging`** – structured logging with timestamps.

---

## 🧪 Testing

The repository includes a **pytest** suite under `tests/`.
```bash
uv run pytest -q
```
Key test modules:
- `tests/test_resources/test_api.py` – API endpoint sanity checks.
- `tests/test_resources/test_browser.py` – Playwright launch & navigation sanity.
- `tests/test_resources/test_llm.py` – Mocked LLM responses.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome‑thing`).
3. Ensure code passes linting (`ruff .`) and tests.
4. Open a Pull Request with a clear description of the changes.

---

## 📜 License

This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

## 📞 Contact

- **Name:** Mayank Kumar Poddar
- **Email:** 23f3004197@ds.study.iitm.ac.in
- **GitHub:** https://github.com/mayanklearns/yantrasolve

Feel free to open an issue on GitHub for bugs, feature requests, or general questions.

---

*Happy solving!*
