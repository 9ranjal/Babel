SHELL := /bin/bash
.ONESHELL:

ROOT_DIR := $(abspath .)
BACKEND_DIR := $(ROOT_DIR)/backend
FRONTEND_DIR := $(ROOT_DIR)/frontend

.PHONY: backend frontend runner dev

backend:
	cd "$(BACKEND_DIR)"
	if [ -f "../.venv/bin/activate" ]; then \
		. ../.venv/bin/activate; \
	fi; \
	PYTHONPATH="$(BACKEND_DIR)" uvicorn api.main:app --reload --port 5002

runner:
	cd "$(BACKEND_DIR)"
	if [ -f "../.venv/bin/activate" ]; then \
		. ../.venv/bin/activate; \
	fi; \
	PYTHONPATH="$(BACKEND_DIR)" python -m api.workers.runner

frontend:
	npm --prefix "$(FRONTEND_DIR)" run dev -- --port 3000

dev:
	@set -euo pipefail
	@trap 'kill 0' EXIT
	@$(MAKE) --no-print-directory backend &
	@$(MAKE) --no-print-directory frontend &
	@wait
SHELL := /bin/bash
PROJECT_ROOT := /Users/pranjalsingh/Project\ Simple
BACKEND_PORT := 5002
FRONTEND_PORT := 5003
UVICORN := $(PROJECT_ROOT)/.venv/bin/uvicorn

.PHONY: restart start stop kill-backend kill-frontend kill-all start-backend start-frontend start-runner start-workers

restart: stop start

start: start-backend start-frontend

stop: kill-all

kill-backend:
	@echo "Killing backend on port $(BACKEND_PORT) if running..."
	@PIDS=$$(lsof -ti:$(BACKEND_PORT)) ; \
	if [ -n "$$PIDS" ]; then \
		echo " - terminating backend process(es): $$PIDS" ; \
		kill $$PIDS ; \
	else \
		echo " - no backend process found" ; \
	fi

kill-frontend:
	@echo "Killing frontend on port $(FRONTEND_PORT) if running..."
	@PIDS=$$(lsof -ti:$(FRONTEND_PORT)) ; \
	if [ -n "$$PIDS" ]; then \
		echo " - terminating frontend process(es): $$PIDS" ; \
		kill $$PIDS ; \
	else \
		echo " - no frontend process found" ; \
	fi

kill-all:
	@echo "🔪 Killing ALL Babel-related processes..."
	@echo "Looking for processes by name..."
	@pkill -f "uvicorn.*api.main:app" 2>/dev/null && echo "✅ Killed uvicorn backend processes" || true
	@pkill -f "python.*api.workers.runner" 2>/dev/null && echo "✅ Killed worker runner processes" || true
	@pkill -f "vite" 2>/dev/null && echo "✅ Killed Vite frontend processes" || true
	@pkill -f "node.*vite" 2>/dev/null && echo "✅ Killed Node/Vite processes" || true
	@echo "Looking for processes on common Babel ports..."
	@for port in 3000 3001 5000 5001 5002 5003 5173 54321; do \
		if lsof -ti:$$port >/dev/null 2>&1; then \
			echo "Killing process on port $$port..."; \
			kill $$(lsof -ti:$$port) 2>/dev/null && echo "✅ Killed process on port $$port" || true; \
		fi; \
	done
	@echo "🧹 Cleanup complete! All Babel processes should be terminated."

start-backend:
start-backend: start-runner
	@echo "Starting backend on port $(BACKEND_PORT)..."
	@cd $(PROJECT_ROOT) && \
		. .venv/bin/activate && \
		PYTHONPATH=backend $(UVICORN) api.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT) > backend.log 2>&1 &
	@echo " - backend logs: $$(pwd)/backend.log"
	@echo " - worker logs:  $$(pwd)/worker.log"

start-runner:
	@echo "Starting worker runner..."
	@cd $(PROJECT_ROOT) && \
		. .venv/bin/activate && \
		PYTHONPATH=backend python -m api.workers.runner > worker.log 2>&1 &
	@echo " - worker logs: $$(pwd)/worker.log"

start-workers: start-runner

start-frontend:
	@echo "Starting frontend on port $(FRONTEND_PORT)..."
	@cd $(PROJECT_ROOT)/frontend && \
		npm run dev -- --host --port $(FRONTEND_PORT) > ../frontend.log 2>&1 &
	@echo " - frontend logs: $$(pwd)/frontend.log"
