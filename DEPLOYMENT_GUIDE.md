# AWS Computer Use Demo - Deployment Guide

## Pre-Deployment Checklist

### 1. Verify AWS Credentials
```bash
aws sts get-caller-identity
# Should show account: 156246831523, region: us-west-2
```

### 2. Current Deployment Status
- ✅ Infrastructure deployed (VPC, ECS, Lambda, API Gateway)
- ✅ Original containers running (but with issues)
- ❌ New code changes NOT deployed
- ❌ API authentication NOT active
- ❌ Updated containers NOT pushed

## Deployment Steps

### Step 1: Deploy DynamoDB Tables for New Features

```bash
# Create API Keys table
aws dynamodb create-table \
  --table-name computer-use-api-keys-dev \
  --attribute-definitions \
    AttributeName=api_key,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
  --key-schema AttributeName=api_key,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=user-index,Keys=[{AttributeName=user_id,KeyType=HASH}],Projection={ProjectionType=ALL} \
  --billing-mode PAY_PER_REQUEST \
  --region us-west-2

# Create Agent Cache table
aws dynamodb create-table \
  --table-name computer-use-agent-cache-dev \
  --attribute-definitions AttributeName=cache_key,AttributeType=S \
  --key-schema AttributeName=cache_key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --ttl-specification AttributeName=ttl,Enabled=true \
  --region us-west-2
```

### Step 2: Build and Push Updated Containers

```bash
cd /Users/maddy/Documents/repos/aws-computer-use

# Run the rebuild script
./scripts/rebuild-containers.sh

# Or manually:
# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 156246831523.dkr.ecr.us-west-2.amazonaws.com

# Build and push VNC Bridge
cd backend/
docker build --platform linux/amd64 -t computer-use/vnc-bridge:latest -f Dockerfile.vnc-bridge .
docker tag computer-use/vnc-bridge:latest 156246831523.dkr.ecr.us-west-2.amazonaws.com/computer-use/vnc-bridge-dev:latest
docker push 156246831523.dkr.ecr.us-west-2.amazonaws.com/computer-use/vnc-bridge-dev:latest

# Build and push Desktop
cd ../containers/desktop/
docker build --platform linux/amd64 -t computer-use/desktop:latest -f Dockerfile.amd64 .
docker tag computer-use/desktop:latest 156246831523.dkr.ecr.us-west-2.amazonaws.com/computer-use/desktop-dev:latest
docker push 156246831523.dkr.ecr.us-west-2.amazonaws.com/computer-use/desktop-dev:latest
```

### Step 3: Update Lambda Functions

```bash
# Package and update Session Manager
cd /Users/maddy/Documents/repos/aws-computer-use/backend
zip -r session-manager.zip functions/session_manager.py
aws lambda update-function-code \
  --function-name computer-use-session-manager-dev \
  --zip-file fileb://session-manager.zip \
  --region us-west-2

# Package and update Computer Use Agent
zip -r agent.zip agents/computer_use_agent.py utils/
aws lambda update-function-code \
  --function-name computer-use-strands-agent-dev \
  --zip-file fileb://agent.zip \
  --region us-west-2 2>/dev/null || echo "Agent lambda may not exist yet"

# Deploy Auth Handler (new)
zip -r auth-handler.zip functions/auth_handler.py
aws lambda create-function \
  --function-name computer-use-api-authorizer-dev \
  --runtime python3.12 \
  --role arn:aws:iam::156246831523:role/computer-use-lambda-session-dev \
  --handler auth_handler.lambda_handler \
  --zip-file fileb://auth-handler.zip \
  --timeout 10 \
  --environment Variables={API_KEYS_TABLE=computer-use-api-keys-dev} \
  --region us-west-2
```

### Step 4: Update ECS Task Definition

```bash
# Create new task definition with updated container images
aws ecs register-task-definition \
  --family computer-use-dev \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu "2048" \
  --memory "4096" \
  --execution-role-arn arn:aws:iam::156246831523:role/computer-use-ecs-execution-dev \
  --task-role-arn arn:aws:iam::156246831523:role/computer-use-ecs-task-dev \
  --container-definitions '[
    {
      "name": "desktop",
      "image": "156246831523.dkr.ecr.us-west-2.amazonaws.com/computer-use/desktop-dev:latest",
      "portMappings": [
        {"containerPort": 5900, "protocol": "tcp"},
        {"containerPort": 6080, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "DISPLAY", "value": ":1"},
        {"name": "VNC_RESOLUTION", "value": "1920x1080"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:6080/ || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 30
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/computer-use/desktop-dev",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "desktop"
        }
      }
    },
    {
      "name": "vnc-bridge",
      "image": "156246831523.dkr.ecr.us-west-2.amazonaws.com/computer-use/vnc-bridge-dev:latest",
      "portMappings": [
        {"containerPort": 8080, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "VNC_HOST", "value": "localhost"},
        {"name": "VNC_PORT", "value": "5900"},
        {"name": "PYTHONUNBUFFERED", "value": "1"}
      ],
      "dependsOn": [
        {"containerName": "desktop", "condition": "HEALTHY"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 30
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/computer-use/vnc-bridge-dev",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "vnc-bridge"
        }
      }
    }
  ]' \
  --region us-west-2
```

### Step 5: Update ECS Service

```bash
# Force new deployment with updated task definition
aws ecs update-service \
  --cluster computer-use-dev \
  --service computer-use-service-dev \
  --task-definition computer-use-dev \
  --force-new-deployment \
  --region us-west-2

# Monitor deployment
watch -n 5 "aws ecs describe-services \
  --cluster computer-use-dev \
  --services computer-use-service-dev \
  --region us-west-2 \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}'"
```

### Step 6: Configure API Gateway Authentication

```bash
# This requires updating API Gateway routes to use the authorizer
# Since it's complex, we'll create the authorizer first
aws apigatewayv2 create-authorizer \
  --api-id p0lkqwkiy4 \
  --authorizer-type REQUEST \
  --authorizer-uri arn:aws:lambda:us-west-2:156246831523:function:computer-use-api-authorizer-dev \
  --identity-sources '$request.header.Authorization' \
  --name api-key-authorizer \
  --authorizer-payload-format-version 2.0 \
  --enable-simple-responses \
  --region us-west-2

# Grant API Gateway permission to invoke authorizer
aws lambda add-permission \
  --function-name computer-use-api-authorizer-dev \
  --statement-id AllowAPIGatewayInvoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-west-2:156246831523:p0lkqwkiy4/*/*" \
  --region us-west-2
```

### Step 7: Generate Initial API Key

```bash
cd /Users/maddy/Documents/repos/aws-computer-use
python scripts/generate-api-key.py --user-id admin --tier premium
```

### Step 8: Test Deployment

```bash
# Test health of new containers
curl -I http://computer-use-dev-797992487.us-west-2.elb.amazonaws.com/health

# Test API with authentication
API_KEY="<generated-api-key>"
curl -X POST https://p0lkqwkiy4.execute-api.us-west-2.amazonaws.com/dev/sessions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action": "create"}'

# Check container logs
aws logs tail /ecs/computer-use/vnc-bridge-dev --follow --region us-west-2
```

## Rollback Plan

If deployment fails:

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster computer-use-dev \
  --service computer-use-service-dev \
  --task-definition computer-use-dev:3 \
  --force-new-deployment \
  --region us-west-2

# Remove API Gateway authorizer
aws apigatewayv2 delete-authorizer \
  --api-id p0lkqwkiy4 \
  --authorizer-id <authorizer-id> \
  --region us-west-2
```

## Post-Deployment Verification

1. **Check ECS Service Health**
   - All tasks should be RUNNING
   - Health checks should be HEALTHY

2. **Verify API Authentication**
   - Requests without API key should return 401
   - Valid API key should allow access

3. **Test VNC Connection**
   - Create a session
   - Verify VNC bridge can capture screenshots

4. **Monitor CloudWatch Logs**
   - Check for any errors in Lambda functions
   - Verify container logs show successful connections

## Deployment Timeline

Estimated time: 30-45 minutes
- DynamoDB tables: 2 minutes
- Container build/push: 10-15 minutes
- Lambda updates: 5 minutes
- ECS deployment: 10-15 minutes
- Testing: 5-10 minutes