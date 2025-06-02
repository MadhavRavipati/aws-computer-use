# ABOUTME: Output values for ECS module
# ABOUTME: Exposes cluster, service, and repository information

output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "desktop_repository_url" {
  description = "URL of the desktop ECR repository"
  value       = aws_ecr_repository.desktop.repository_url
}

output "vnc_bridge_repository_url" {
  description = "URL of the VNC bridge ECR repository"
  value       = aws_ecr_repository.vnc_bridge.repository_url
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "desktop_target_group_arn" {
  description = "ARN of the desktop target group"
  value       = aws_lb_target_group.desktop.arn
}

output "security_groups" {
  description = "Security group IDs"
  value = {
    alb     = aws_security_group.alb.id
    desktop = aws_security_group.desktop.id
  }
}

output "service_discovery" {
  description = "Service discovery details"
  value = {
    namespace_id   = aws_service_discovery_private_dns_namespace.main.id
    namespace_name = aws_service_discovery_private_dns_namespace.main.name
    service_arn    = aws_service_discovery_service.desktop.arn
  }
}

output "iam_roles" {
  description = "IAM role ARNs"
  value = {
    execution_role_arn = aws_iam_role.ecs_execution.arn
    task_role_arn      = aws_iam_role.ecs_task.arn
  }
}

output "task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

output "execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = aws_iam_role.ecs_execution.arn
}

output "log_groups" {
  description = "CloudWatch log group names"
  value = {
    desktop    = aws_cloudwatch_log_group.desktop.name
    vnc_bridge = aws_cloudwatch_log_group.vnc_bridge.name
    ecs_exec   = aws_cloudwatch_log_group.ecs_exec.name
  }
}