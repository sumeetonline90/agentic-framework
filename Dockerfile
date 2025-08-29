# Agentic Framework Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash agentic && \
    chown -R agentic:agentic /app

# Switch to non-root user
USER agentic

# Expose port (if needed for web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from main import AgenticFramework; asyncio.run(AgenticFramework().get_status())" || exit 1

# Default command
CMD ["python", "main.py"]
