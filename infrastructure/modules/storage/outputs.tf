# ABOUTME: Output values for storage module
# ABOUTME: Exposes bucket names, table names, and ARNs

output "s3_bucket_name" {
  description = "Name of the S3 bucket for assets"
  value       = aws_s3_bucket.assets.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for assets"
  value       = aws_s3_bucket.assets.arn
}

output "frontend_bucket_name" {
  description = "Name of the S3 bucket for frontend"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_arn" {
  description = "ARN of the S3 bucket for frontend"
  value       = aws_s3_bucket.frontend.arn
}

output "frontend_bucket_website_endpoint" {
  description = "Website endpoint of the frontend bucket"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB sessions table"
  value       = aws_dynamodb_table.sessions.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB sessions table"
  value       = aws_dynamodb_table.sessions.arn
}

output "agent_cache_table_name" {
  description = "Name of the DynamoDB agent cache table"
  value       = aws_dynamodb_table.agent_cache.name
}

output "agent_cache_table_arn" {
  description = "ARN of the DynamoDB agent cache table"
  value       = aws_dynamodb_table.agent_cache.arn
}

output "vnc_password_secret_arn" {
  description = "ARN of the VNC password secret"
  value       = aws_secretsmanager_secret.vnc_password.arn
}