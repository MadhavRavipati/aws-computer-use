# ABOUTME: Output values for networking module
# ABOUTME: Exposes VPC and subnet identifiers

output "vpc_id" {
  description = "ID of the VPC"
  value       = local.vpc_id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = local.private_subnet_ids
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = local.public_subnet_ids
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = var.use_existing_vpc ? data.aws_vpc.existing[0].cidr_block : aws_vpc.new[0].cidr_block
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = var.use_existing_vpc ? [] : aws_nat_gateway.main[*].id
}

output "vpc_endpoints" {
  description = "VPC endpoint IDs"
  value = {
    s3              = aws_vpc_endpoint.s3.id
    dynamodb        = aws_vpc_endpoint.dynamodb.id
    ecr_api         = aws_vpc_endpoint.ecr_api.id
    ecr_dkr         = aws_vpc_endpoint.ecr_dkr.id
    secrets_manager = aws_vpc_endpoint.secrets_manager.id
  }
}

# Data source for existing VPC
data "aws_vpc" "existing" {
  count = var.use_existing_vpc ? 1 : 0
  id    = var.existing_vpc_id
}