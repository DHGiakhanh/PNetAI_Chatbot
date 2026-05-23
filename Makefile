.PHONY: run dev install lint format

# Run the server in development mode
run:
	.venv/bin/uvicorn pnetai_chatbot.interface.api.v1.router:app --host 0.0.0.0 --port 8000 --reload

# Alias for run
dev: run

# Sync dependencies with uv
install:
	uv sync

# Lint with Ruff
lint:
	uv run ruff check src/

# Format with Ruff
format:
	uv run ruff format src/
	uv run ruff check --fix src/
