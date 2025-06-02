# ABOUTME: Output values for CloudFront distribution module
# ABOUTME: Exports distribution URL and configuration details

output "distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.id
}

output "distribution_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "distribution_url" {
  description = "Full URL of the CloudFront distribution"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "origin_access_control_id" {
  description = "ID of the Origin Access Control"
  value       = aws_cloudfront_origin_access_control.main.id
}