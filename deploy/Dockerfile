# Dockerfile for Traffic Collector Daemon
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system traffic-collector && \
    useradd --system --gid traffic-collector --shell /bin/false \
    --home-dir /var/lib/traffic-collector --create-home traffic-collector

# Copy requirements and install Python dependencies
COPY requirements-vm.txt .
RUN pip install --no-cache-dir -r requirements-vm.txt

# Copy application files
COPY traffic_collector_daemon.py .
COPY config/collector_config.yaml /etc/traffic-collector/config.yaml

# Create directories and set permissions
RUN mkdir -p /var/lib/traffic-collector /var/log && \
    chown -R traffic-collector:traffic-collector /var/lib/traffic-collector /var/log /app

# Switch to non-root user
USER traffic-collector

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Expose port
EXPOSE 8080

# Run the daemon
CMD ["python", "traffic_collector_daemon.py", "start", "--foreground", "--config", "/etc/traffic-collector/config.yaml"]