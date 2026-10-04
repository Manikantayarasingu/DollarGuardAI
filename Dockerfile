# ============================================================
# DollarGuard AI - Production Docker Image
# ============================================================

FROM python:3.11-slim

# Prevent Python from creating .pyc files
# and ensure logs appear immediately.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Application directory
WORKDIR /app

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file first for Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        pypdf \
        reportlab \
        "python-jose[cryptography]" \
        "passlib[bcrypt]" \
        python-multipart \
        pytest \
        bcrypt==4.0.1 \
        httpx==0.28.1

# Copy application
COPY app ./app
COPY data ./data
COPY documents ./documents
COPY scripts ./scripts
COPY config ./config
COPY tests ./tests

# Create runtime directories
RUN mkdir -p logs

# API port
EXPOSE 8000

# Production API server
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]