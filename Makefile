SHELL := /bin/bash
PROJECT_ROOT := /Users/pranjalsingh/Project\ Simple
BACKEND_PORT := 5002
FRONTEND_PORT := 5003
UVICORN := $(PROJECT_ROOT)/.venv/bin/uvicorn

.PHONY: restart start stop kill-backend kill-frontend start-backend start-frontend

restart: stop start

start: start-backend start-frontend

stop: kill-backend kill-frontend

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

start-backend:
	@echo "Starting backend on port $(BACKEND_PORT)..."
	@cd $(PROJECT_ROOT) && \
		PYTHONPATH=backend $(UVICORN) api.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT) > backend.log 2>&1 &
	@echo " - backend logs: $$(pwd)/backend.log"

start-frontend:
	@echo "Starting frontend on port $(FRONTEND_PORT)..."
	@cd $(PROJECT_ROOT)/frontend && \
		npm run dev -- --host --port $(FRONTEND_PORT) > ../frontend.log 2>&1 &
	@echo " - frontend logs: $$(pwd)/frontend.log"
