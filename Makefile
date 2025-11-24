# Makefile
.PHONY: start test format lint help

# Run FastAPI locally
start:
	uv run main.py

# Run tests
test:
	uv run pytest

# Format code
format:
	uv run black src tests

# Lint code
lint:
	uv run ruff check src tests

# Show help
help:
	@echo "Available make commands:"
	@echo ""
	@echo "make start  - Run FastAPI server"
	@echo "make test   - Run pytest tests"
	@echo "make format - Format code with black"
	@echo "make lint   - Lint code with ruff"