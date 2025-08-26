#!/bin/bash

# AWS Infrastructure Setup Script for Village Traffic Collector
# This script sets up the required AWS infrastructure for ECS deployment

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="village-traffic-collector"

# Print functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create IAM roles
create_iam_roles() {
    print_info "Creating IAM roles..."
    
    # ECS Task Execution Role
    if ! aws iam get-role --role-name ecsTaskExecutionRole &> /dev/null; then
        print_info "Creating ecsTaskExecutionRole..."
        
        cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
        
        aws iam create-role \
            --role-name ecsTaskExecutionRole \
            --assume-role-policy-document file://trust-policy.json
        
        aws iam attach-role-policy \
            --role-name ecsTaskExecutionRole \
            --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
            
        aws iam attach-role-policy \
            --role-name ecsTaskExecutionRole \
            --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
        
        rm trust-policy.json
        print_success "ecsTaskExecutionRole created"
    fi
    
    # Village Traffic Collector Task Role
    if ! aws iam get-role --role-name villageTrafficCollectorTaskRole &> /dev/null; then
        print_info "Creating villageTrafficCollectorTaskRole..."
        
        cat > task-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
        
        cat > task-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:${AWS_REGION}:*:secret:village/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:${AWS_REGION}:*:log-group:/ecs/village-traffic-collector:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeTasks",
        "ecs:DescribeServices",
        "ecs:DescribeClusters"
      ],
      "Resource": "*"
    }
  ]
}
EOF
        
        aws iam create-role \
            --role-name villageTrafficCollectorTaskRole \
            --assume-role-policy-document file://task-trust-policy.json
        
        aws iam put-role-policy \
            --role-name villageTrafficCollectorTaskRole \
            --policy-name VillageTrafficCollectorPolicy \
            --policy-document file://task-policy.json
        
        rm task-trust-policy.json task-policy.json
        print_success "villageTrafficCollectorTaskRole created"
    fi
}

# Create secrets in AWS Secrets Manager
create_secrets() {
    print_info "Creating secrets in AWS Secrets Manager..."
    
    # Prompt for TomTom API key
    if ! aws secretsmanager describe-secret --secret-id village/tomtom-api-key &> /dev/null; then
        print_info "Enter your TomTom API key:"
        read -s TOMTOM_API_KEY
        
        aws secretsmanager create-secret \
            --name village/tomtom-api-key \
            --description "TomTom API key for traffic data collection" \
            --secret-string "$TOMTOM_API_KEY"
        
        print_success "TomTom API key secret created"
    fi
    
    # Create database URL secret (for future PostgreSQL use)
    if ! aws secretsmanager describe-secret --secret-id village/database-url &> /dev/null; then
        DATABASE_URL="sqlite:///var/lib/traffic-collector/traffic_data.db"
        
        aws secretsmanager create-secret \
            --name village/database-url \
            --description "Database connection URL" \
            --secret-string "$DATABASE_URL"
        
        print_success "Database URL secret created"
    fi
    
    # Create API secret key
    if ! aws secretsmanager describe-secret --secret-id village/api-secret-key &> /dev/null; then
        API_SECRET_KEY=$(openssl rand -base64 32)
        
        aws secretsmanager create-secret \
            --name village/api-secret-key \
            --description "API secret key for authentication" \
            --secret-string "$API_SECRET_KEY"
        
        print_success "API secret key created"
    fi
}

# Create CloudWatch log group
create_log_group() {
    print_info "Creating CloudWatch log group..."
    
    if ! aws logs describe-log-groups --log-group-name-prefix "/ecs/village-traffic-collector" --query 'logGroups[0].logGroupName' --output text | grep -q "/ecs/village-traffic-collector"; then
        aws logs create-log-group \
            --log-group-name "/ecs/village-traffic-collector" \
            --retention-in-days 14
        
        print_success "CloudWatch log group created"
    else
        print_info "CloudWatch log group already exists"
    fi
}

# Create VPC and networking (if needed)
create_networking() {
    print_info "Setting up networking..."
    
    # Get default VPC
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region "$AWS_REGION")
    
    if [[ "$VPC_ID" == "None" ]]; then
        print_error "No default VPC found. Please create a VPC first."
        exit 1
    fi
    
    print_info "Using VPC: $VPC_ID"
    
    # Get default security group
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
        --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" \
        --query 'SecurityGroups[0].GroupId' --output text --region "$AWS_REGION")
    
    # Add HTTP inbound rule to security group if not exists
    if ! aws ec2 describe-security-groups \
        --group-ids "$SECURITY_GROUP_ID" \
        --query 'SecurityGroups[0].IpPermissions[?FromPort==`8080`]' \
        --output text | grep -q "8080"; then
        
        print_info "Adding HTTP inbound rule to security group..."
        aws ec2 authorize-security-group-ingress \
            --group-id "$SECURITY_GROUP_ID" \
            --protocol tcp \
            --port 8080 \
            --cidr 0.0.0.0/0
    fi
    
    # Get subnets
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --query 'Subnets[*].SubnetId' --output text --region "$AWS_REGION")
    
    print_success "Networking configured"
    echo "VPC ID: $VPC_ID"
    echo "Security Group: $SECURITY_GROUP_ID"
    echo "Subnets: $SUBNET_IDS"
}

# Create EFS file system (for persistent storage)
create_efs() {
    print_info "Creating EFS file system for persistent storage..."
    
    # Check if EFS already exists
    EFS_ID=$(aws efs describe-file-systems \
        --query 'FileSystems[?CreationToken==`village-traffic-collector-storage`].FileSystemId' \
        --output text --region "$AWS_REGION")
    
    if [[ -z "$EFS_ID" || "$EFS_ID" == "None" ]]; then
        print_info "Creating new EFS file system..."
        
        EFS_RESPONSE=$(aws efs create-file-system \
            --creation-token village-traffic-collector-storage \
            --throughput-mode provisioned \
            --provisioned-throughput-in-mibps 1 \
            --performance-mode generalPurpose \
            --tags Key=Name,Value=village-traffic-collector-storage \
            --region "$AWS_REGION")
        
        EFS_ID=$(echo "$EFS_RESPONSE" | jq -r '.FileSystemId')
        
        # Wait for EFS to be available
        print_info "Waiting for EFS to become available..."
        aws efs wait file-system-available --file-system-id "$EFS_ID" --region "$AWS_REGION"
        
        print_success "EFS file system created: $EFS_ID"
    else
        print_info "EFS file system already exists: $EFS_ID"
    fi
    
    # Create access point
    ACCESS_POINT_ID=$(aws efs describe-access-points \
        --file-system-id "$EFS_ID" \
        --query 'AccessPoints[?Tags[?Key==`Name` && Value==`village-traffic-collector`]].AccessPointId' \
        --output text --region "$AWS_REGION")
    
    if [[ -z "$ACCESS_POINT_ID" || "$ACCESS_POINT_ID" == "None" ]]; then
        print_info "Creating EFS access point..."
        
        ACCESS_POINT_RESPONSE=$(aws efs create-access-point \
            --file-system-id "$EFS_ID" \
            --posix-user Uid=1000,Gid=1000 \
            --root-directory Path=/var/lib/traffic-collector,CreationInfo='{OwnerUid=1000,OwnerGid=1000,Permissions=755}' \
            --tags Key=Name,Value=village-traffic-collector \
            --region "$AWS_REGION")
        
        ACCESS_POINT_ID=$(echo "$ACCESS_POINT_RESPONSE" | jq -r '.AccessPointId')
        print_success "EFS access point created: $ACCESS_POINT_ID"
    else
        print_info "EFS access point already exists: $ACCESS_POINT_ID"
    fi
    
    echo "EFS_FILE_SYSTEM_ID=$EFS_ID"
    echo "EFS_ACCESS_POINT_ID=$ACCESS_POINT_ID"
}

# Generate environment configuration
generate_config() {
    print_info "Generating configuration..."
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region "$AWS_REGION")
    SUBNET_IDS=($(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text --region "$AWS_REGION"))
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text --region "$AWS_REGION")
    
    cat > aws-config.env << EOF
# Generated AWS Configuration
AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
AWS_REGION=$AWS_REGION
CLUSTER_NAME=village-cluster
SERVICE_NAME=village-traffic-collector
ECR_REPOSITORY=village-traffic-collector

# Network Configuration
VPC_ID=$VPC_ID
SUBNET_ONE=${SUBNET_IDS[0]}
SUBNET_TWO=${SUBNET_IDS[1]:-${SUBNET_IDS[0]}}
SECURITY_GROUP_ID=$SECURITY_GROUP_ID

# EFS Configuration
EFS_FILE_SYSTEM_ID=${EFS_ID:-}
EFS_ACCESS_POINT_ID=${ACCESS_POINT_ID:-}

# Secrets Manager ARNs
TOMTOM_API_KEY_SECRET=arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:village/tomtom-api-key
DATABASE_URL_SECRET=arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:village/database-url
API_SECRET_KEY_SECRET=arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:village/api-secret-key
EOF
    
    print_success "Configuration saved to aws-config.env"
}

# Main setup function
setup_aws_infrastructure() {
    print_info "Setting up AWS infrastructure for Village Traffic Collector..."
    
    create_iam_roles
    create_secrets
    create_log_group
    create_networking
    create_efs
    generate_config
    
    print_success "AWS infrastructure setup completed!"
    print_info "Next steps:"
    print_info "1. Review the generated aws-config.env file"
    print_info "2. Run './deploy.sh deploy' to deploy the application"
    print_info "3. Monitor the deployment in the AWS ECS console"
}

# Cleanup function
cleanup_aws_infrastructure() {
    print_warning "This will delete ALL AWS resources for Village Traffic Collector!"
    print_warning "Are you sure you want to continue? (yes/no)"
    read -r confirm
    
    if [[ "$confirm" != "yes" ]]; then
        print_info "Cleanup cancelled"
        exit 0
    fi
    
    print_info "Cleaning up AWS infrastructure..."
    
    # Delete secrets
    aws secretsmanager delete-secret --secret-id village/tomtom-api-key --force-delete-without-recovery || true
    aws secretsmanager delete-secret --secret-id village/database-url --force-delete-without-recovery || true
    aws secretsmanager delete-secret --secret-id village/api-secret-key --force-delete-without-recovery || true
    
    # Delete log group
    aws logs delete-log-group --log-group-name /ecs/village-traffic-collector || true
    
    # Delete EFS (if exists)
    if [[ -n "${EFS_ID:-}" ]]; then
        # Delete access points first
        ACCESS_POINTS=$(aws efs describe-access-points --file-system-id "$EFS_ID" --query 'AccessPoints[*].AccessPointId' --output text)
        for ap in $ACCESS_POINTS; do
            aws efs delete-access-point --access-point-id "$ap" || true
        done
        
        # Delete file system
        aws efs delete-file-system --file-system-id "$EFS_ID" || true
    fi
    
    print_success "Cleanup completed"
}

# Usage function
usage() {
    echo "Usage: $0 [setup|cleanup]"
    echo ""
    echo "Commands:"
    echo "  setup   - Set up AWS infrastructure for ECS deployment"
    echo "  cleanup - Remove all AWS resources (DESTRUCTIVE)"
    echo ""
    echo "Environment variables:"
    echo "  AWS_REGION - AWS region (default: us-east-1)"
}

# Main script logic
case "${1:-}" in
    setup)
        setup_aws_infrastructure
        ;;
    cleanup)
        cleanup_aws_infrastructure
        ;;
    *)
        usage
        exit 1
        ;;
esac