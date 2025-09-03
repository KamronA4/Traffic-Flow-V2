#!/bin/bash

# Script to fix ECS service-linked role issue

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Create ECS service-linked role
create_ecs_service_role() {
    print_info "Creating ECS service-linked role..."
    
    # Check if the role already exists
    if aws iam get-role --role-name AWSServiceRoleForECS &> /dev/null; then
        print_info "ECS service-linked role already exists"
    else
        # Create the service-linked role
        aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com || true
        print_success "ECS service-linked role created"
    fi
}

# Wait for role to be available
wait_for_role() {
    print_info "Waiting for role to be available..."
    sleep 10
    
    if aws iam get-role --role-name AWSServiceRoleForECS &> /dev/null; then
        print_success "ECS service-linked role is ready"
    else
        print_error "Failed to create ECS service-linked role"
        exit 1
    fi
}

# Main execution
print_info "Fixing ECS service-linked role issue..."
create_ecs_service_role
wait_for_role

print_success "ECS service-linked role setup complete!"
print_info "You can now run './deploy.sh deploy' again"