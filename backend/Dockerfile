# ==============================================================================
# Production Dockerfile for Jet Freight Logistics Credit Control CRM Backend
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install minimal OS runtime packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root unprivileged application user (CWE-250)
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -m -d /app -s /bin/bash appuser

# Copy application code and logo
COPY --chown=appuser:appuser backend/app /app/backend/app
COPY --chown=appuser:appuser jfll-logo.jpeg /app/jfll-logo.jpeg

# Prepare storage directory with proper permissions
RUN mkdir -p /app/backend/storage/uploads /app/backend/storage/memos && \
    chown -R appuser:appuser /app/backend/storage

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8001/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
