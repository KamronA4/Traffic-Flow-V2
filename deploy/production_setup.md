# Production Deployment Guide
Complete guide for deploying Traffic Collector to production environments

## Prerequisites

### System Requirements
- Ubuntu 20.04+ or CentOS 8+ (or compatible Linux distribution)
- Minimum 2 CPU cores, 4GB RAM, 20GB storage
- Python 3.8+ and pip
- Root/sudo access for initial setup

### API Keys and Configuration
- TomTom API key with sufficient daily quota (50,000+ requests recommended)
- Secure API keys for authentication
- SSL certificates (for HTTPS deployment)

## Deployment Options

### Option 1: Native Linux Deployment (Recommended)

1. **Run the automated setup script:**
   ```bash
   sudo bash deploy/setup_vm.sh
   ```

2. **Configure your API keys:**
   ```bash
   sudo nano /etc/traffic-collector/environment
   ```
   Add:
   ```
   TOMTOM_API_KEY=your_tomtom_api_key_here
   TRAFFIC_API_KEY=your_secure_api_key_here
   ```

3. **Start services:**
   ```bash
   sudo systemctl restart traffic-collector.service
   sudo systemctl restart traffic-collector-api.service
   ```

4. **Verify deployment:**
   ```bash
   # Check service status
   sudo systemctl status traffic-collector.service
   
   # Check API health
   curl http://localhost:8080/health
   
   # View logs
   sudo journalctl -u traffic-collector.service -f
   ```

### Option 2: Docker Deployment

1. **Set up environment variables:**
   ```bash
   cp deploy/.env.example deploy/.env
   nano deploy/.env
   ```

2. **Deploy with Docker Compose:**
   ```bash
   cd deploy
   docker-compose up -d
   ```

3. **Monitor containers:**
   ```bash
   docker-compose ps
   docker-compose logs -f traffic-collector
   ```

### Option 3: Cloud Platform Deployment

#### AWS EC2
1. Launch Ubuntu 20.04 LTS instance (t3.medium or larger)
2. Configure security groups (ports 22, 80, 443, 8080)
3. Run native deployment script
4. Set up Elastic Load Balancer for high availability

#### Google Cloud Platform
1. Create Compute Engine instance (e2-medium or larger)
2. Configure firewall rules
3. Run native deployment script
4. Use Cloud Load Balancing for distribution

#### Microsoft Azure
1. Create Virtual Machine (Standard_B2s or larger)
2. Configure Network Security Groups
3. Run native deployment script
4. Use Azure Load Balancer

## Security Configuration

### Firewall Setup
```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp  # API port
sudo ufw enable

# iptables (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### SSL/TLS Setup
1. **Obtain SSL certificate:**
   ```bash
   # Using Let's Encrypt (free)
   sudo certbot --nginx -d your-domain.com
   
   # Or use your own certificates
   sudo cp your-cert.pem /etc/nginx/ssl/
   sudo cp your-key.pem /etc/nginx/ssl/
   ```

2. **Configure HTTPS in nginx:**
   ```bash
   sudo nano /etc/nginx/sites-available/traffic-collector
   ```

### API Security
- Change default API keys in production
- Use environment variables for sensitive data
- Enable request rate limiting
- Consider IP whitelisting for admin endpoints

## Monitoring and Maintenance

### Service Monitoring
```bash
# Check service health
curl http://localhost:8080/health

# View service status
sudo systemctl status traffic-collector.service

# Monitor resource usage
htop
df -h
```

### Log Management
```bash
# View real-time logs
sudo journalctl -u traffic-collector.service -f

# View API logs
sudo tail -f /var/log/nginx/access.log

# Check log rotation
sudo logrotate -d /etc/logrotate.d/traffic-collector
```

### Database Maintenance
```bash
# Manual database backup
sudo -u traffic-collector /opt/traffic-collector/scripts/backup_database.sh

# Check database size
sudo du -h /var/lib/traffic-collector/traffic_data.db

# Database vacuum (optimize)
sudo -u traffic-collector sqlite3 /var/lib/traffic-collector/traffic_data.db "VACUUM;"
```

### Health Checks
Automated health checks run every 5 minutes via cron. Manual checks:
```bash
# API health
curl -H "X-API-Key: your-api-key" http://localhost:8080/status

# Service status
python3 /opt/traffic-collector/traffic_collector_daemon.py status
```

## Performance Optimization

### System Tuning
```bash
# Increase file descriptor limits
echo "traffic-collector soft nofile 65536" >> /etc/security/limits.conf
echo "traffic-collector hard nofile 65536" >> /etc/security/limits.conf

# Optimize network settings
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
sysctl -p
```

### Database Optimization
- Regular VACUUM operations (automated)
- Proper indexing (automatically created)
- Data retention policies (90 days default)

### API Performance
- Connection pooling enabled
- Request caching (5-15 minutes TTL)
- Rate limiting configured
- Gzip compression enabled

## Scaling Considerations

### Horizontal Scaling
- Deploy multiple collector instances in different regions
- Use load balancer to distribute API requests
- Implement database replication for high availability

### Vertical Scaling
- Increase VM resources (CPU, RAM)
- Optimize collection intervals based on quota usage
- Implement adaptive scheduling for peak/off-peak times

### Data Archiving
- Set up automated data archiving to external storage
- Implement data compression for long-term retention
- Consider time-series database for large-scale deployments

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check configuration
sudo journalctl -u traffic-collector.service --no-pager

# Verify API key
sudo -u traffic-collector python3 -c "import os; print(os.getenv('TOMTOM_API_KEY'))"

# Check permissions
sudo ls -la /var/lib/traffic-collector/
```

**API quota exceeded:**
```bash
# Check today's usage
curl -H "X-API-Key: your-key" http://localhost:8080/status | jq .api_requests_today

# Adjust collection intervals in config
sudo nano /etc/traffic-collector/config.yaml
```

**Database errors:**
```bash
# Check database integrity
sudo -u traffic-collector sqlite3 /var/lib/traffic-collector/traffic_data.db "PRAGMA integrity_check;"

# Check disk space
df -h /var/lib/traffic-collector/
```

### Support Contacts
- Check logs: `/var/log/traffic-collector.log`
- Configuration: `/etc/traffic-collector/config.yaml`
- Service status: `systemctl status traffic-collector.service`

## Backup and Recovery

### Automated Backups
- Database backups: Every 6 hours
- Configuration backups: Daily
- Log rotation: 30 days retention

### Manual Backup
```bash
# Full system backup
sudo tar -czf traffic-collector-backup-$(date +%Y%m%d).tar.gz \
  /opt/traffic-collector \
  /etc/traffic-collector \
  /var/lib/traffic-collector \
  /etc/systemd/system/traffic-collector.service
```

### Recovery Procedures
1. Stop services
2. Restore database from backup
3. Verify configuration
4. Restart services
5. Validate data integrity

This completes the production deployment guide. Follow these procedures for a secure, scalable, and maintainable Traffic Collector deployment.