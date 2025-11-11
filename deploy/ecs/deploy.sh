#!/bin/bash

# ECS Deployment Script for Village Traffic Collector
# This script deploys the traffic collector daemon to Amazon ECS

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
CLUSTER_NAME="${CLUSTER_NAME:-village-cluster}"
SERVICE_NAME="${SERVICE_NAME:-village-traffic-collector}"
ECR_REPOSITORY="${ECR_REPOSITORY:-village-traffic-collector}"

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

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is not installed. Please install it first."
        exit 1
    fi
    
    # Get AWS account ID if not provided
    if [[ -z "$AWS_ACCOUNT_ID" ]]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
        print_info "Detected AWS Account ID: $AWS_ACCOUNT_ID"
    fi
    
    print_success "Prerequisites check passed"
}

# Create ECR repository if it doesn't exist
setup_ecr() {
    print_info "Setting up ECR repository..."
    
    if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &> /dev/null; then
        print_info "Creating ECR repository: $ECR_REPOSITORY"
        aws ecr create-repository \
            --repository-name "$ECR_REPOSITORY" \
            --region "$AWS_REGION" \
            --image-tag-mutability MUTABLE \
            --image-scanning-configuration scanOnPush=true
        
        print_success "ECR repository created"
    else
        print_info "ECR repository already exists"
    fi
}

# Build and push Docker image
build_and_push() {
    print_info "Building and pushing Docker image..."
    
    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    # Build image
    IMAGE_TAG="$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"
    IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
    LATEST_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
    
    print_info "Building image: $IMAGE_URI"
    docker build -t "$IMAGE_URI" -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_ROOT"
    
    # Tag as latest
    docker tag "$IMAGE_URI" "$LATEST_URI"
    
    # Push both tags
    print_info "Pushing images to ECR..."
    docker push "$IMAGE_URI"
    docker push "$LATEST_URI"
    
    print_success "Docker images pushed successfully"
    echo "IMAGE_URI=$IMAGE_URI" > "${SCRIPT_DIR}/.build-info"
}

# Create ECS cluster if it doesn't exist
setup_cluster() {
    print_info "Setting up ECS cluster..."
    
    if ! aws ecs describe-clusters --clusters "$CLUSTER_NAME" --region "$AWS_REGION" --query 'clusters[0].status' --output text 2>/dev/null | grep -q ACTIVE; then
        print_info "Creating ECS cluster: $CLUSTER_NAME"
        aws ecs create-cluster --cluster-name "$CLUSTER_NAME" --region "$AWS_REGION" --capacity-providers FARGATE --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
        print_success "ECS cluster created"
    else
        print_info "ECS cluster already exists"
    fi
}

# Register task definition
register_task_definition() {
    print_info "Registering ECS task definition..."
    
    # Read image URI from build info
    if [[ -f "${SCRIPT_DIR}/.build-info" ]]; then
        source "${SCRIPT_DIR}/.build-info"
    else
        IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
    fi
    
    # Use simpler task definition and substitute variables
    TASK_DEF_JSON=$(cat "$SCRIPT_DIR/task-definition-simple.json" | \
        sed "s|PLACEHOLDER_IMAGE|$IMAGE_URI|g" | \
        sed "s|us-east-1|$AWS_REGION|g" | \
        sed "s|ACCOUNT_ID|$AWS_ACCOUNT_ID|g")
    
    # Debug: show the JSON being sent
    echo "$TASK_DEF_JSON" > /tmp/task-def-debug.json
    print_info "Task definition JSON saved to /tmp/task-def-debug.json for debugging"
    
    # Save to temporary file and register the task definition
    echo "$TASK_DEF_JSON" > /tmp/task-def-temp.json
    TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file:///tmp/task-def-temp.json --region "$AWS_REGION" --query 'taskDefinition.taskDefinitionArn' --output text)
    rm /tmp/task-def-temp.json
    
    print_success "Task definition registered: $TASK_DEF_ARN"
}

# Create or update ECS service
deploy_service() {
    print_info "Deploying ECS service..."
    
    # Check if service exists
    if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$AWS_REGION" --query 'services[0].status' --output text 2>/dev/null | grep -q ACTIVE; then
        print_info "Updating existing service: $SERVICE_NAME"
        aws ecs update-service \
            --cluster "$CLUSTER_NAME" \
            --service "$SERVICE_NAME" \
            --task-definition "$TASK_DEF_ARN" \
            --region "$AWS_REGION" > /dev/null
    else
        print_info "Creating new service: $SERVICE_NAME"
        
        # Get default VPC and subnets
        VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region "$AWS_REGION")
        print_info "Using VPC: $VPC_ID"
        
        # Get subnets as array
        SUBNET_ARRAY=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output json --region "$AWS_REGION")
        SUBNET_IDS=$(echo "$SUBNET_ARRAY" | jq -r '.[]' | head -2 | tr '\n' ',' | sed 's/,$//')
        print_info "Using subnets: $SUBNET_IDS"
        
        SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text --region "$AWS_REGION")
        print_info "Using security group: $SECURITY_GROUP_ID"
        
        # Create network configuration JSON
        NETWORK_CONFIG="{\"awsvpcConfiguration\":{\"subnets\":[\"$(echo $SUBNET_IDS | sed 's/,/\",\"/g')\"],\"securityGroups\":[\"$SECURITY_GROUP_ID\"],\"assignPublicIp\":\"ENABLED\"}}"
        
        # Create service
        aws ecs create-service \
            --cluster "$CLUSTER_NAME" \
            --service-name "$SERVICE_NAME" \
            --task-definition "$TASK_DEF_ARN" \
            --desired-count 1 \
            --launch-type FARGATE \
            --network-configuration "$NETWORK_CONFIG" \
            --region "$AWS_REGION" > /dev/null
    fi
    
    print_success "Service deployment initiated"
}

# Wait for service stability
wait_for_stability() {
    print_info "Waiting for service to become stable (this may take a few minutes)..."
    
    aws ecs wait services-stable \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region "$AWS_REGION"
    
    print_success "Service is now stable"
}

# Setup CloudWatch dashboard
setup_monitoring() {
    print_info "Setting up CloudWatch monitoring..."
    
    # Create CloudWatch dashboard
    DASHBOARD_JSON=$(cat << EOF
{
    "widgets": [
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "Village/TrafficCollector", "APIRequestsToday", "Service", "$SERVICE_NAME", "Cluster", "$CLUSTER_NAME" ],
                    [ ".", "QuotaRemaining", ".", ".", ".", "." ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$AWS_REGION",
                "title": "API Usage",
                "period": 300
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "Village/TrafficCollector", "IncidentsTotal", "Service", "$SERVICE_NAME", "Cluster", "$CLUSTER_NAME" ],
                    [ ".", "FlowRecordsTotal", ".", ".", ".", "." ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$AWS_REGION",
                "title": "Data Collection",
                "period": 300
            }
        }
    ]
}
EOF
)
    
    aws cloudwatch put-dashboard \
        --dashboard-name "VillageTrafficCollector" \
        --dashboard-body "$DASHBOARD_JSON" \
        --region "$AWS_REGION"
    
    print_success "CloudWatch dashboard created"
}

# Main deployment function
deploy() {
    print_info "Starting Village Traffic Collector ECS deployment..."
    print_info "Cluster: $CLUSTER_NAME"
    print_info "Service: $SERVICE_NAME"
    print_info "Region: $AWS_REGION"
    
    check_prerequisites
    setup_ecr
    build_and_push
    setup_cluster
    register_task_definition
    deploy_service
    wait_for_stability
    setup_monitoring
    
    print_success "Deployment completed successfully!"
    print_info "Service URL: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME/services/$SERVICE_NAME"
    print_info "CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=VillageTrafficCollector"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up ECS resources..."
    
    # Delete service
    if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$AWS_REGION" --query 'services[0].status' --output text 2>/dev/null | grep -q ACTIVE; then
        print_info "Scaling service to 0..."
        aws ecs update-service --cluster "$CLUSTER_NAME" --service "$SERVICE_NAME" --desired-count 0 --region "$AWS_REGION" > /dev/null
        
        print_info "Waiting for tasks to stop..."
        aws ecs wait services-stable --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$AWS_REGION"
        
        print_info "Deleting service..."
        aws ecs delete-service --cluster "$CLUSTER_NAME" --service "$SERVICE_NAME" --region "$AWS_REGION" > /dev/null
        
        print_success "Service deleted"
    fi
    
    # Delete cluster (if empty)
    print_info "Deleting cluster..."
    aws ecs delete-cluster --cluster "$CLUSTER_NAME" --region "$AWS_REGION" > /dev/null 2>&1 || true
    
    print_success "Cleanup completed"
}

# Show usage
usage() {
    echo "Usage: $0 [deploy|cleanup|status]"
    echo ""
    echo "Commands:"
    echo "  deploy   - Deploy the traffic collector to ECS"
    echo "  cleanup  - Remove all ECS resources"
    echo "  status   - Show current deployment status"
    echo ""
    echo "Environment variables:"
    echo "  AWS_REGION       - AWS region (default: us-east-1)"
    echo "  AWS_ACCOUNT_ID   - AWS account ID (auto-detected)"
    echo "  CLUSTER_NAME     - ECS cluster name (default: village-cluster)"
    echo "  SERVICE_NAME     - ECS service name (default: village-traffic-collector)"
    echo "  ECR_REPOSITORY   - ECR repository name (default: village-traffic-collector)"
}

# Show status
show_status() {
    print_info "ECS Deployment Status"
    print_info "====================="
    
    # Check service status
    if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$AWS_REGION" --query 'services[0].status' --output text 2>/dev/null | grep -q ACTIVE; then
        RUNNING_COUNT=$(aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$AWS_REGION" --query 'services[0].runningCount' --output text)
        DESIRED_COUNT=$(aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$AWS_REGION" --query 'services[0].desiredCount' --output text)
        
        print_success "Service Status: ACTIVE"
        print_info "Running Tasks: $RUNNING_COUNT / $DESIRED_COUNT"
    else
        print_warning "Service not found or not active"
    fi
}

# Main script logic
case "${1:-}" in
    deploy)
        deploy
        ;;
    cleanup)
        cleanup
        ;;
    status)
        show_status
        ;;
    *)
        usage
        exit 1
        ;;
esac