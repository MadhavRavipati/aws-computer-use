# ABOUTME: Input variables for Lambda module
# ABOUTME: Defines required table ARNs and ECS configuration

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "sessions_table_arn" {
  description = "ARN of the sessions DynamoDB table"
  type        = string
}

variable "sessions_table_name" {
  description = "Name of the sessions DynamoDB table"
  type        = string
}

variable "connections_table_arn" {
  description = "ARN of the connections DynamoDB table"
  type        = string
  default     = ""
}

variable "connections_table_name" {
  description = "Name of the connections DynamoDB table"
  type        = string
  default     = ""
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task IAM role"
  type        = string
}

variable "ecs_execution_role_arn" {
  description = "ARN of the ECS execution IAM role"
  type        = string
}