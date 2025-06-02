# ABOUTME: API Gateway module for REST and WebSocket APIs
# ABOUTME: Provides session management and real-time VNC streaming endpoints

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  common_tags = {
    Module = "api"
  }
}

# REST API for session management
resource "aws_api_gateway_rest_api" "main" {
  name        = "computer-use-api-${var.environment}"
  description = "REST API for Computer Use Demo session management"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.common_tags
}

# Resources for REST API
resource "aws_api_gateway_resource" "sessions" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "sessions"
}

resource "aws_api_gateway_resource" "session_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.sessions.id
  path_part   = "{sessionId}"
}

# Methods for session management
resource "aws_api_gateway_method" "create_session" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.sessions.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "get_session" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.session_id.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "delete_session" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.session_id.id
  http_method   = "DELETE"
  authorization = "NONE"
}

# Lambda integrations
resource "aws_api_gateway_integration" "create_session" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.sessions.id
  http_method = aws_api_gateway_method.create_session.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${var.session_manager_lambda_arn}/invocations"
}

resource "aws_api_gateway_integration" "get_session" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.session_id.id
  http_method = aws_api_gateway_method.get_session.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${var.session_manager_lambda_arn}/invocations"
}

resource "aws_api_gateway_integration" "delete_session" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.session_id.id
  http_method = aws_api_gateway_method.delete_session.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${var.session_manager_lambda_arn}/invocations"
}

# REST API deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.sessions.id,
      aws_api_gateway_resource.session_id.id,
      aws_api_gateway_method.create_session.id,
      aws_api_gateway_method.get_session.id,
      aws_api_gateway_method.delete_session.id,
      aws_api_gateway_integration.create_session.id,
      aws_api_gateway_integration.get_session.id,
      aws_api_gateway_integration.delete_session.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  xray_tracing_enabled = true

  tags = local.common_tags
}

# WebSocket API for VNC streaming
resource "aws_apigatewayv2_api" "websocket" {
  name                       = "computer-use-ws-${var.environment}"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
  
  tags = local.common_tags
}

# WebSocket routes
resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$connect"
  
  target = "integrations/${aws_apigatewayv2_integration.ws_connect.id}"
}

resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  
  target = "integrations/${aws_apigatewayv2_integration.ws_disconnect.id}"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  
  target = "integrations/${aws_apigatewayv2_integration.ws_default.id}"
}

# WebSocket integrations
resource "aws_apigatewayv2_integration" "ws_connect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  
  integration_method     = "POST"
  integration_uri        = var.websocket_handler_lambda_arn
  credentials_arn        = aws_iam_role.api_gateway.arn
}

resource "aws_apigatewayv2_integration" "ws_disconnect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  
  integration_method     = "POST"
  integration_uri        = var.websocket_handler_lambda_arn
  credentials_arn        = aws_iam_role.api_gateway.arn
}

resource "aws_apigatewayv2_integration" "ws_default" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  
  integration_method     = "POST"
  integration_uri        = var.websocket_handler_lambda_arn
  credentials_arn        = aws_iam_role.api_gateway.arn
}

# WebSocket deployment
resource "aws_apigatewayv2_deployment" "websocket" {
  api_id      = aws_apigatewayv2_api.websocket.id
  description = "WebSocket deployment for ${var.environment}"

  triggers = {
    redeployment = sha1(jsonencode([
      aws_apigatewayv2_route.connect.id,
      aws_apigatewayv2_route.disconnect.id,
      aws_apigatewayv2_route.default.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_apigatewayv2_stage" "websocket" {
  api_id        = aws_apigatewayv2_api.websocket.id
  deployment_id = aws_apigatewayv2_deployment.websocket.id
  name          = var.environment

  tags = local.common_tags
}

# IAM role for API Gateway
resource "aws_iam_role" "api_gateway" {
  name = "computer-use-api-gateway-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "api_gateway_lambda" {
  name = "lambda-invoke"
  role = aws_iam_role.api_gateway.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          var.session_manager_lambda_arn,
          var.websocket_handler_lambda_arn
        ]
      }
    ]
  })
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_gateway_rest" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.session_manager_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_websocket" {
  statement_id  = "AllowAPIGatewayWebSocketInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.websocket_handler_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

# CORS configuration for REST API
resource "aws_api_gateway_method" "options_sessions" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.sessions.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_sessions" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.sessions.id
  http_method = aws_api_gateway_method.options_sessions.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "options_sessions" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.sessions.id
  http_method = aws_api_gateway_method.options_sessions.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_sessions" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.sessions.id
  http_method = aws_api_gateway_method.options_sessions.http_method
  status_code = aws_api_gateway_method_response.options_sessions.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,DELETE'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}