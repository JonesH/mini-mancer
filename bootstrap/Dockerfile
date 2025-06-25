FROM python:3.13-slim

WORKDIR /app

# Install curl for health checks and uv
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/
COPY main.py .
COPY web_main.py .

# Create data directory
RUN mkdir -p data

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 14159

# Default to dual-interface deployment (both Telegram and FastAPI)
CMD ["uv", "run", "python", "web_main.py"]