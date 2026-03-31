# BrahmaAI Makefile
# Run `make help` to see all commands

.PHONY: help install dev test lint clean docker-up docker-down

## ── General ──────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  BrahmaAI Development Commands"
	@echo "  ─────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

## ── Setup ────────────────────────────────────────────────────────────────────

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install Python backend dependencies
	cd backend && python -m venv .venv && \
	. .venv/bin/activate && \
	pip install -r requirements.txt

install-frontend: ## Install Node.js frontend dependencies
	cd frontend && npm install

## ── Development ──────────────────────────────────────────────────────────────

dev: ## Start both backend and frontend in dev mode (requires tmux or two terminals)
	@echo "Starting backend on :8000 and frontend on :3000"
	@echo "Run these in separate terminals:"
	@echo "  make backend"
	@echo "  make frontend"

backend: ## Start backend dev server
	cd backend && . .venv/bin/activate && \
	uvicorn backend.main:app --reload --port 8000

frontend: ## Start frontend dev server
	cd frontend && npm run dev

## ── Testing ──────────────────────────────────────────────────────────────────

test: test-backend ## Run all tests

test-backend: ## Run Python backend tests
	cd backend && . .venv/bin/activate && \
	pytest tests/ -v --tb=short

test-watch: ## Run tests in watch mode
	cd backend && . .venv/bin/activate && \
	pytest tests/ -v --tb=short -f

## ── Code Quality ─────────────────────────────────────────────────────────────

lint: ## Run linters (ruff + mypy + eslint)
	cd backend && . .venv/bin/activate && \
	ruff check . && mypy . --ignore-missing-imports
	cd frontend && npm run lint

format: ## Auto-format code
	cd backend && . .venv/bin/activate && \
	ruff format .

typecheck: ## TypeScript type checking
	cd frontend && npx tsc --noEmit

## ── Docker ───────────────────────────────────────────────────────────────────

docker-up: ## Start full stack with Docker Compose
	docker-compose up --build -d

docker-down: ## Stop Docker Compose stack
	docker-compose down

docker-logs: ## Follow Docker Compose logs
	docker-compose logs -f

docker-rebuild: ## Rebuild and restart
	docker-compose down && docker-compose up --build -d

## ── Database / Memory ────────────────────────────────────────────────────────

clear-memory: ## Clear FAISS vector index
	rm -f backend/data/faiss_index.index backend/data/faiss_index.meta.json
	@echo "Memory cleared."

## ── Clean ────────────────────────────────────────────────────────────────────

clean: ## Remove all build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null; true
	rm -rf frontend/.next frontend/node_modules
	rm -rf backend/.venv
	@echo "Cleaned."

## ── Utilities ────────────────────────────────────────────────────────────────

setup-env: ## Copy .env.example to .env
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env — please fill in your API keys."; \
	else \
		echo ".env already exists."; \
	fi

api-docs: ## Open API docs in browser
	open http://localhost:8000/api/docs

demo: ## Print demo task examples
	@echo ""
	@echo "  BrahmaAI Demo Tasks"
	@echo "  ───────────────────"
	@echo "  1. 'Search for the latest AI trends in 2025 and create a report'"
	@echo "  2. 'Generate a FastAPI app for a todo list with full CRUD'"
	@echo "  3. 'Plan a 5-day trip to Tokyo with a \$$2000 budget'"
	@echo "  4. 'Summarize the PDF at /tmp/report.pdf'"
	@echo ""
