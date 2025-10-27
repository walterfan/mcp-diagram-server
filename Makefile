.PHONY: help install test test-cov test-verbose lint format clean run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	poetry install

test: ## Run tests with pytest
	poetry run pytest test/

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=mcp_diagram_server --cov-report=html --cov-report=term test/

test-verbose: ## Run tests with verbose output
	poetry run pytest -v test/

lint: ## Lint code with ruff
	poetry run ruff check .

format: ## Format code with black
	poetry run black .

clean: ## Clean temporary files
	rm -rf __pycache__/ .pytest_cache/ .coverage htmlcov/ dist/ *.egg-info/
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the MCP diagram server
	poetry run uvicorn mcp_diagram_server:app --host 0.0.0.0 --port 8050 --reload

install-local: ## Install dependencies without Poetry (using pip)
	pip install fastapi uvicorn graphviz requests python-dotenv pytest pytest-cov httpx black ruff

all: install test lint ## Install, test, and lint
