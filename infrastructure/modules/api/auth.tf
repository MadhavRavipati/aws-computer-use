# ABOUTME: API Gateway authentication configuration
# ABOUTME: Sets up Lambda authorizer and API key management

# DynamoDB table for API keys
resource "aws_dynamodb_table" "api_keys" {
  name           = "computer-use-api-keys-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "api_key"
  
  attribute {
    name = "api_key"
    type = "S"
  }
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  global_secondary_index {
    name            = "user-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }
  
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  
  tags = var.tags
}

# Lambda function for authorization
resource "aws_lambda_function" "authorizer" {
  function_name = "computer-use-api-authorizer-${var.environment}"
  role          = aws_iam_role.authorizer.arn
  handler       = "auth_handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 10
  
  filename         = data.archive_file.auth_handler.output_path
  source_code_hash = data.archive_file.auth_handler.output_base64sha256
  
  environment {
    variables = {
      API_KEYS_TABLE = aws_dynamodb_table.api_keys.name
    }
  }
  
  tags = var.tags
}

# Lambda function for creating API keys
resource "aws_lambda_function" "create_api_key" {
  function_name = "computer-use-create-api-key-${var.environment}"
  role          = aws_iam_role.authorizer.arn
  handler       = "auth_handler.create_api_key_handler"
  runtime       = "python3.12"
  timeout       = 10
  
  filename         = data.archive_file.auth_handler.output_path
  source_code_hash = data.archive_file.auth_handler.output_base64sha256
  
  environment {
    variables = {
      API_KEYS_TABLE = aws_dynamodb_table.api_keys.name
    }
  }
  
  tags = var.tags
}

# Package Lambda function
data "archive_file" "auth_handler" {
  type        = "zip"
  source_file = "${path.module}/../../../backend/functions/auth_handler.py"
  output_path = "${path.module}/auth_handler.zip"
}

# IAM role for authorizer Lambda
resource "aws_iam_role" "authorizer" {
  name = "computer-use-api-authorizer-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
  
  tags = var.tags
}

# IAM policy for authorizer Lambda
resource "aws_iam_policy" "authorizer" {
  name = "computer-use-api-authorizer-policy-${var.environment}"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.api_keys.arn,
          "${aws_dynamodb_table.api_keys.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# Attach policies to role
resource "aws_iam_role_policy_attachment" "authorizer_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.authorizer.name
}

resource "aws_iam_role_policy_attachment" "authorizer_custom" {
  policy_arn = aws_iam_policy.authorizer.arn
  role       = aws_iam_role.authorizer.name
}

# API Gateway authorizer
resource "aws_apigatewayv2_authorizer" "api_key" {
  api_id                            = var.api_gateway_id
  authorizer_type                   = "REQUEST"
  authorizer_uri                    = aws_lambda_function.authorizer.invoke_arn
  authorizer_payload_format_version = "2.0"
  enable_simple_responses           = true
  name                              = "api-key-authorizer"
  
  # Cache authorization results for 5 minutes
  authorizer_result_ttl_in_seconds = 300
  
  identity_sources = ["$request.header.Authorization"]
}

# Grant API Gateway permission to invoke authorizer
resource "aws_lambda_permission" "api_gateway_authorizer" {
  statement_id  = "AllowAPIGatewayInvokeAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

# Grant API Gateway permission to invoke create API key function
resource "aws_lambda_permission" "api_gateway_create_key" {
  statement_id  = "AllowAPIGatewayInvokeCreateKey"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_api_key.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

# Update API routes to use authorizer
resource "aws_apigatewayv2_route" "sessions_post_auth" {
  api_id    = var.api_gateway_id
  route_key = "POST /sessions"
  target    = "integrations/${var.session_integration_id}"
  
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.api_key.id
}

resource "aws_apigatewayv2_route" "sessions_get_auth" {
  api_id    = var.api_gateway_id
  route_key = "GET /sessions/{id}"
  target    = "integrations/${var.session_integration_id}"
  
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.api_key.id
}

resource "aws_apigatewayv2_route" "sessions_delete_auth" {
  api_id    = var.api_gateway_id
  route_key = "DELETE /sessions/{id}"
  target    = "integrations/${var.session_integration_id}"
  
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.api_key.id
}

# Admin route for creating API keys (requires separate auth)
resource "aws_apigatewayv2_route" "create_api_key" {
  api_id    = var.api_gateway_id
  route_key = "POST /admin/api-keys"
  target    = "integrations/${aws_apigatewayv2_integration.create_api_key.id}"
}

resource "aws_apigatewayv2_integration" "create_api_key" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.create_api_key.invoke_arn
}

# Outputs
output "authorizer_id" {
  value = aws_apigatewayv2_authorizer.api_key.id
}

output "api_keys_table_name" {
  value = aws_dynamodb_table.api_keys.name
}