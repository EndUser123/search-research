# Dockerfile for FastAPI Authentication API
# Multi-stage build for production optimization

Test Case ID: TC-DOCKER-001
Priority: High
Test Type: Container Configuration

Purpose:
Production-ready Docker configuration with security best practices,
multi-stage builds, and proper dependency management.

Algorithm Approach: Multi-stage Docker build with optimization
Time Complexity: O(1) - Image build time
Space Complexity: O(n) - Image size where n is optimized

Security Considerations:
- Non-root user execution
- Minimal attack surface
- Security scanning compatibility
- Runtime security best practices
"""

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_ENV=production
ARG APP_VERSION=1.0.0

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for Docker layer optimization
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set labels for metadata and security
LABEL maintainer="FastAPI Auth Team" \
      version="${APP_VERSION}" \
      description="FastAPI Authentication API" \
      org.opencontainers.image.title="FastAPI Auth API" \
      org.opencontainers.image.description="Secure FastAPI Authentication API" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.source="https://github.com/your-org/fastapi-auth-api" \
      org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    APP_HOME=/app

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -d ${APP_HOME} -s /bin/bash appuser

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create application directory with proper permissions
RUN mkdir -p ${APP_HOME} && \
    chown -R appuser:appuser ${APP_HOME}

# Set working directory
WORKDIR ${APP_HOME}

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser .env.example .env

# Create necessary directories
RUN mkdir -p logs data && \
    chown -R appuser:appuser logs data

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
