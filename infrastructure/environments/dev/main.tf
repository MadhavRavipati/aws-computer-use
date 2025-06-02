# ABOUTME: Simplified Terraform configuration for initial deployment
# ABOUTME: Uses only existing modules to deploy core infrastructure

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "computer-use-demo"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Networking module
module "networking" {
  source = "../../modules/networking"
  
  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  use_existing_vpc   = var.use_existing_vpc
  existing_vpc_id    = var.existing_vpc_id
  availability_zones = data.aws_availability_zones.available.names
}

# Storage resources
module "storage" {
  source = "../../modules/storage"
  
  environment = var.environment
  account_id  = data.aws_caller_identity.current.account_id
}

# ECS cluster and services
module "ecs" {
  source = "../../modules/ecs"
  
  environment     = var.environment
  vpc_id          = module.networking.vpc_id
  private_subnets = module.networking.private_subnet_ids
  public_subnets  = module.networking.public_subnet_ids
}

# Lambda functions
module "lambda" {
  source = "../../modules/lambda"
  
  environment            = var.environment
  sessions_table_arn     = module.storage.dynamodb_table_arn
  sessions_table_name    = module.storage.dynamodb_table_name
  ecs_cluster_name       = module.ecs.cluster_name
  ecs_task_role_arn      = module.ecs.task_role_arn
  ecs_execution_role_arn = module.ecs.execution_role_arn
}

# API Gateway
module "api" {
  source = "../../modules/api"
  
  environment                   = var.environment
  session_manager_lambda_arn    = module.lambda.session_manager_lambda_arn
  session_manager_lambda_name   = module.lambda.session_manager_lambda_name
  websocket_handler_lambda_arn  = module.lambda.websocket_handler_lambda_arn
  websocket_handler_lambda_name = module.lambda.websocket_handler_lambda_name
}

# CloudFront distribution
module "cloudfront" {
  source = "../../modules/cloudfront"
  
  environment                    = var.environment
  s3_bucket_id                   = module.storage.s3_bucket_id
  s3_bucket_regional_domain_name = module.storage.s3_bucket_regional_domain_name
  s3_bucket_arn                  = module.storage.frontend_bucket_arn
  api_gateway_url                = module.api.rest_api_endpoint
  websocket_url                  = module.api.websocket_api_endpoint
}

# Outputs for reference
output "vpc_id" {
  value = module.networking.vpc_id
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "s3_bucket_name" {
  value = module.storage.s3_bucket_name
}

output "dynamodb_table_name" {
  value = module.storage.dynamodb_table_name
}

output "rest_api_endpoint" {
  value = module.api.rest_api_endpoint
}

output "websocket_api_endpoint" {
  value = module.api.websocket_api_endpoint
}

output "cloudfront_distribution_url" {
  value = module.cloudfront.distribution_url
}

output "cloudfront_distribution_id" {
  value = module.cloudfront.distribution_id
}