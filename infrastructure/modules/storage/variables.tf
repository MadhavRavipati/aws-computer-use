# ABOUTME: Variable definitions for storage module
# ABOUTME: Configures S3 and DynamoDB settings

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "enable_backups" {
  description = "Enable point-in-time recovery for DynamoDB"
  type        = bool
  default     = true
}