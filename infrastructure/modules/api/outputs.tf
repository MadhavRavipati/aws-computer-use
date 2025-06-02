# ABOUTME: Output values from API Gateway module
# ABOUTME: Exports API endpoints and WebSocket URLs

output "rest_api_id" {
  description = "ID of the REST API"
  value       = aws_api_gateway_rest_api.main.id
}

output "rest_api_endpoint" {
  description = "Base URL for the REST API"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "websocket_api_id" {
  description = "ID of the WebSocket API"
  value       = aws_apigatewayv2_api.websocket.id
}

output "websocket_api_endpoint" {
  description = "WebSocket connection URL"
  value       = aws_apigatewayv2_stage.websocket.invoke_url
}

output "api_gateway_role_arn" {
  description = "ARN of the API Gateway IAM role"
  value       = aws_iam_role.api_gateway.arn
}