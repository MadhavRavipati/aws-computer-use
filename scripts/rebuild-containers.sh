#!/bin/bash
# ABOUTME: Script to rebuild and push container images to ECR
# ABOUTME: Ensures AMD64 architecture for ECS Fargate compatibility

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID="156246831523"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo -e "${YELLOW}Starting container rebuild process...${NC}"

# Login to ECR
echo -e "${GREEN}Logging into ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Build and push VNC Bridge container
echo -e "${GREEN}Building VNC Bridge container...${NC}"
cd backend/
docker build --platform linux/amd64 -t computer-use/vnc-bridge:latest -f Dockerfile.vnc-bridge .
docker tag computer-use/vnc-bridge:latest ${ECR_REGISTRY}/computer-use/vnc-bridge-dev:latest
docker push ${ECR_REGISTRY}/computer-use/vnc-bridge-dev:latest
echo -e "${GREEN}VNC Bridge container pushed successfully${NC}"

# Build and push Desktop container
echo -e "${GREEN}Building Desktop container...${NC}"
cd ../containers/desktop/
docker build --platform linux/amd64 -t computer-use/desktop:latest -f Dockerfile.amd64 .
docker tag computer-use/desktop:latest ${ECR_REGISTRY}/computer-use/desktop-dev:latest
docker push ${ECR_REGISTRY}/computer-use/desktop-dev:latest
echo -e "${GREEN}Desktop container pushed successfully${NC}"

# Update ECS service to use new images
echo -e "${GREEN}Updating ECS service...${NC}"
aws ecs update-service \
    --cluster computer-use-dev \
    --service computer-use-service-dev \
    --force-new-deployment \
    --region ${AWS_REGION}

echo -e "${GREEN}Container rebuild complete! ECS service is being updated.${NC}"
echo -e "${YELLOW}Monitor the deployment with:${NC}"
echo "aws ecs describe-services --cluster computer-use-dev --services computer-use-service-dev --region ${AWS_REGION}"