# Multi-stage / optimized Python container for MS Furniture Gallery
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_ENV=production

# Set working directory
WORKDIR /app

# Install system dependencies (build-essential for compiling C-extensions if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure instance and uploads directories exist with appropriate permissions
RUN mkdir -p instance static/uploads

# Expose port
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start gunicorn production server
CMD ["gunicorn", "wsgi:app", "--workers", "4", "--threads", "2", "--bind", "0.0.0.0:5000", "--timeout", "120"]
