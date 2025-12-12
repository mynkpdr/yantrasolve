# Makefile
.PHONY: start test format lint help clean

# Run FastAPI locally
start:
	uv run main.py

# Run tests
test:
	uv run pytest

# Format code
format:
	uv run black app tests

# Lint code
lint:
	uv run ruff check app tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf /tmp/quiz_files
	rm -rf /tmp/quiz_cache
	rm -rf /tmp/quiz_logs


# Show help
help:
	@echo "Available make commands:"
	@echo ""
	@echo "make start  - Run FastAPI server"
	@echo "make test   - Run pytest tests"
	@echo "make format - Format code with black"
	@echo "make lint   - Lint code with ruff"
	@echo "make clean  - Clean up temporary files"
	@echo "make help   - Show this help message"