# =====================================================
# AI Log Analyzer — Backend Dockerfile
# Multi-stage: build → production
# =====================================================

# Stage 1: dependency builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# Stage 2: production runtime
FROM python:3.12-slim

WORKDIR /app

# Runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -m -u 1001 appuser

# Copy installed packages
COPY --from=builder /install /usr/local

# Copy application
COPY app/ ./app/

# Create upload directory with correct permissions for the app user
RUN mkdir -p /app/uploads && \
    chown -R appuser:appuser /app/uploads && \
    chmod 755 /app/uploads

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
