# Use Python 3.11 stable base image - FORCE THIS VERSION
FROM python:3.11-slim

# Set Python version explicitly - FORCE PYTHON 3.11
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_PREFER_BINARY=1

# Verify Python version
RUN python --version && which python

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Force binary wheels - avoid any source compilation
RUN pip install --upgrade pip setuptools wheel && \
    pip install --only-binary=:all: --no-deps --force-reinstall \
    pandas==2.2.2 \
    numpy==1.26.4 \
    scikit-learn==1.4.2 \
    scipy==1.11.4 || true

# Install remaining dependencies (should be binary compatible)
RUN pip install --no-cache-dir \
    pandas==2.2.2 \
    numpy==1.26.4 \
    scikit-learn==1.4.2 \
    scipy==1.11.4 \
    Flask==2.3.3 \
    Flask-CORS==4.0.0 \
    Flask-SQLAlchemy==3.0.5 \
    Flask-Bcrypt==1.0.1 \
    Flask-JWT-Extended==4.5.2 \
    python-dotenv==1.0.0 \
    requests==2.31.0 \
    alpha-vantage==2.3.1 \
    python-telegram-bot==20.1 \
    schedule==1.2.0 \
    gunicorn==21.2.0 \
    cryptography>=41.0.0 \
    PyJWT>=2.8.0 \
    APScheduler==3.10.4 \
    huggingface_hub>=1.13.0 \
    transformers>=4.30.0 \
    uvicorn>=0.23.2

# Note: MetaTrader5 removed - not supported on Linux/Render

# Copy entire project
COPY . /app

# Expose port 7860 (required by Hugging Face Spaces)
EXPOSE 7860

# Set environment variables for HF Spaces
ENV FLASK_PORT=7860

# Run the Flask app from backend/src
CMD ["python", "src/main.py"]
