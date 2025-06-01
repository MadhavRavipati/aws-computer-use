# ABOUTME: Output values for development environment
# ABOUTME: Exposes important resource identifiers and endpoints

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api.api_endpoint
}

output "websocket_endpoint" {
  description = "WebSocket API endpoint URL"
  value       = module.api.websocket_endpoint
}

output "frontend_url" {
  description = "CloudFront distribution URL"
  value       = module.frontend.cloudfront_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "bedrock_agent_id" {
  description = "ID of the Bedrock agent"
  value       = module.bedrock.agent_id
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for assets"
  value       = module.storage.s3_bucket_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB sessions table"
  value       = module.storage.dynamodb_table_name
}

output "ecr_repositories" {
  description = "ECR repository URLs"
  value = {
    desktop    = module.ecs.desktop_repository_url
    vnc_bridge = module.ecs.vnc_bridge_repository_url
  }
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.networking.private_subnet_ids
}

output "deployment_instructions" {
  description = "Next steps for deployment"
  value = <<-EOT
    Deployment Instructions:
    
    1. Build and push Docker images:
       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.ecs.desktop_repository_url}
       docker build -t ${module.ecs.desktop_repository_url}:latest ./containers/desktop
       docker push ${module.ecs.desktop_repository_url}:latest
    
    2. Deploy Lambda functions:
       cd backend && ./deploy-lambdas.sh
    
    3. Update frontend configuration:
       API_ENDPOINT=${module.api.api_endpoint}
       WS_ENDPOINT=${module.api.websocket_endpoint}
    
    4. Deploy frontend:
       cd frontend && npm run build && aws s3 sync out/ s3://${module.storage.s3_bucket_name}
  EOT
}