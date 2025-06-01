# ABOUTME: Variable definitions for ECS module
# ABOUTME: Configures cluster, services, and container settings

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnets" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "public_subnets" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}

variable "task_cpu" {
  description = "CPU units for ECS task"
  type        = string
  default     = "2048"
}

variable "task_memory" {
  description = "Memory for ECS task"
  type        = string
  default     = "4096"
}

variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 0
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}