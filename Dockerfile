# Use Python 3.11 Alpine for minimal image size
FROM python:3.11-alpine

# Install system dependencies (ImageMagick and GhostScript)
# ImageMagick: PDF to PNG conversion
# GhostScript: PDF pre-processing for better compatibility
RUN apk add --no-cache \
    imagemagick \
    ghostscript \
    imagemagick-pdf

# Set working directory
WORKDIR /app

# Copy requirements (no runtime dependencies, only dev dependencies for potential debugging)
COPY requirements.txt .
# No pip install needed - all stdlib!

# Copy application source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "src.main"]
