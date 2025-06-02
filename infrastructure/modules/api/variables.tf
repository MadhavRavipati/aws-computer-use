# ABOUTME: Input variables for API Gateway module
# ABOUTME: Defines required Lambda ARNs and configuration

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "session_manager_lambda_arn" {
  description = "ARN of the session manager Lambda function"
  type        = string
}

variable "session_manager_lambda_name" {
  description = "Name of the session manager Lambda function"
  type        = string
}

variable "websocket_handler_lambda_arn" {
  description = "ARN of the WebSocket handler Lambda function"
  type        = string
}

variable "websocket_handler_lambda_name" {
  description = "Name of the WebSocket handler Lambda function"
  type        = string
}