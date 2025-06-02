# ABOUTME: Lambda module for serverless functions
# ABOUTME: Deploys session manager, WebSocket handler, and Bedrock agent functions

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
    Module = "lambda"
  }
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

# Session Manager Lambda
resource "aws_iam_role" "session_manager" {
  name               = "computer-use-session-manager-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "session_manager_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.session_manager.name
}

resource "aws_iam_role_policy_attachment" "session_manager_vpc" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.session_manager.name
}

resource "aws_iam_role_policy" "session_manager_policy" {
  name = "session-manager-policy"
  role = aws_iam_role.session_manager.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "ecs:StopTask",
          "ecs:DescribeTasks",
          "ecs:ListTasks"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.sessions_table_arn,
          "${var.sessions_table_arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          var.ecs_task_role_arn,
          var.ecs_execution_role_arn
        ]
      }
    ]
  })
}

# WebSocket Handler Lambda
resource "aws_iam_role" "websocket_handler" {
  name               = "computer-use-websocket-handler-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "websocket_handler_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.websocket_handler.name
}

resource "aws_iam_role_policy" "websocket_handler_policy" {
  name = "websocket-handler-policy"
  role = aws_iam_role.websocket_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.sessions_table_arn,
          aws_dynamodb_table.connections.arn,
          "${var.sessions_table_arn}/index/*",
          "${aws_dynamodb_table.connections.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeTasks",
          "ecs:ListTasks"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "websocket_handler" {
  filename         = "${path.module}/lambda_packages/websocket_handler.zip"
  function_name    = "computer-use-websocket-handler-${var.environment}"
  role            = aws_iam_role.websocket_handler.arn
  handler         = "websocket_handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/lambda_packages/websocket_handler.zip")
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      CONNECTIONS_TABLE = aws_dynamodb_table.connections.name
      SESSIONS_TABLE    = var.sessions_table_name
      ECS_CLUSTER      = var.ecs_cluster_name
    }
  }

  tags = local.common_tags
}

# DynamoDB table for WebSocket connections
resource "aws_dynamodb_table" "connections" {
  name           = "computer-use-connections-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "connection_id"

  attribute {
    name = "connection_id"
    type = "S"
  }

  attribute {
    name = "session_id"
    type = "S"
  }

  global_secondary_index {
    name            = "session-index"
    hash_key        = "session_id"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = local.common_tags
}