# SmartCampus 360 - FastAPI Backend Dockerfile
FROM python:3.12-slim

# Prevent writing .pyc files and enable unbuffered output for live log streaming
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app

# Install system dependencies (curl for healthchecks, gcc and libpq for PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy Alembic migration config and backend application code
COPY alembic.ini /app/alembic.ini
COPY backend /app/backend

# Create uploads storage directory
RUN mkdir -p /app/uploads/tickets

# Ensure entrypoint script is executable
RUN chmod +x /app/backend/entrypoint.sh

# Expose backend application port
EXPOSE 8000

# Healthcheck probe using the /health endpoint
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/backend/entrypoint.sh"]
