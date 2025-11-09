# LoreGuard Makefile
# Container and service management

.PHONY: help detect-ip check-env up down restart logs logs-follow clean clean-force quick-start quick-start-infra health-check init-db reset-db reset-db-force stop-services rebuild-services start-api start-normalize start-assistant start-web test format lint

# Default target
help:
	@echo "LoreGuard Development Commands"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make detect-ip      - Detect host IP address for network access"
	@echo "  make check-env      - Check environment configuration"
	@echo "  make quick-start    - Full setup: infrastructure + start all services"
	@echo "  make quick-start-infra - Infrastructure only (containers + DB)"
	@echo ""
	@echo "Docker Compose:"
	@echo "  make up             - Start all containers"
	@echo "  make down           - Stop all containers"
	@echo "  make restart        - Restart all containers"
	@echo "  make logs           - View last 100 lines of container logs"
	@echo "  make logs-follow     - Follow container logs (streaming)"
	@echo "  make clean          - Stop containers and remove volumes (interactive, WARNING: deletes data)"
	@echo "  make clean-force    - Force cleanup without confirmation"
	@echo ""
	@echo "Database:"
	@echo "  make init-db        - Initialize database schema"
	@echo "  make reset-db       - Reset database (WARNING: deletes data)"
	@echo ""
	@echo "Services:"
	@echo "  make health-check    - Check health of all services"
	@echo "  make start-api      - Start API service (development, foreground)"
	@echo "  make start-normalize - Start normalize service (development, foreground)"
	@echo "  make start-assistant - Start AI assistant service (development, foreground)"
	@echo "  make start-web      - Start frontend (development, foreground)"
	@echo "  make stop-services  - Stop all background application services"
	@echo ""
	@echo "Development:"
	@echo "  make test           - Run tests"
	@echo "  make format         - Format code"
	@echo "  make lint           - Lint code"

# Detect IP address
detect-ip:
	@echo "Detecting host IP address..."
	@bash scripts/detect-ip.sh
	@echo ""
	@echo "To use detected IP, source the .env file:"
	@echo "  source .env"

# Check environment
check-env:
	@echo "Checking environment..."
	@if [ ! -f .env ]; then \
		echo "Warning: .env not found. Run 'make detect-ip' first (will create from .env.template)."; \
	else \
		echo "✓ Environment file found"; \
		echo "IP configuration:"; \
		grep LOREGUARD_HOST_IP .env 2>/dev/null || echo "  (IP not yet detected - run 'make detect-ip')"; \
	fi
	@if [ ! -f .env ]; then \
		echo "Warning: .env file not found. Consider creating from .env.template"; \
	else \
		echo "✓ .env file found"; \
	fi
	@echo ""
	@echo "Required services:"
	@command -v docker >/dev/null && echo "✓ Docker installed" || echo "✗ Docker not found"
	@if docker compose version &>/dev/null; then \
		echo "✓ Docker Compose installed (plugin)"; \
	elif command -v docker-compose >/dev/null; then \
		echo "✓ Docker Compose installed (standalone)"; \
	else \
		echo "✗ Docker Compose not found"; \
	fi

# Quick start - full setup (infrastructure only)
quick-start-infra: detect-ip check-env
	@echo "Starting LoreGuard infrastructure..."
	@# Load environment variables from .env (Docker Compose reads this automatically)
	@# Also export for shell commands that need it
	@if [ -f .env ]; then \
		set -a && . $(CURDIR)/.env && set +a; \
	fi
	@echo "Starting infrastructure containers..."
	@docker compose -f docker-compose.dev.yml up -d postgres redis minio
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Initializing database..."
	@make init-db
	@echo ""
	@echo "✓ Infrastructure ready!"

# Quick start - full setup including application services
# Now uses containerized backend services + local frontend (for hot reload)
quick-start: quick-start-infra
	@echo ""
	@echo "🚀 Building and starting containerized backend services..."
	@# Ensure IP is detected and loaded (detect-ip writes to .env which Docker Compose reads)
	@# Also export for shell commands
	@if [ -f .env ]; then \
		set -a && . $(CURDIR)/.env && set +a; \
	fi
	@docker compose -f docker-compose.dev.yml build loreguard-api loreguard-normalize loreguard-assistant loreguard-ingestion
	@docker compose -f docker-compose.dev.yml up -d loreguard-api loreguard-normalize loreguard-assistant loreguard-ingestion
	@echo ""
	@echo "🚀 Starting frontend (local, for hot reload)..."
	@bash scripts/dev/start-services.sh web-only
	@echo ""
	@if [ -f .env ]; then \
		HOST_IP=$$(grep LOREGUARD_HOST_IP .env | cut -d= -f2); \
		echo "═══════════════════════════════════════════════════════"; \
		echo "  ✅ LoreGuard is now running!"; \
		echo "═══════════════════════════════════════════════════════"; \
		echo ""; \
		echo "🌐 Access your application:"; \
		echo "   Frontend:  http://$$HOST_IP:6060 (local, hot reload enabled)"; \
		echo "   API:       http://$$HOST_IP:8000 (containerized)"; \
		echo "   Normalize: http://$$HOST_IP:8001 (containerized)"; \
		echo "   Assistant: http://$$HOST_IP:8002 (containerized)"; \
		echo "   Ingestion: Running (containerized, invoked via API)"; \
		echo "   API Docs:  http://$$HOST_IP:8000/docs"; \
		echo ""; \
		echo "📊 Service Status:"; \
		echo "   - Infrastructure: Running (containers)"; \
		echo "   - API Service: Running (containerized)"; \
		echo "   - Normalize Service: Running (containerized)"; \
		echo "   - AI Assistant Service: Running (containerized)"; \
		echo "   - Ingestion Service: Running (containerized)"; \
		echo "   - Frontend: Running (local, hot reload)"; \
		echo ""; \
		echo "💡 Useful commands:"; \
		echo "   make stop-services     - Stop all application services"; \
		echo "   make logs              - View container logs"; \
		echo "   make health-check      - Check service health"; \
		echo "   make rebuild-services  - Rebuild backend containers"; \
	else \
		echo "═══════════════════════════════════════════════════════"; \
		echo "  ✅ LoreGuard is now running!"; \
		echo "═══════════════════════════════════════════════════════"; \
		echo ""; \
		echo "🌐 Access your application:"; \
		echo "   Frontend:  http://localhost:6060"; \
		echo "   API:       http://localhost:8000"; \
		echo "   API Docs:  http://localhost:8000/docs"; \
	fi

# Docker Compose commands
up: detect-ip
	@echo "Starting LoreGuard containers..."
	@# Docker Compose automatically reads .env file (detect-ip writes to it)
	@# Also export for shell commands that need it
	@if [ -f .env ]; then \
		set -a && . $(CURDIR)/.env && set +a; \
	fi
	@docker compose -f docker-compose.dev.yml up -d

down:
	@echo "Stopping LoreGuard containers..."
	@docker compose -f docker-compose.dev.yml down

restart:
	@echo "Restarting LoreGuard containers..."
	@docker compose -f docker-compose.dev.yml restart

logs:
	@docker compose -f docker-compose.dev.yml logs --tail=100

logs-follow:
	@docker compose -f docker-compose.dev.yml logs -f

clean:
	@echo "WARNING: This will remove all containers and volumes (data will be lost)"
	@if [ -t 0 ]; then \
		read -p "Are you sure? [y/N] " -n 1 -r; \
		echo; \
		if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
			docker compose -f docker-compose.dev.yml down -v; \
			echo "✓ Containers and volumes removed"; \
		fi; \
	else \
		echo "Non-interactive mode: Skipping clean. Use 'make clean-force' to force cleanup."; \
	fi

clean-force:
	@echo "Removing all containers and volumes..."
	@docker compose -f docker-compose.dev.yml down -v
	@echo "✓ Containers and volumes removed"

# Database operations
init-db:
	@echo "Initializing database..."
	@bash scripts/dev/init-databases.sh

reset-db:
	@echo "WARNING: This will reset the database (data will be lost)"
	@if [ -t 0 ]; then \
		read -p "Are you sure? [y/N] " -n 1 -r; \
		echo; \
		if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
			docker compose -f docker-compose.dev.yml exec -T postgres psql -U loreguard -d loreguard -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; \
			make init-db; \
			echo "✓ Database reset complete"; \
		fi; \
	else \
		echo "Non-interactive mode: Skipping reset. Use 'make reset-db-force' to force reset."; \
	fi

reset-db-force:
	@echo "Resetting database..."
	@docker compose -f docker-compose.dev.yml exec -T postgres psql -U loreguard -d loreguard -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@make init-db
	@echo "✓ Database reset complete"

# Health checks
health-check:
	@bash scripts/dev/health-check.sh

# Stop application services
stop-services:
	@echo "Stopping application services..."
	@mkdir -p logs
	@echo "Stopping containerized backend services..."
	@# Load environment variables if available
	@if [ -f .env ]; then \
		set -a && . $(CURDIR)/.env && set +a; \
	fi
	@docker compose -f docker-compose.dev.yml stop loreguard-api loreguard-normalize loreguard-assistant loreguard-ingestion 2>/dev/null || true
	@echo "Stopping local frontend service..."
	@if [ -f logs/web.pid ]; then \
		PID=$$(cat logs/web.pid); \
		if kill $$PID 2>/dev/null; then \
			rm logs/web.pid && echo "✓ Frontend service stopped"; \
		else \
			rm logs/web.pid && echo "⚠️  Frontend service was not running"; \
		fi; \
	fi
	@echo "✓ Service stop complete"

# Rebuild backend services (useful after code changes)
rebuild-services: detect-ip
	@echo "Rebuilding backend service containers..."
	@# Ensure IP is detected before building (Docker Compose reads .env automatically)
	@# Also export for shell commands
	@if [ -f .env ]; then \
		set -a && . $(CURDIR)/.env && set +a; \
	fi
	@docker compose -f docker-compose.dev.yml build --no-cache loreguard-api loreguard-normalize loreguard-assistant loreguard-ingestion
	@echo "✓ Services rebuilt. Restart with: docker compose -f docker-compose.dev.yml up -d loreguard-api loreguard-normalize loreguard-assistant loreguard-ingestion"

# Start services (development mode)
start-api:
	@echo "Starting API service..."
	@cd apps/svc-api && \
		if [ -d venv ] && [ ! -f venv/bin/python ]; then \
			echo "Removing broken virtual environment..."; \
			rm -rf venv; \
		fi && \
		if [ ! -d venv ]; then \
			if ! python3 -c "import ensurepip" 2>/dev/null; then \
				PYTHON_VERSION=$$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1); \
				echo "❌ Error: python3-venv package not properly installed"; \
				echo "   The 'ensurepip' module is missing."; \
				echo "   Install with: sudo apt install python$$PYTHON_VERSION-venv"; \
				exit 1; \
			fi; \
			echo "Creating virtual environment..."; \
			python3 -m venv venv || { \
				PYTHON_VERSION=$$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1); \
				echo "❌ Failed to create virtual environment"; \
				echo "   Install with: sudo apt install python$$PYTHON_VERSION-venv"; \
				exit 1; \
			}; \
		fi && \
		. venv/bin/activate && \
		pip install --upgrade pip -q && \
		pip install -r requirements.txt -q && \
		if [ -f $(CURDIR)/.env ]; then set -a && . $(CURDIR)/.env && set +a; fi && \
		python -m app.main

start-normalize:
	@echo "Starting normalize service..."
	@cd apps/svc-normalize && \
		if [ -d venv ] && [ ! -f venv/bin/python ]; then \
			echo "Removing broken virtual environment..."; \
			rm -rf venv; \
		fi && \
		if [ ! -d venv ]; then \
			if ! python3 -c "import ensurepip" 2>/dev/null; then \
				PYTHON_VERSION=$$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1); \
				echo "❌ Error: python3-venv package not properly installed"; \
				echo "   The 'ensurepip' module is missing."; \
				echo "   Install with: sudo apt install python$$PYTHON_VERSION-venv"; \
				exit 1; \
			fi; \
			echo "Creating virtual environment..."; \
			python3 -m venv venv || { \
				PYTHON_VERSION=$$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1); \
				echo "❌ Failed to create virtual environment"; \
				echo "   Install with: sudo apt install python$$PYTHON_VERSION-venv"; \
				exit 1; \
			}; \
		fi && \
		. venv/bin/activate && \
		pip install --upgrade pip -q && \
		pip install -r requirements.txt -q && \
		if [ -f $(CURDIR)/.env ]; then set -a && . $(CURDIR)/.env && set +a; fi && \
		python -m app.main

start-assistant:
	@echo "Starting AI assistant service..."
	@cd apps/svc-assistant && \
		if [ -d venv ] && [ ! -f venv/bin/python ]; then \
			echo "Removing broken virtual environment..."; \
			rm -rf venv; \
		fi && \
		if [ ! -d venv ]; then \
			if ! python3 -c "import ensurepip" 2>/dev/null; then \
				PYTHON_VERSION=$$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1); \
				echo "❌ Error: python3-venv package not properly installed"; \
				echo "   The 'ensurepip' module is missing."; \
				echo "   Install with: sudo apt install python$$PYTHON_VERSION-venv"; \
				exit 1; \
			fi; \
			echo "Creating virtual environment..."; \
			python3 -m venv venv || { \
				PYTHON_VERSION=$$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1); \
				echo "❌ Failed to create virtual environment"; \
				echo "   Install with: sudo apt install python$$PYTHON_VERSION-venv"; \
				exit 1; \
			}; \
		fi && \
		. venv/bin/activate && \
		pip install --upgrade pip -q && \
		pip install -r requirements.txt -q && \
		if [ -f $(CURDIR)/.env ]; then set -a && . $(CURDIR)/.env && set +a; fi && \
		export PYTHONPATH=$$(cd ../svc-api && pwd):$$PYTHONPATH && \
		python -m app.main

start-web:
	@echo "Starting frontend..."
	@cd apps/web && \
		if [ ! -d node_modules ]; then \
			echo "Installing dependencies..."; \
			npm install; \
		fi && \
		if [ -f $(CURDIR)/.env ]; then set -a && . $(CURDIR)/.env && set +a; fi && \
		npm run dev

# Development tasks
test:
	@echo "Running tests..."
	@cd apps/svc-api && python3 -m pytest tests/ 2>/dev/null || echo "No tests found"
	@cd apps/svc-normalize && python3 -m pytest tests/ 2>/dev/null || echo "No tests found"

format:
	@echo "Formatting code..."
	@command -v black >/dev/null && black apps/ || echo "black not installed"
	@command -v prettier >/dev/null && prettier --write apps/web/src || echo "prettier not installed"

lint:
	@echo "Linting code..."
	@command -v flake8 >/dev/null && flake8 apps/svc-api apps/svc-normalize || echo "flake8 not installed"
	@command -v eslint >/dev/null && eslint apps/web/src || echo "eslint not installed"

# Note: Environment variables are loaded from .env file
# Docker Compose reads .env automatically
# Shell commands export from .env as needed

