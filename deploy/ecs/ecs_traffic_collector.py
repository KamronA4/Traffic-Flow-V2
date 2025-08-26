#!/usr/bin/env python3
"""
ECS-Optimized Traffic Collector Daemon
AWS ECS/Fargate compatible version with CloudWatch integration
"""

import os
import sys
import json
import boto3
import signal
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import watchtower
from botocore.exceptions import ClientError, NoCredentialsError

# Import the original collector
sys.path.append('/app')
from traffic_collector_daemon import CollectorDaemon as OriginalCollectorDaemon

class ECSTrafficCollectorDaemon(OriginalCollectorDaemon):
    """ECS-optimized traffic collector daemon with AWS integration"""
    
    def __init__(self, config_path: str = "/etc/traffic-collector/config.yaml"):
        # AWS configuration
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.cluster_name = os.getenv('ECS_CLUSTER', 'village-cluster')
        self.service_name = os.getenv('ECS_SERVICE', 'village-traffic-collector')
        
        # ECS metadata
        self.task_arn = self._get_task_arn()
        self.task_definition_family = self._get_task_definition_family()
        
        # Initialize AWS clients
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name=self.aws_region)
            self.secrets_manager = boto3.client('secretsmanager', region_name=self.aws_region)
            self.ecs_client = boto3.client('ecs', region_name=self.aws_region)
            self.aws_available = True
        except (ClientError, NoCredentialsError) as e:
            logging.warning(f"AWS services not available: {e}")
            self.aws_available = False
        
        # Set up CloudWatch logging before parent initialization
        self._setup_cloudwatch_logging()
        
        # Database configuration for ECS
        self.db_type = os.getenv('DB_TYPE', 'sqlite')
        if self.db_type == 'postgres':
            self.database_url = self._get_secret('village/database-url')
        
        # Initialize parent class
        super().__init__(config_path)
        
        # ECS-specific health check
        self.health_check_file = '/tmp/collector-healthy'
        self._create_health_check_file()
        
        # Start metrics reporting
        if self.aws_available:
            self._start_metrics_reporter()
    
    def _setup_cloudwatch_logging(self):
        """Setup CloudWatch logging for ECS"""
        if not self.aws_available:
            return
            
        try:
            # Create CloudWatch log group if it doesn't exist
            log_group = f'/ecs/village-traffic-collector'
            
            try:
                self.cloudwatch.describe_log_groups(logGroupNamePrefix=log_group)
            except ClientError:
                self.cloudwatch.create_log_group(logGroupName=log_group)
                
            # Add CloudWatch handler
            cloudwatch_handler = watchtower.CloudWatchLogsHandler(
                boto3_client=self.cloudwatch,
                log_group=log_group,
                stream_name=f'traffic-collector-{self.task_arn.split("/")[-1][-8:]}'
            )
            cloudwatch_handler.setLevel(logging.INFO)
            
            # Update root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(cloudwatch_handler)
            
            logging.info("CloudWatch logging configured successfully")
            
        except Exception as e:
            logging.warning(f"Failed to setup CloudWatch logging: {e}")
    
    def _get_task_arn(self) -> str:
        """Get ECS task ARN from metadata endpoint"""
        try:
            metadata_uri_v4 = os.environ.get('ECS_CONTAINER_METADATA_URI_V4')
            if metadata_uri_v4:
                response = requests.get(f"{metadata_uri_v4}/task")
                task_metadata = response.json()
                return task_metadata.get('TaskARN', 'unknown')
        except Exception:
            pass
        return 'unknown'
    
    def _get_task_definition_family(self) -> str:
        """Get task definition family from task ARN"""
        if self.task_arn != 'unknown':
            return self.task_arn.split(':')[-1].split('/')[1]
        return 'village-traffic-collector'
    
    def _get_secret(self, secret_id: str) -> str:
        """Get secret from AWS Secrets Manager"""
        if not self.aws_available:
            return os.getenv(secret_id.replace('village/', '').replace('-', '_').upper(), '')
            
        try:
            response = self.secrets_manager.get_secret_value(SecretId=secret_id)
            return response['SecretString']
        except ClientError as e:
            logging.error(f"Failed to get secret {secret_id}: {e}")
            # Fallback to environment variable
            env_var = secret_id.replace('village/', '').replace('-', '_').upper()
            return os.getenv(env_var, '')
    
    def _create_health_check_file(self):
        """Create health check file for ECS health checks"""
        try:
            with open(self.health_check_file, 'w') as f:
                f.write(f"healthy-{datetime.now().isoformat()}")
            logging.info("Health check file created")
        except Exception as e:
            logging.error(f"Failed to create health check file: {e}")
    
    def _update_health_check(self):
        """Update health check file with current timestamp"""
        try:
            with open(self.health_check_file, 'w') as f:
                f.write(f"healthy-{datetime.now().isoformat()}")
        except Exception as e:
            logging.error(f"Failed to update health check file: {e}")
    
    def _start_metrics_reporter(self):
        """Start background thread for CloudWatch metrics reporting"""
        if not self.aws_available:
            return
            
        def metrics_loop():
            while self.running:
                try:
                    self._send_custom_metrics()
                    time.sleep(300)  # Send metrics every 5 minutes
                except Exception as e:
                    logging.error(f"Error sending metrics: {e}")
                    time.sleep(60)
        
        metrics_thread = threading.Thread(target=metrics_loop, daemon=True)
        metrics_thread.start()
        logging.info("CloudWatch metrics reporter started")
    
    def _send_custom_metrics(self):
        """Send custom metrics to CloudWatch"""
        if not self.aws_available:
            return
            
        try:
            # Get current stats
            status = self.status()
            
            # Prepare metrics
            metrics = [
                {
                    'MetricName': 'APIRequestsToday',
                    'Value': status['api_requests_today'],
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': self.service_name},
                        {'Name': 'Cluster', 'Value': self.cluster_name}
                    ]
                },
                {
                    'MetricName': 'QuotaRemaining',
                    'Value': status['quota_remaining'],
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': self.service_name},
                        {'Name': 'Cluster', 'Value': self.cluster_name}
                    ]
                },
                {
                    'MetricName': 'IncidentsTotal',
                    'Value': status['incidents_total'],
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': self.service_name},
                        {'Name': 'Cluster', 'Value': self.cluster_name}
                    ]
                },
                {
                    'MetricName': 'FlowRecordsTotal',
                    'Value': status['flow_records_total'],
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': self.service_name},
                        {'Name': 'Cluster', 'Value': self.cluster_name}
                    ]
                }
            ]
            
            # Send metrics in batches
            for i in range(0, len(metrics), 20):
                batch = metrics[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace='Village/TrafficCollector',
                    MetricData=batch
                )
                
            logging.debug("Custom metrics sent to CloudWatch")
            
        except Exception as e:
            logging.error(f"Failed to send custom metrics: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Override config loading to support AWS Secrets Manager"""
        config = super()._load_config()
        
        # Override API key with secret if available
        if self.aws_available:
            tomtom_key = self._get_secret('village/tomtom-api-key')
            if tomtom_key:
                config['tomtom_api_key'] = tomtom_key
        
        # ECS-specific configuration overrides
        config.update({
            'daily_quota': int(os.getenv('DAILY_QUOTA', '50000')),
            'rate_limit_delay': float(os.getenv('RATE_LIMIT_DELAY', '0.1')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        })
        
        return config
    
    def collection_cycle(self):
        """Override collection cycle with ECS health checks and metrics"""
        try:
            # Run original collection cycle
            super().collection_cycle()
            
            # Update health check
            self._update_health_check()
            
        except Exception as e:
            logging.error(f"Collection cycle error: {e}")
            # Remove health check file on error
            try:
                os.remove(self.health_check_file)
            except FileNotFoundError:
                pass
            raise
    
    def _signal_handler(self, signum, frame):
        """Enhanced signal handler for ECS graceful shutdown"""
        logging.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        # Remove health check file
        try:
            os.remove(self.health_check_file)
        except FileNotFoundError:
            pass
        
        # Send final metrics
        if self.aws_available:
            try:
                self._send_custom_metrics()
            except Exception:
                pass
        
        # Call parent shutdown
        super()._signal_handler(signum, frame)
    
    def status(self) -> Dict[str, Any]:
        """Enhanced status with ECS metadata"""
        base_status = super().status()
        
        # Add ECS-specific information
        base_status.update({
            'ecs_task_arn': self.task_arn,
            'ecs_cluster': self.cluster_name,
            'ecs_service': self.service_name,
            'aws_region': self.aws_region,
            'db_type': self.db_type,
            'aws_available': self.aws_available,
            'health_check_file_exists': os.path.exists(self.health_check_file)
        })
        
        return base_status

def main():
    """Main entry point for ECS daemon"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ECS Traffic Collector Daemon')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'restart'], 
                       help='Action to perform')
    parser.add_argument('--config', default='/etc/traffic-collector/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--foreground', action='store_true',
                       help='Run in foreground (for ECS)')
    
    args = parser.parse_args()
    
    daemon = ECSTrafficCollectorDaemon(args.config)
    
    if args.action == 'start':
        daemon.start()
        if args.foreground:
            try:
                logging.info("Traffic Collector Daemon running in foreground mode")
                while daemon.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Received keyboard interrupt")
                daemon.stop()
        else:
            logging.info("Daemon started in background")
    
    elif args.action == 'stop':
        daemon.stop()
    
    elif args.action == 'status':
        status = daemon.status()
        print(json.dumps(status, indent=2))
    
    elif args.action == 'restart':
        daemon.stop()
        time.sleep(2)
        daemon.start()

if __name__ == "__main__":
    main()