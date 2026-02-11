# ──────────────────────────────────────────────
# Shortlist — Development & Deployment Commands
# ──────────────────────────────────────────────
# Usage: make <target>
# Run `make help` to see all available commands.
# ──────────────────────────────────────────────

.PHONY: help dev dev-backend dev-frontend test lint clean migrate

# ── Defaults ──
PYTHON := python
PIP := pip
NPM := npm

# ──────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────
help: ## Show this help message
	@echo "Shortlist — Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ──────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────
dev: ## Start both backend and frontend in development mode
	@echo "Starting Shortlist development servers..."
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## Start backend development server
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && $(NPM) run dev

# ──────────────────────────────────────────────
# Testing
# ──────────────────────────────────────────────
test: ## Run all backend tests
	cd backend && $(PYTHON) -m pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	cd backend && $(PYTHON) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-fast: ## Run tests quickly (no verbose)
	cd backend && $(PYTHON) -m pytest tests/ -q

# ──────────────────────────────────────────────
# Linting & Type Checking
# ──────────────────────────────────────────────
lint: ## Run linters on backend code
	cd backend && flake8 app/ --max-line-length=120 --statistics
	cd backend && pylint app/ --errors-only --disable=E0401

lint-frontend: ## Run frontend linter
	cd frontend && $(NPM) run lint

typecheck: ## Run TypeScript type checking
	cd frontend && npx tsc --noEmit

# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────
migrate: ## Apply all database migrations
	cd backend && $(PYTHON) apply_migration.py

# ──────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────
clean: ## Remove build artifacts, caches, and temp files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/coverage.xml

health: ## Check backend health
	curl -s http://localhost:8000/health | python -m json.tool

health-deep: ## Deep health check (DB + LLM)
	curl -s http://localhost:8000/health/deep | python -m json.tool

metrics: ## View application metrics
	curl -s http://localhost:8000/metrics | python -m json.tool

secret: ## Generate a production SECRET_KEY
	@$(PYTHON) -c "import secrets; print(secrets.token_urlsafe(64))"
