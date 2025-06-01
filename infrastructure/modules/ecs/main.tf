# ABOUTME: ECS module for Fargate cluster and desktop container services
# ABOUTME: Manages ECS cluster, task definitions, services, and auto-scaling

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "computer-use-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs_exec.name
      }
    }
  }
  
  tags = {
    Name = "computer-use-cluster-${var.environment}"
  }
}

# Cluster capacity providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# ECR Repositories
resource "aws_ecr_repository" "desktop" {
  name                 = "computer-use/desktop-${var.environment}"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "AES256"
  }
  
  lifecycle {
    prevent_destroy = false
  }
  
  tags = {
    Name = "computer-use-desktop-${var.environment}"
  }
}

resource "aws_ecr_repository" "vnc_bridge" {
  name                 = "computer-use/vnc-bridge-${var.environment}"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "AES256"
  }
  
  lifecycle {
    prevent_destroy = false
  }
  
  tags = {
    Name = "computer-use-vnc-bridge-${var.environment}"
  }
}

# ECR lifecycle policies
resource "aws_ecr_lifecycle_policy" "desktop" {
  repository = aws_ecr_repository.desktop.name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "ecs_exec" {
  name              = "/ecs/exec/computer-use-${var.environment}"
  retention_in_days = 7
  
  tags = {
    Name = "computer-use-ecs-exec-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "desktop" {
  name              = "/ecs/computer-use/desktop-${var.environment}"
  retention_in_days = 7
  
  tags = {
    Name = "computer-use-desktop-logs-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "vnc_bridge" {
  name              = "/ecs/computer-use/vnc-bridge-${var.environment}"
  retention_in_days = 7
  
  tags = {
    Name = "computer-use-vnc-bridge-logs-${var.environment}"
  }
}

# Task execution role
resource "aws_iam_role" "ecs_execution" {
  name = "computer-use-ecs-execution-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
  
  tags = {
    Name = "computer-use-ecs-execution-${var.environment}"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_basic" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for Secrets Manager access
resource "aws_iam_policy" "ecs_execution_secrets" {
  name = "computer-use-ecs-execution-secrets-${var.environment}"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:computer-use/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_secrets" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = aws_iam_policy.ecs_execution_secrets.arn
}

# Task role
resource "aws_iam_role" "ecs_task" {
  name = "computer-use-ecs-task-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
  
  tags = {
    Name = "computer-use-ecs-task-${var.environment}"
  }
}

# Task role policy - will be updated by other modules
resource "aws_iam_policy" "ecs_task_base" {
  name = "computer-use-ecs-task-base-${var.environment}"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.desktop.arn}:*",
          "${aws_cloudwatch_log_group.vnc_bridge.arn}:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_base" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_task_base.arn
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "computer-use-alb-${var.environment}"
  description = "Security group for ALB"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from anywhere"
  }
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP from anywhere (redirect to HTTPS)"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }
  
  tags = {
    Name = "computer-use-alb-${var.environment}"
  }
}

resource "aws_security_group" "desktop" {
  name        = "computer-use-desktop-${var.environment}"
  description = "Security group for desktop containers"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port       = 6080
    to_port         = 6080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "noVNC from ALB"
  }
  
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.main.cidr_block]
    description = "VNC bridge API from VPC"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }
  
  tags = {
    Name = "computer-use-desktop-${var.environment}"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "computer-use-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = var.public_subnets
  
  enable_deletion_protection = false
  enable_http2              = true
  enable_cross_zone_load_balancing = true
  
  tags = {
    Name = "computer-use-alb-${var.environment}"
  }
}

# Target Group for desktop containers
resource "aws_lb_target_group" "desktop" {
  name        = "computer-use-desktop-${var.environment}"
  port        = 6080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/"
    matcher             = "200"
  }
  
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 3600
    enabled         = true
  }
  
  deregistration_delay = 30
  
  tags = {
    Name = "computer-use-desktop-tg-${var.environment}"
  }
}

# HTTP listener (redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS listener will be added when certificate is available
# For now, using self-signed certificate
resource "aws_lb_listener" "https" {
  count = var.certificate_arn != "" ? 1 : 0
  
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.desktop.arn
  }
}

# Service Discovery
resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "computer-use.local"
  vpc  = var.vpc_id
  
  tags = {
    Name = "computer-use-service-discovery-${var.environment}"
  }
}

resource "aws_service_discovery_service" "desktop" {
  name = "desktop"
  
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
  
  health_check_custom_config {
    failure_threshold = 1
  }
  
  tags = {
    Name = "computer-use-desktop-service-${var.environment}"
  }
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_vpc" "main" {
  id = var.vpc_id
}