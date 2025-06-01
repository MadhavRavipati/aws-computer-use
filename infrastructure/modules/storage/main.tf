# ABOUTME: Storage module for S3 buckets and DynamoDB tables
# ABOUTME: Manages data persistence for sessions and assets

# S3 bucket for assets
resource "aws_s3_bucket" "assets" {
  bucket = "computer-use-assets-${var.environment}-${var.account_id}"
  
  tags = {
    Name = "computer-use-assets-${var.environment}"
  }
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id
  
  rule {
    id     = "delete-old-screenshots"
    status = "Enabled"
    
    filter {
      prefix = "screenshots/"
    }
    
    expiration {
      days = 7
    }
  }
  
  rule {
    id     = "archive-recordings"
    status = "Enabled"
    
    filter {
      prefix = "recordings/"
    }
    
    transition {
      days          = 30
      storage_class = "GLACIER_IR"
    }
    
    expiration {
      days = 90
    }
  }
}

# S3 bucket CORS configuration
resource "aws_s3_bucket_cors_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["*"] # Will be restricted in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# DynamoDB table for sessions
resource "aws_dynamodb_table" "sessions" {
  name           = "computer-use-sessions-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "session_id"
  
  attribute {
    name = "session_id"
    type = "S"
  }
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "created_at"
    type = "N"
  }
  
  global_secondary_index {
    name            = "user-index"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }
  
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  point_in_time_recovery {
    enabled = var.enable_backups
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = {
    Name = "computer-use-sessions-${var.environment}"
  }
}

# DynamoDB table for agent memory/cache
resource "aws_dynamodb_table" "agent_cache" {
  name           = "computer-use-agent-cache-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "cache_key"
  
  attribute {
    name = "cache_key"
    type = "S"
  }
  
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = {
    Name = "computer-use-agent-cache-${var.environment}"
  }
}

# Secrets Manager for VNC passwords
resource "aws_secretsmanager_secret" "vnc_password" {
  name_prefix             = "computer-use/vnc-password-${var.environment}-"
  description             = "VNC password for desktop containers"
  recovery_window_in_days = 7
  
  tags = {
    Name = "computer-use-vnc-password-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "vnc_password" {
  secret_id = aws_secretsmanager_secret.vnc_password.id
  secret_string = jsonencode({
    password = random_password.vnc.result
  })
}

resource "random_password" "vnc" {
  length  = 16
  special = true
}

# S3 bucket for frontend static assets
resource "aws_s3_bucket" "frontend" {
  bucket = "computer-use-frontend-${var.environment}-${var.account_id}"
  
  tags = {
    Name = "computer-use-frontend-${var.environment}"
  }
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  
  index_document {
    suffix = "index.html"
  }
  
  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# S3 bucket policy for CloudFront
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = var.account_id
          }
        }
      }
    ]
  })
}