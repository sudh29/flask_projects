.PHONY: test lint clean help

help:
	@echo "Available commands:"
	@echo "  make test   - Run test suites across all 6 Flask projects"
	@echo "  make lint   - Run Ruff linter across the repository"
	@echo "  make clean  - Clean python bytecode and test databases"

test:
	@echo "=== Running Flask projects test suite ==="
	uv run pytest

lint:
	uv run ruff check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.db" -delete

