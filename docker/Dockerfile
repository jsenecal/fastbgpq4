# Use official bgpq4 image to get the binary
FROM ghcr.io/bgp/bgpq4:latest AS bgpq4

# Runtime image with Python app
FROM python:3.14-alpine

# Copy bgpq4 binary from official image
COPY --from=bgpq4 /bgp/bgpq4 /usr/local/bin/bgpq4

# Set working directory
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .python-version README.md ./
COPY app ./app

# Install dependencies
RUN uv pip install --system --no-cache .

# Create non-root user
RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
