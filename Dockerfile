# Stage 1: Build dependencies and compile bytecode
FROM python:3.11-slim AS builder

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary from the official Astral image for high-speed builds
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable dynamic Python bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency specifications for caching
COPY pyproject.toml uv.lock ./

# Install python dependencies in isolated virtual environment
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application source code
COPY src/ ./src/

# Package the application
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Stage 2: Clean runtime target
FROM python:3.11-slim AS runtime

# Create secure system non-root group and user
RUN groupadd -r appgroup && useradd -r -g appgroup -s /sbin/nologin appuser

# Configure optimal production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy the built virtual environment and application source with correct permissions
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src

# Set strict non-privileged user boundary
USER appuser

# Expose primary API endpoint
EXPOSE 8000

# Standard container healthcheck using lightweight python HTTP request check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=5)"

# Entry point execution command
CMD ["uvicorn", "pnetai_chatbot.main:app", "--host", "0.0.0.0", "--port", "8000"]
