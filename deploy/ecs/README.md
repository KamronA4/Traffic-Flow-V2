# ECS Deployment Guide for Village Traffic Collector

This guide explains how to deploy the Village Traffic Collector daemon to Amazon ECS, enabling 24/7 traffic data collection without requiring your local computer to be always on.

## Overview

The ECS deployment provides:
- **24/7 Operation**: Continuous data collection using AWS Fargate
- **Auto-scaling**: Automatic resource adjustment based on demand
- **High Availability**: Multi-AZ deployment with automatic failover
- **Cost Optimization**: Pay-per-use pricing with Fargate Spot options
- **Monitoring**: CloudWatch logs and metrics integration
- **Security**: AWS Secrets Manager for API keys and credentials

## Prerequisites

1. **AWS CLI** installed and configured with appropriate permissions
2. **Docker** installed for building images
3. **Git** for version control
4. **jq** for JSON processing
5. **TomTom API Key** (sign up at developer.tomtom.com for 50k free requests/day)

### Required AWS Permissions

Your AWS user/role needs the following permissions:
- ECS full access
- ECR full access
- IAM role creation and management
- Secrets Manager access
- CloudWatch logs and metrics
- VPC and networking access

## Quick Start

### 1. Set up AWS Infrastructure

```bash
# Navigate to the ECS deployment directory
cd deploy/ecs

# Set up all required AWS resources
./aws-setup.sh setup
```

This script will:
- Create IAM roles for ECS tasks
- Set up AWS Secrets Manager secrets
- Create CloudWatch log groups
- Configure networking (VPC, subnets, security groups)
- Set up EFS for persistent storage
- Generate configuration files

### 2. Deploy to ECS

```bash
# Deploy the traffic collector daemon
./deploy.sh deploy
```

This will:
- Build and push the Docker image to ECR
- Create ECS cluster and service
- Deploy with the specified configuration
- Set up CloudWatch monitoring
- Wait for service stability

### 3. Monitor the Deployment

- **ECS Console**: Check service status and task health
- **CloudWatch Logs**: View application logs in real-time
- **CloudWatch Dashboard**: Monitor API usage and performance metrics

## Manual Deployment Steps

If you prefer to deploy manually or customize the process:

### 1. Build and Push Docker Image

```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
AWS_REGION=us-east-1
ECR_REPOSITORY=village-traffic-collector

# Create ECR repository
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

# Build and tag image
docker build -t $ECR_REPOSITORY -f Dockerfile ../../
docker tag $ECR_REPOSITORY:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

# Login and push to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
```

### 2. Register Task Definition

```bash
# Update task definition with your values
sed -i "s/\${AWS_ACCOUNT_ID}/$AWS_ACCOUNT_ID/g" task-definition.json
sed -i "s/\${AWS_REGION}/$AWS_REGION/g" task-definition.json

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION
```

### 3. Create ECS Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name village-cluster --region $AWS_REGION

# Create service
aws ecs create-service \
    --cluster village-cluster \
    --service-name village-traffic-collector \
    --task-definition village-traffic-collector:1 \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration file://network-config.json \
    --region $AWS_REGION
```

## Configuration Options

### Environment Variables

The following environment variables can be configured in the task definition:

| Variable | Default | Description |
|----------|---------|-------------|
| `DAILY_QUOTA` | 50000 | TomTom API daily request limit |
| `RATE_LIMIT_DELAY` | 0.1 | Seconds between API requests |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `DB_TYPE` | sqlite | Database type (sqlite/postgres) |
| `AWS_REGION` | us-east-1 | AWS region for services |

### Secrets Configuration

Secrets are stored in AWS Secrets Manager:

- `village/tomtom-api-key`: Your TomTom API key
- `village/database-url`: Database connection string
- `village/api-secret-key`: API authentication secret

### Resource Configuration

Default resource allocation:
- **CPU**: 0.5 vCPU (512 units)
- **Memory**: 1 GB (1024 MB)
- **Storage**: 20 GB EFS volume

You can adjust these in the task definition based on your needs.

## Monitoring and Alerting

### CloudWatch Metrics

The daemon publishes custom metrics:
- `Village/TrafficCollector/APIRequestsToday`: Daily API usage
- `Village/TrafficCollector/QuotaRemaining`: Remaining API quota
- `Village/TrafficCollector/IncidentsTotal`: Total incidents collected
- `Village/TrafficCollector/FlowRecordsTotal`: Total flow records

### CloudWatch Alarms

Set up alarms for:
- API quota exhaustion (≥90% of daily limit)
- Task health failures
- High memory/CPU utilization

### Dashboard

Access the pre-configured dashboard:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=VillageTrafficCollector
```

## Troubleshooting

### Common Issues

1. **Task keeps restarting**
   - Check CloudWatch logs for errors
   - Verify TomTom API key is valid
   - Ensure network connectivity

2. **No data being collected**
   - Verify API key has remaining quota
   - Check collection zones configuration
   - Review application logs

3. **High costs**
   - Use Fargate Spot for 70% cost savings
   - Reduce collection frequency during off-peak hours
   - Optimize resource allocation

### Debugging Commands

```bash
# View service status
aws ecs describe-services --cluster village-cluster --services village-traffic-collector

# Check task health
aws ecs describe-tasks --cluster village-cluster --tasks $(aws ecs list-tasks --cluster village-cluster --service village-traffic-collector --query 'taskArns[0]' --output text)

# View logs
aws logs get-log-events --log-group-name /ecs/village-traffic-collector --log-stream-name traffic-collector-XXXXXXXXX

# Check metrics
aws cloudwatch get-metric-statistics --namespace Village/TrafficCollector --metric-name APIRequestsToday --start-time 2023-01-01T00:00:00Z --end-time 2023-01-02T00:00:00Z --period 3600 --statistics Sum
```

## Cost Optimization

### Fargate Spot

Save up to 70% by using Fargate Spot:

```json
{
  "capacityProviders": ["FARGATE_SPOT", "FARGATE"],
  "defaultCapacityProviderStrategy": [
    {
      "capacityProvider": "FARGATE_SPOT",
      "weight": 4
    },
    {
      "capacityProvider": "FARGATE",
      "weight": 1
    }
  ]
}
```

### Scheduled Scaling

Reduce costs during off-peak hours:

```bash
# Scale down at night
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/village-cluster/village-traffic-collector \
    --min-capacity 0 \
    --max-capacity 1
```

### Right-sizing Resources

Monitor utilization and adjust:
- Start with 0.25 vCPU / 512 MB for light workloads
- Scale up based on actual usage patterns

## Security Best Practices

1. **Use least-privilege IAM roles**
2. **Store secrets in AWS Secrets Manager**
3. **Enable VPC flow logs**
4. **Use private subnets with NAT gateway**
5. **Enable ECS Exec only when needed**
6. **Regularly rotate API keys**

## Updates and Maintenance

### Updating the Application

1. **Via GitHub Actions** (recommended):
   - Push changes to main branch
   - Workflow automatically builds and deploys

2. **Manual update**:
   ```bash
   ./deploy.sh deploy
   ```

### Database Maintenance

- **Backup**: EFS provides automatic backups
- **Cleanup**: Old data is automatically purged based on retention settings
- **Migration**: Use EFS for seamless database migration

## Support and Troubleshooting

For issues:
1. Check CloudWatch logs first
2. Review ECS service events
3. Verify AWS permissions
4. Test TomTom API connectivity

## Cleanup

To remove all AWS resources:

```bash
# Stop and delete the service
./deploy.sh cleanup

# Remove AWS infrastructure
./aws-setup.sh cleanup
```

**Warning**: This will permanently delete all collected data and AWS resources.

## Next Steps

After successful deployment:
1. Monitor API usage and costs
2. Set up additional CloudWatch alarms
3. Configure automated backups
4. Consider multi-region deployment for high availability
5. Set up integration with your existing monitoring systems

## File Structure

```
deploy/ecs/
├── README.md                    # This documentation
├── Dockerfile                   # ECS-optimized container image
├── ecs_traffic_collector.py     # ECS-enhanced daemon with CloudWatch integration
├── task-definition.json         # ECS task definition
├── service-template.json        # ECS service configuration template
├── ecs-params.yml              # ECS parameters configuration
├── buildspec.yml               # AWS CodeBuild specification
├── cloudwatch-dashboard.json   # CloudWatch dashboard configuration
├── deploy.sh                   # Main deployment script
├── aws-setup.sh               # AWS infrastructure setup
├── .env.template              # Environment configuration template
└── network-config.json        # Network configuration for ECS service
```

This deployment setup provides a production-ready, scalable solution for continuous traffic data collection using your existing TomTom API integration while maintaining all the dynamic request management and quota controls you've already implemented.