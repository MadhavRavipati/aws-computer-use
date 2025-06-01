# ABOUTME: Networking module for VPC, subnets, and network resources
# ABOUTME: Supports both creating new VPC and using existing VPC

locals {
  vpc_id = var.use_existing_vpc ? var.existing_vpc_id : aws_vpc.new[0].id
  
  # Create subnets only if creating new VPC
  create_subnets = !var.use_existing_vpc
  
  # Get existing subnets if using existing VPC
  existing_private_subnets = var.use_existing_vpc ? data.aws_subnets.private[0].ids : []
  existing_public_subnets  = var.use_existing_vpc ? data.aws_subnets.public[0].ids : []
  
  # Final subnet IDs
  private_subnet_ids = var.use_existing_vpc ? local.existing_private_subnets : aws_subnet.private[*].id
  public_subnet_ids  = var.use_existing_vpc ? local.existing_public_subnets : aws_subnet.public[*].id
}

# Create new VPC if not using existing
resource "aws_vpc" "new" {
  count = var.use_existing_vpc ? 0 : 1
  
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "computer-use-vpc-${var.environment}"
  }
}

# Get existing subnets if using existing VPC
data "aws_subnets" "private" {
  count = var.use_existing_vpc ? 1 : 0
  
  filter {
    name   = "vpc-id"
    values = [var.existing_vpc_id]
  }
  
  tags = {
    Type = "Private"
  }
}

data "aws_subnets" "public" {
  count = var.use_existing_vpc ? 1 : 0
  
  filter {
    name   = "vpc-id"
    values = [var.existing_vpc_id]
  }
  
  tags = {
    Type = "Public"
  }
}

# Create subnets if creating new VPC
resource "aws_subnet" "private" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  vpc_id            = local.vpc_id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]
  
  tags = {
    Name = "computer-use-private-${var.availability_zones[count.index]}-${var.environment}"
    Type = "Private"
  }
}

resource "aws_subnet" "public" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  vpc_id                  = local.vpc_id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 100)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "computer-use-public-${var.availability_zones[count.index]}-${var.environment}"
    Type = "Public"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = local.create_subnets ? 1 : 0
  
  vpc_id = local.vpc_id
  
  tags = {
    Name = "computer-use-igw-${var.environment}"
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  domain = "vpc"
  
  tags = {
    Name = "computer-use-nat-eip-${var.availability_zones[count.index]}-${var.environment}"
  }
  
  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = {
    Name = "computer-use-nat-${var.availability_zones[count.index]}-${var.environment}"
  }
  
  depends_on = [aws_internet_gateway.main]
}

# Route tables
resource "aws_route_table" "public" {
  count = local.create_subnets ? 1 : 0
  
  vpc_id = local.vpc_id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }
  
  tags = {
    Name = "computer-use-public-rt-${var.environment}"
  }
}

resource "aws_route_table" "private" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  vpc_id = local.vpc_id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }
  
  tags = {
    Name = "computer-use-private-rt-${var.availability_zones[count.index]}-${var.environment}"
  }
}

# Route table associations
resource "aws_route_table_association" "public" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "private" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# VPC Endpoints
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = local.vpc_id
  service_name = "com.amazonaws.${data.aws_region.current.name}.s3"
  
  tags = {
    Name = "computer-use-s3-endpoint-${var.environment}"
  }
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id       = local.vpc_id
  service_name = "com.amazonaws.${data.aws_region.current.name}.dynamodb"
  
  tags = {
    Name = "computer-use-dynamodb-endpoint-${var.environment}"
  }
}

# Associate VPC endpoints with route tables
resource "aws_vpc_endpoint_route_table_association" "s3_private" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
  route_table_id  = aws_route_table.private[count.index].id
}

resource "aws_vpc_endpoint_route_table_association" "dynamodb_private" {
  count = local.create_subnets ? length(var.availability_zones) : 0
  
  vpc_endpoint_id = aws_vpc_endpoint.dynamodb.id
  route_table_id  = aws_route_table.private[count.index].id
}

# Interface endpoints for other services
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.private_subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
  
  tags = {
    Name = "computer-use-ecr-api-endpoint-${var.environment}"
  }
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.private_subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
  
  tags = {
    Name = "computer-use-ecr-dkr-endpoint-${var.environment}"
  }
}

resource "aws_vpc_endpoint" "secrets_manager" {
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.private_subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
  
  tags = {
    Name = "computer-use-secrets-endpoint-${var.environment}"
  }
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  name        = "computer-use-vpc-endpoints-${var.environment}"
  description = "Security group for VPC endpoints"
  vpc_id      = local.vpc_id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.use_existing_vpc ? "10.0.0.0/8" : var.vpc_cidr]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "computer-use-vpc-endpoints-${var.environment}"
  }
}

# Data sources
data "aws_region" "current" {}