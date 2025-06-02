# ABOUTME: Input variables for CloudFront distribution module
# ABOUTME: Defines parameters for CDN configuration and S3 integration

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "s3_bucket_id" {
  description = "ID of the S3 bucket to serve content from"
  type        = string
}

variable "s3_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "api_gateway_url" {
  description = "URL of the API Gateway REST endpoint"
  type        = string
}

variable "websocket_url" {
  description = "URL of the WebSocket API endpoint"
  type        = string
}