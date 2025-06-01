# ABOUTME: Main Terraform configuration for development environment
# ABOUTME: Orchestrates all AWS resources for Computer Use Demo

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Configure this based on your AWS account
    # bucket = "your-terraform-state-bucket"
    # key    = "computer-use/dev/terraform.tfstate"
    # region = "us-west-2"
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

# Use existing VPC if available, otherwise create new one
data "aws_vpc" "existing" {
  count = var.use_existing_vpc ? 1 : 0
  id    = var.existing_vpc_id
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

# ECS cluster and services
module "ecs" {
  source = "../../modules/ecs"
  
  environment    = var.environment
  vpc_id         = module.networking.vpc_id
  private_subnets = module.networking.private_subnet_ids
  public_subnets  = module.networking.public_subnet_ids
}

# Bedrock agent configuration
module "bedrock" {
  source = "../../modules/bedrock"
  
  environment      = var.environment
  lambda_role_arn  = module.lambda.execution_role_arn
  s3_bucket_arn    = module.storage.s3_bucket_arn
  dynamodb_table_arn = module.storage.dynamodb_table_arn
}

# Lambda functions
module "lambda" {
  source = "../../modules/lambda"
  
  environment        = var.environment
  vpc_id            = module.networking.vpc_id
  private_subnets   = module.networking.private_subnet_ids
  ecs_cluster_arn   = module.ecs.cluster_arn
  dynamodb_table_name = module.storage.dynamodb_table_name
  s3_bucket_name     = module.storage.s3_bucket_name
}

# Storage resources
module "storage" {
  source = "../../modules/storage"
  
  environment = var.environment
  account_id  = data.aws_caller_identity.current.account_id
}

# API Gateway
module "api" {
  source = "../../modules/api"
  
  environment       = var.environment
  lambda_functions  = module.lambda.function_arns
  allowed_origins   = var.allowed_origins
}

# Monitoring and alerts
module "monitoring" {
  source = "../../modules/monitoring"
  
  environment              = var.environment
  ecs_cluster_name        = module.ecs.cluster_name
  bedrock_agent_id        = module.bedrock.agent_id
  budget_notification_email = var.budget_notification_email
}

# Frontend deployment
module "frontend" {
  source = "../../modules/frontend"
  
  environment = var.environment
  domain_name = var.domain_name
}