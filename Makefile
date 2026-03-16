.PHONY: help install dev test lint format clean run docker docs

# Default target
help:
	@echo "Graph-to-Agent Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install package in production mode"
	@echo "  make dev         Install package with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test        Run tests with coverage"
	@echo "  make lint        Run linter (ruff)"
	@echo "  make format      Format code (ruff)"
	@echo "  make typecheck   Run type checker (mypy)"
	@echo ""
	@echo "Running:"
	@echo "  make run         Run the Flask web app"
	@echo "  make run-docker  Run with Docker Compose"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       Remove build artifacts"
	@echo ""

# Installation
install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pre-commit install

# Testing
test:
	pytest tests/ -v --cov=src/graph_to_agent --cov-report=term-missing

test-quick:
	pytest tests/ -v -x

# Linting and formatting
lint:
	ruff check src/ tests/ controllers/ logics/

format:
	ruff format src/ tests/ controllers/ logics/
	ruff check --fix src/ tests/ controllers/ logics/

typecheck:
	mypy src/graph_to_agent

# Running the app
run:
	python -m flask --app app:app run --debug --port 5000

run-prod:
	gunicorn -w 4 -b 0.0.0.0:8080 app:app

# Docker
docker-build:
	docker build -t graph-to-agent -f docker/Dockerfile .

docker-run:
	docker run -p 8080:8080 --env-file .env graph-to-agent

docker-compose:
	docker-compose -f docker/docker-compose.yml up

docker-compose-dev:
	docker-compose -f docker/docker-compose.yml up dev

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	pip install build
	python -m build

# Publish to PyPI (use with caution)
publish: build
	pip install twine
	twine upload dist/*

# Generate documentation
docs:
	@echo "TODO: Add documentation generation"
