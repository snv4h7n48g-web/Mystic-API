variable "app_name" {
  type        = string
  description = "Application name prefix."
  default     = "mystic-api"
}

variable "environment" {
  type        = string
  description = "Deployment environment, e.g. staging or production."
}

variable "aws_region" {
  type        = string
  description = "AWS region for deployment."
  default     = "us-east-1"
}

variable "container_image" {
  type        = string
  description = "Fully qualified container image URI, usually from ECR."
}

variable "api_container_port" {
  type        = number
  default     = 8000
  description = "Port exposed by the FastAPI container."
}

variable "desired_count" {
  type        = number
  default     = 1
  description = "Desired ECS service count."
}

variable "task_cpu" {
  type        = number
  default     = 512
  description = "Fargate task CPU units."
}

variable "task_memory" {
  type        = number
  default     = 1024
  description = "Fargate task memory in MiB."
}

variable "vpc_cidr" {
  type        = string
  default     = "10.40.0.0/16"
  description = "CIDR block for the application VPC."
}

variable "availability_zones" {
  type        = list(string)
  description = "Two availability zones for high-availability deployment."
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDRs for public subnets."
}

variable "private_app_subnet_cidrs" {
  type        = list(string)
  description = "CIDRs for private ECS app subnets."
}

variable "private_db_subnet_cidrs" {
  type        = list(string)
  description = "CIDRs for private RDS subnets."
}

variable "db_name" {
  type        = string
  default     = "mystic"
  description = "PostgreSQL database name."
}

variable "db_username" {
  type        = string
  default     = "mystic"
  description = "PostgreSQL username."
}

variable "db_password_secret_arn" {
  type        = string
  description = "Secrets Manager ARN containing the DB password value."
}

variable "jwt_secret_arn" {
  type        = string
  description = "Secrets Manager ARN containing JWT_SECRET_KEY."
}

variable "google_service_account_json_secret_arn" {
  type        = string
  description = "Secrets Manager ARN containing GOOGLE_SERVICE_ACCOUNT_JSON."
}

variable "apple_shared_secret_arn" {
  type        = string
  default     = ""
  description = "Optional Secrets Manager ARN containing APPLE_SHARED_SECRET."
}

variable "google_play_package_name" {
  type        = string
  default     = ""
  description = "Android package name used for Play Billing verification."
}

variable "cors_allowed_origins" {
  type        = string
  description = "Comma-separated browser origins allowed by the API."
}

variable "s3_bucket_name" {
  type        = string
  description = "S3 bucket name for uploads."
}

variable "bedrock_preview_model" {
  type        = string
  default     = "us.amazon.nova-lite-v1:0"
  description = "Preview model identifier."
}

variable "bedrock_full_model" {
  type        = string
  default     = "us.amazon.nova-pro-v1:0"
  description = "Full reading model identifier."
}

variable "db_instance_class" {
  type        = string
  default     = "db.t4g.micro"
  description = "RDS instance class."
}

variable "db_allocated_storage" {
  type        = number
  default     = 20
  description = "Allocated DB storage in GB."
}

variable "db_multi_az" {
  type        = bool
  default     = false
  description = "Enable Multi-AZ for the database."
}

variable "ecs_min_capacity" {
  type        = number
  default     = 1
  description = "Minimum ECS autoscaling capacity."
}

variable "ecs_max_capacity" {
  type        = number
  default     = 3
  description = "Maximum ECS autoscaling capacity."
}

variable "alarm_email_endpoints" {
  type        = list(string)
  default     = []
  description = "Email endpoints subscribed to monitoring alerts."
}

variable "alb_5xx_alarm_threshold" {
  type        = number
  default     = 5
  description = "Threshold for ALB target 5xx count alarm."
}

variable "alb_response_time_alarm_threshold" {
  type        = number
  default     = 2
  description = "Threshold in seconds for ALB target response time."
}

variable "ecs_cpu_alarm_threshold" {
  type        = number
  default     = 80
  description = "Threshold for ECS CPU utilization alarm."
}

variable "ecs_memory_alarm_threshold" {
  type        = number
  default     = 80
  description = "Threshold for ECS memory utilization alarm."
}

variable "rds_cpu_alarm_threshold" {
  type        = number
  default     = 80
  description = "Threshold for RDS CPU utilization alarm."
}

variable "rds_connections_alarm_threshold" {
  type        = number
  default     = 80
  description = "Threshold for RDS database connections alarm."
}

variable "rds_free_storage_alarm_threshold_bytes" {
  type        = number
  default     = 5368709120
  description = "Threshold in bytes for low RDS free storage."
}

variable "llm_cost_alarm_threshold_usd" {
  type        = number
  default     = 25
  description = "Threshold for hourly LLM cost alarm in USD."
}
