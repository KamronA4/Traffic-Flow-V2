# ECS-Optimized Dockerfile for Traffic Collector Daemon
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy and install Python dependencies
COPY requirements-vm.txt .
RUN pip install --user --no-cache-dir -r requirements-vm.txt
RUN pip install --user --no-cache-dir \
    boto3==1.26.137 \
    psycopg2-binary==2.9.6 \
    watchtower==3.0.1

# Final stage - minimal runtime image
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system traffic-collector && \
    useradd --system --gid traffic-collector --shell /bin/false \
    --home-dir /var/lib/traffic-collector --create-home traffic-collector

# Copy Python packages from builder
COPY --from=builder --chown=traffic-collector:traffic-collector /root/.local /home/traffic-collector/.local

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=traffic-collector:traffic-collector traffic_collector_daemon.py .
COPY --chown=traffic-collector:traffic-collector deploy/ecs/ecs_traffic_collector.py .
COPY --chown=traffic-collector:traffic-collector config/collector_config.yaml /etc/traffic-collector/config.yaml

# Create necessary directories
RUN mkdir -p /var/lib/traffic-collector /var/log/traffic-collector && \
    chown -R traffic-collector:traffic-collector /var/lib/traffic-collector /var/log/traffic-collector /app

# Add Python packages to PATH
ENV PATH=/home/traffic-collector/.local/bin:$PATH
ENV PYTHONPATH=/home/traffic-collector/.local/lib/python3.9/site-packages:$PYTHONPATH

# ECS-specific environment variables
ENV AWS_DEFAULT_REGION=us-east-1
ENV ECS_ENABLE_CONTAINER_METADATA=true
ENV PYTHONUNBUFFERED=1

# Health check for ECS
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; import os; sys.exit(0 if os.path.exists('/tmp/collector-healthy') else 1)" || exit 1

# Switch to non-root user
USER traffic-collector

# Expose metrics port
EXPOSE 8080

# Use ECS-optimized entrypoint
ENTRYPOINT ["python", "ecs_traffic_collector.py"]
CMD ["start", "--foreground", "--config", "/etc/traffic-collector/config.yaml"]