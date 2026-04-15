output "alb_dns_name" {
  value       = aws_lb.api.dns_name
  description = "Public ALB DNS name."
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "ECS cluster name."
}

output "ecs_service_name" {
  value       = aws_ecs_service.api.name
  description = "ECS service name."
}

output "db_endpoint" {
  value       = aws_db_instance.postgres.address
  description = "RDS endpoint hostname."
}

output "uploads_bucket_name" {
  value       = aws_s3_bucket.uploads.bucket
  description = "Upload bucket name."
}

output "alerts_topic_arn" {
  value       = aws_sns_topic.alerts.arn
  description = "SNS topic ARN for operations alerts."
}

output "cloudwatch_dashboard_name" {
  value       = aws_cloudwatch_dashboard.operations.dashboard_name
  description = "CloudWatch dashboard name."
}
