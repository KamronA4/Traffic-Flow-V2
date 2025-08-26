#!/bin/bash
#
# Traffic Collector VM Setup Script
# Automated deployment script for Ubuntu 20.04+ virtual machines
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_USER="traffic-collector"
SERVICE_GROUP="traffic-collector"
INSTALL_DIR="/opt/traffic-collector"
CONFIG_DIR="/etc/traffic-collector"
DATA_DIR="/var/lib/traffic-collector"
LOG_DIR="/var/log"
BACKUP_DIR="/var/backups/traffic-collector"

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check Ubuntu version
check_ubuntu_version() {
    if ! lsb_release -d | grep -q "Ubuntu"; then
        error "This script is designed for Ubuntu. Detected: $(lsb_release -d | cut -f2)"
        exit 1
    fi
    
    VERSION=$(lsb_release -r | cut -f2)
    if [[ $(echo "$VERSION >= 20.04" | bc -l) -eq 0 ]]; then
        error "Ubuntu 20.04 or newer is required. Detected: $VERSION"
        exit 1
    fi
    
    log "Ubuntu $VERSION detected - compatible"
}

# Update system packages
update_system() {
    log "Updating system packages..."
    apt update && apt upgrade -y
    apt install -y software-properties-common curl wget git
}

# Install Python and dependencies
install_python() {
    log "Installing Python 3.8+ and pip..."
    apt install -y python3 python3-pip python3-venv python3-dev
    
    # Verify Python version
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log "Python $PYTHON_VERSION installed"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    apt install -y \
        sqlite3 \
        logrotate \
        cron \
        bc \
        jq \
        htop \
        curl \
        wget \
        unzip \
        supervisor \
        nginx \
        certbot \
        python3-certbot-nginx
}

# Create service user and directories
create_user_and_directories() {
    log "Creating service user and directories..."
    
    # Create user and group
    if ! getent group $SERVICE_GROUP > /dev/null 2>&1; then
        groupadd --system $SERVICE_GROUP
        log "Created group: $SERVICE_GROUP"
    fi
    
    if ! getent passwd $SERVICE_USER > /dev/null 2>&1; then
        useradd --system --gid $SERVICE_GROUP --shell /bin/false \
                --home-dir $DATA_DIR --create-home $SERVICE_USER
        log "Created user: $SERVICE_USER"
    fi
    
    # Create directories
    mkdir -p $INSTALL_DIR $CONFIG_DIR $DATA_DIR $BACKUP_DIR
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR $DATA_DIR $BACKUP_DIR
    chown -R root:$SERVICE_GROUP $CONFIG_DIR
    chmod 755 $INSTALL_DIR $CONFIG_DIR $DATA_DIR
    chmod 750 $BACKUP_DIR
    
    log "Directories created and permissions set"
}

# Setup Python virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    cd $INSTALL_DIR
    sudo -u $SERVICE_USER python3 -m venv venv
    
    # Activate venv and install packages
    source venv/bin/activate
    pip install --upgrade pip
    pip install \
        requests \
        pyyaml \
        schedule \
        sqlite3 \
        pandas \
        numpy \
        python-daemon \
        psutil \
        flask \
        gunicorn
    
    log "Python environment setup complete"
}

# Copy application files
copy_application_files() {
    log "Copying application files..."
    
    # Copy main daemon script
    if [[ -f "traffic_collector_daemon.py" ]]; then
        cp traffic_collector_daemon.py $INSTALL_DIR/
        chmod 755 $INSTALL_DIR/traffic_collector_daemon.py
        chown $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/traffic_collector_daemon.py
    else
        error "traffic_collector_daemon.py not found in current directory"
        exit 1
    fi
    
    # Copy configuration
    if [[ -f "config/collector_config.yaml" ]]; then
        cp config/collector_config.yaml $CONFIG_DIR/config.yaml
        chmod 640 $CONFIG_DIR/config.yaml
        chown root:$SERVICE_GROUP $CONFIG_DIR/config.yaml
    else
        warning "Config file not found, creating default"
        create_default_config
    fi
    
    log "Application files copied"
}

# Create default configuration
create_default_config() {
    cat > $CONFIG_DIR/config.yaml << 'EOF'
tomtom_api_key: "${TOMTOM_API_KEY}"
database_path: "/var/lib/traffic-collector/traffic_data.db"
daily_quota: 50000
rate_limit_delay: 0.1
log_level: "INFO"

collection_zones:
  - name: "I-95_Providence_Corridor"
    bbox: [41.7, -71.6, 41.9, -71.3]
    priority: 1
    interval_minutes: 5
    data_types: ["flow", "incidents"]

api_endpoints:
  incidents: "https://api.tomtom.com/traffic/services/5/incidentDetails"
  flow: "https://api.tomtom.com/traffic/services/4/flowSegmentData"
EOF
    
    chmod 640 $CONFIG_DIR/config.yaml
    chown root:$SERVICE_GROUP $CONFIG_DIR/config.yaml
}

# Install systemd service
install_systemd_service() {
    log "Installing systemd service..."
    
    if [[ -f "deploy/traffic-collector.service" ]]; then
        cp deploy/traffic-collector.service /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable traffic-collector.service
        log "Systemd service installed and enabled"
    else
        error "Service file not found at deploy/traffic-collector.service"
        exit 1
    fi
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/traffic-collector << 'EOF'
/var/log/traffic-collector.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 traffic-collector traffic-collector
    postrotate
        systemctl reload traffic-collector.service > /dev/null 2>&1 || true
    endscript
}
EOF
    
    log "Log rotation configured"
}

# Setup database backup
setup_database_backup() {
    log "Setting up database backup..."
    
    cat > /etc/cron.d/traffic-collector-backup << 'EOF'
# Traffic Collector Database Backup
0 2 * * * traffic-collector /opt/traffic-collector/scripts/backup_database.sh >> /var/log/traffic-collector-backup.log 2>&1
0 3 * * 0 traffic-collector /opt/traffic-collector/scripts/cleanup_old_backups.sh >> /var/log/traffic-collector-backup.log 2>&1
EOF
    
    # Create backup scripts directory
    mkdir -p $INSTALL_DIR/scripts
    
    # Database backup script
    cat > $INSTALL_DIR/scripts/backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/traffic-collector"
DB_PATH="/var/lib/traffic-collector/traffic_data.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/traffic_data_$DATE.db"

if [[ -f "$DB_PATH" ]]; then
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
    gzip "$BACKUP_FILE"
    echo "Database backup created: $BACKUP_FILE.gz"
else
    echo "Database file not found: $DB_PATH"
    exit 1
fi
EOF
    
    # Cleanup old backups script
    cat > $INSTALL_DIR/scripts/cleanup_old_backups.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/traffic-collector"
find "$BACKUP_DIR" -name "traffic_data_*.db.gz" -mtime +30 -delete
echo "Old backups cleaned up"
EOF
    
    chmod 755 $INSTALL_DIR/scripts/*.sh
    chown $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/scripts/*.sh
    
    log "Database backup configured"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up basic monitoring..."
    
    # Create health check script
    cat > $INSTALL_DIR/scripts/health_check.sh << 'EOF'
#!/bin/bash
# Basic health check for traffic collector service

SERVICE_NAME="traffic-collector"
LOG_FILE="/var/log/traffic-collector-health.log"

# Check if service is running
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "$(date): Service is running" >> $LOG_FILE
else
    echo "$(date): Service is NOT running - attempting restart" >> $LOG_FILE
    systemctl restart $SERVICE_NAME
fi

# Check database size and log if growing too large (>1GB)
DB_SIZE=$(du -m /var/lib/traffic-collector/traffic_data.db 2>/dev/null | cut -f1)
if [[ $DB_SIZE -gt 1024 ]]; then
    echo "$(date): Database size is large: ${DB_SIZE}MB" >> $LOG_FILE
fi

# Check API quota usage (if available)
if [[ -f /var/lib/traffic-collector/traffic_data.db ]]; then
    USAGE=$(sqlite3 /var/lib/traffic-collector/traffic_data.db "SELECT SUM(requests_count) FROM api_usage WHERE DATE(timestamp) = DATE('now')" 2>/dev/null || echo "0")
    echo "$(date): API requests today: $USAGE" >> $LOG_FILE
fi
EOF
    
    chmod 755 $INSTALL_DIR/scripts/health_check.sh
    chown $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/scripts/health_check.sh
    
    # Add to crontab for regular health checks
    cat > /etc/cron.d/traffic-collector-health << 'EOF'
# Traffic Collector Health Check
*/5 * * * * traffic-collector /opt/traffic-collector/scripts/health_check.sh
EOF
    
    log "Monitoring setup complete"
}

# Create API endpoint for Streamlit integration
setup_api_endpoint() {
    log "Setting up API endpoint for Streamlit integration..."
    
    # Create simple Flask API
    cat > $INSTALL_DIR/api_server.py << 'EOF'
#!/usr/bin/env python3
"""
Simple API server for Traffic Collector data access
Provides REST endpoints for Streamlit application
"""

import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
import os

app = Flask(__name__)
DB_PATH = "/var/lib/traffic-collector/traffic_data.db"

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/status')
def status():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Get record counts
            cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
            incidents_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM traffic_flow")
            flow_count = cursor.fetchone()[0]
            
            # Get API usage today
            today = datetime.now().date()
            cursor.execute("SELECT SUM(requests_count) FROM api_usage WHERE DATE(timestamp) = ?", (today,))
            api_usage = cursor.fetchone()[0] or 0
            
            return jsonify({
                'incidents_total': incidents_count,
                'flow_records_total': flow_count,
                'api_requests_today': api_usage,
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/incidents')
def get_incidents():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM traffic_incidents WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND DATE(timestamp) >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND DATE(timestamp) <= ?"
                params.append(end_date)
                
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            incidents = [dict(row) for row in rows]
            return jsonify(incidents)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF
    
    chmod 755 $INSTALL_DIR/api_server.py
    chown $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/api_server.py
    
    # Create systemd service for API
    cat > /etc/systemd/system/traffic-collector-api.service << 'EOF'
[Unit]
Description=Traffic Collector API Server
After=network.target traffic-collector.service

[Service]
Type=simple
User=traffic-collector
Group=traffic-collector
WorkingDirectory=/opt/traffic-collector
ExecStart=/opt/traffic-collector/venv/bin/python /opt/traffic-collector/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable traffic-collector-api.service
    
    log "API endpoint setup complete"
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Install ufw if not present
    apt install -y ufw
    
    # Reset to defaults
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow API endpoint
    ufw allow 8080/tcp
    
    # Allow HTTP/HTTPS for potential web interface
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable firewall
    ufw --force enable
    
    log "Firewall configured"
}

# Final setup and start services
finalize_setup() {
    log "Finalizing setup and starting services..."
    
    # Set final permissions
    chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR $DATA_DIR $BACKUP_DIR
    
    # Start and enable services
    systemctl start traffic-collector.service
    systemctl start traffic-collector-api.service
    
    # Check service status
    if systemctl is-active --quiet traffic-collector.service; then
        log "Traffic Collector service is running"
    else
        error "Traffic Collector service failed to start"
        systemctl status traffic-collector.service
    fi
    
    if systemctl is-active --quiet traffic-collector-api.service; then
        log "Traffic Collector API service is running"
    else
        warning "Traffic Collector API service failed to start"
        systemctl status traffic-collector-api.service
    fi
}

# Print completion message
print_completion_message() {
    log "Traffic Collector VM setup completed successfully!"
    echo
    info "Next steps:"
    echo "1. Set your TomTom API key:"
    echo "   sudo nano /etc/traffic-collector/environment"
    echo "   Add: TOMTOM_API_KEY=your_api_key_here"
    echo
    echo "2. Restart the service:"
    echo "   sudo systemctl restart traffic-collector.service"
    echo
    echo "3. Check service status:"
    echo "   sudo systemctl status traffic-collector.service"
    echo
    echo "4. View logs:"
    echo "   sudo journalctl -u traffic-collector.service -f"
    echo
    echo "5. API endpoint is available at:"
    echo "   http://$(hostname -I | awk '{print $1}'):8080/status"
    echo
    info "Configuration files:"
    echo "- Service config: $CONFIG_DIR/config.yaml"
    echo "- Systemd service: /etc/systemd/system/traffic-collector.service"
    echo "- Database: $DATA_DIR/traffic_data.db"
    echo "- Logs: /var/log/traffic-collector.log"
}

# Main execution
main() {
    log "Starting Traffic Collector VM setup..."
    
    check_root
    check_ubuntu_version
    update_system
    install_python
    install_dependencies
    create_user_and_directories
    setup_python_env
    copy_application_files
    install_systemd_service
    setup_log_rotation
    setup_database_backup
    setup_monitoring
    setup_api_endpoint
    configure_firewall
    finalize_setup
    print_completion_message
    
    log "Setup complete! The Traffic Collector is now running as a service."
}

# Run main function
main "$@"