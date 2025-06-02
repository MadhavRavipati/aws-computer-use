# ABOUTME: Output values from Lambda module
# ABOUTME: Exports Lambda function ARNs and names for API Gateway integration

output "session_manager_lambda_arn" {
  description = "ARN of the session manager Lambda function"
  value       = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:computer-use-session-manager-${var.environment}"
}

output "session_manager_lambda_name" {
  description = "Name of the session manager Lambda function"
  value       = "computer-use-session-manager-${var.environment}"
}

output "websocket_handler_lambda_arn" {
  description = "ARN of the WebSocket handler Lambda function"
  value       = aws_lambda_function.websocket_handler.arn
}

output "websocket_handler_lambda_name" {
  description = "Name of the WebSocket handler Lambda function"
  value       = aws_lambda_function.websocket_handler.function_name
}

output "connections_table_arn" {
  description = "ARN of the connections DynamoDB table"
  value       = aws_dynamodb_table.connections.arn
}

output "connections_table_name" {
  description = "Name of the connections DynamoDB table"
  value       = aws_dynamodb_table.connections.name
}

# Data sources needed for outputs
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}