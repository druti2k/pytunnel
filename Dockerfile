FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requerments.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requerments.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p certs logs

# Create non-root user
RUN useradd -m -u 1000 pytunnel && \
    chown -R pytunnel:pytunnel /app

# Switch to non-root user
USER pytunnel

# Expose ports
EXPOSE 8765 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f -k https://localhost:8081/health || exit 1

# Run the application
CMD ["python", "pytunnel.py", "server"]
