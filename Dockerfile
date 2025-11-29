FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Create non-root user
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV PLAYWRIGHT_BROWSERS_PATH=0

# Put venv tools in PATH *before anything else*
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies only
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Copy the entire app
COPY . /app

# Install project (and playwright dependency)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Now Playwright CLI is available, so this works:
RUN python -m playwright install chromium --with-deps

USER nonroot

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
