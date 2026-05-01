# Use Python 3.11 stable base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy entire project
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Expose port 7860 (required by Hugging Face Spaces)
EXPOSE 7860

# Set environment variables for HF Spaces
ENV FLASK_PORT=7860
ENV PYTHONUNBUFFERED=1

# Run the Flask app
CMD ["python", "backend/src/main.py"]
