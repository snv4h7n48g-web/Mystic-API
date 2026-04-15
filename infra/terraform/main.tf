locals {
  name_prefix = "${var.app_name}-${var.environment}"

  common_tags = {
    Application = var.app_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  container_environment = [
    { name = "APP_ENV", value = var.environment },
    { name = "AWS_REGION", value = var.aws_region },
    { name = "DB_HOST", value = aws_db_instance.postgres.address },
    { name = "DB_PORT", value = tostring(aws_db_instance.postgres.port) },
    { name = "DB_NAME", value = var.db_name },
    { name = "DB_USER", value = var.db_username },
    { name = "CORS_ALLOWED_ORIGINS", value = var.cors_allowed_origins },
    { name = "S3_BUCKET_NAME", value = aws_s3_bucket.uploads.bucket },
    { name = "BEDROCK_PREVIEW_MODEL", value = var.bedrock_preview_model },
    { name = "BEDROCK_FULL_MODEL", value = var.bedrock_full_model },
    { name = "MYSTIC_USE_PERSONA_ORCHESTRATION", value = "true" },
    { name = "ALLOW_DEV_PURCHASE_BYPASS", value = "false" },
    { name = "GOOGLE_PLAY_PACKAGE_NAME", value = var.google_play_package_name }
  ]

  container_secrets = concat(
    [
      { name = "DB_PASSWORD", valueFrom = var.db_password_secret_arn },
      { name = "JWT_SECRET_KEY", valueFrom = var.jwt_secret_arn },
      { name = "GOOGLE_SERVICE_ACCOUNT_JSON", valueFrom = var.google_service_account_json_secret_arn }
    ],
    var.apple_shared_secret_arn != "" ? [
      { name = "APPLE_SHARED_SECRET", valueFrom = var.apple_shared_secret_arn }
    ] : []
  )

  db_password_value = try(
    jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string).password,
    data.aws_secretsmanager_secret_version.db_password.secret_string
  )

  alarm_actions = length(var.alarm_email_endpoints) > 0 ? [aws_sns_topic.alerts.arn] : []
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = var.db_password_secret_arn
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw"
  })
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-${count.index + 1}"
  })
}

resource "aws_subnet" "private_app" {
  count             = length(var.private_app_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_app_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-app-${count.index + 1}"
  })
}

resource "aws_subnet" "private_db" {
  count             = length(var.private_db_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_db_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-db-${count.index + 1}"
  })
}

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-eip"
  })
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-rt"
  })
}

resource "aws_route_table_association" "private_app" {
  count          = length(aws_subnet.private_app)
  subnet_id      = aws_subnet.private_app[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_db" {
  count          = length(aws_subnet.private_db)
  subnet_id      = aws_subnet.private_db[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Public ALB access"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_security_group" "ecs_service" {
  name        = "${local.name_prefix}-ecs-sg"
  description = "API tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = var.api_container_port
    to_port         = var.api_container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_security_group" "db" {
  name        = "${local.name_prefix}-db-sg"
  description = "PostgreSQL access from ECS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_service.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"

  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "alert_email" {
  count     = length(var.alarm_email_endpoints)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email_endpoints[count.index]
}

resource "aws_s3_bucket" "uploads" {
  bucket = var.s3_bucket_name

  tags = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    id     = "expire-old-uploads"
    status = "Enabled"

    filter {}

    expiration {
      days = 30
    }
  }
}

resource "aws_db_subnet_group" "postgres" {
  name       = "${local.name_prefix}-db-subnets"
  subnet_ids = aws_subnet.private_db[*].id

  tags = local.common_tags
}

resource "aws_db_instance" "postgres" {
  identifier                  = "${local.name_prefix}-postgres"
  engine                      = "postgres"
  engine_version              = "16.4"
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  db_name                     = var.db_name
  username                    = var.db_username
  password                    = local.db_password_value
  manage_master_user_password = false
  skip_final_snapshot         = true
  deletion_protection         = var.environment == "production"
  multi_az                    = var.db_multi_az
  publicly_accessible         = false
  db_subnet_group_name        = aws_db_subnet_group.postgres.name
  vpc_security_group_ids      = [aws_security_group.db.id]

  lifecycle {
    ignore_changes = [password]
  }

  tags = local.common_tags
}

resource "aws_lb" "api" {
  name               = substr(replace("${local.name_prefix}-alb", "_", "-"), 0, 32)
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = local.common_tags
}

resource "aws_lb_target_group" "api" {
  name        = substr(replace("${local.name_prefix}-tg", "_", "-"), 0, 32)
  port        = var.api_container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    enabled             = true
    path                = "/health/ready"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
    timeout             = 5
  }

  tags = local.common_tags
}

resource "aws_lb_listener" "api_http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${local.name_prefix}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_managed" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_task_execution_secrets" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
      "kms:Decrypt"
    ]
    resources = compact([
      var.db_password_secret_arn,
      var.jwt_secret_arn,
      var.google_service_account_json_secret_arn,
      var.apple_shared_secret_arn != "" ? var.apple_shared_secret_arn : null,
    ])
  }
}

resource "aws_iam_policy" "ecs_task_execution_secrets" {
  name   = "${local.name_prefix}-ecs-secrets"
  policy = data.aws_iam_policy_document.ecs_task_execution_secrets.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_secrets" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.ecs_task_execution_secrets.arn
}

resource "aws_iam_role" "ecs_task" {
  name               = "${local.name_prefix}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json

  tags = local.common_tags
}

data "aws_iam_policy_document" "ecs_task_runtime" {
  statement {
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = ["${aws_s3_bucket.uploads.arn}/*"]
  }

  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.uploads.arn]
  }
}

resource "aws_iam_policy" "ecs_task_runtime" {
  name   = "${local.name_prefix}-ecs-runtime"
  policy = data.aws_iam_policy_document.ecs_task_runtime.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_runtime" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_task_runtime.arn
}

resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.container_image
      essential = true
      portMappings = [
        {
          containerPort = var.api_container_port
          hostPort      = var.api_container_port
          protocol      = "tcp"
        }
      ]
      environment = local.container_environment
      secrets     = local.container_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    assign_public_ip = false
    subnets          = aws_subnet.private_app[*].id
    security_groups  = [aws_security_group.ecs_service.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.api_container_port
  }

  depends_on = [aws_lb_listener.api_http]

  tags = local.common_tags
}

resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = var.ecs_max_capacity
  min_capacity       = var.ecs_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu_target" {
  name               = "${local.name_prefix}-cpu-target"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    target_value       = 60
    scale_in_cooldown  = 60
    scale_out_cooldown = 60
  }
}

resource "aws_cloudwatch_log_metric_filter" "purchase_verification_failed" {
  name           = "${local.name_prefix}-purchase-verification-failed"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "{ $.event = \"purchase_verification_failed\" || $.event = \"purchase_verification_runtime_error\" || $.event = \"purchase_verification_not_implemented\" }"

  metric_transformation {
    name      = "${replace(local.name_prefix, "-", "_")}_purchase_verification_failures"
    namespace = "Mystic/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "bedrock_generation_failed" {
  name           = "${local.name_prefix}-bedrock-generation-failed"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "{ $.event = \"bedrock_generation_failed\" }"

  metric_transformation {
    name      = "${replace(local.name_prefix, "-", "_")}_bedrock_generation_failures"
    namespace = "Mystic/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "llm_call_completed" {
  name           = "${local.name_prefix}-llm-call-completed"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "{ $.event = \"llm_call_completed\" }"

  metric_transformation {
    name      = "${replace(local.name_prefix, "-", "_")}_llm_call_completed"
    namespace = "Mystic/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "llm_cost_usd" {
  name           = "${local.name_prefix}-llm-cost-usd"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "{ $.event = \"llm_call_completed\" }"

  metric_transformation {
    name      = "${replace(local.name_prefix, "-", "_")}_llm_cost_usd"
    namespace = "Mystic/Application"
    value     = "$.cost_usd"
  }
}

resource "aws_cloudwatch_log_metric_filter" "llm_input_tokens" {
  name           = "${local.name_prefix}-llm-input-tokens"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "{ $.event = \"llm_call_completed\" }"

  metric_transformation {
    name      = "${replace(local.name_prefix, "-", "_")}_llm_input_tokens"
    namespace = "Mystic/Application"
    value     = "$.input_tokens"
  }
}

resource "aws_cloudwatch_log_metric_filter" "llm_output_tokens" {
  name           = "${local.name_prefix}-llm-output-tokens"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "{ $.event = \"llm_call_completed\" }"

  metric_transformation {
    name      = "${replace(local.name_prefix, "-", "_")}_llm_output_tokens"
    namespace = "Mystic/Application"
    value     = "$.output_tokens"
  }
}

resource "aws_cloudwatch_log_metric_filter" "app_error_logs" {
  name           = "${local.name_prefix}-app-error-logs"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "{ $.level = \"ERROR\" }"

  metric_transformation {
    name      = "${replace(local.name_prefix, "-", "_")}_app_error_logs"
    namespace = "Mystic/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_target_5xx" {
  alarm_name          = "${local.name_prefix}-alb-target-5xx"
  alarm_description   = "ALB target 5xx responses are above the acceptable threshold."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = var.alb_5xx_alarm_threshold
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  alarm_actions       = local.alarm_actions

  dimensions = {
    LoadBalancer = aws_lb.api.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_target_response_time" {
  alarm_name          = "${local.name_prefix}-alb-response-time"
  alarm_description   = "ALB target response time is above the acceptable threshold."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = var.alb_response_time_alarm_threshold
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  statistic           = "Average"
  period              = 300
  alarm_actions       = local.alarm_actions

  dimensions = {
    LoadBalancer = aws_lb.api.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  alarm_name          = "${local.name_prefix}-alb-unhealthy-hosts"
  alarm_description   = "ALB has unhealthy API targets."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 0
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  alarm_actions       = local.alarm_actions

  dimensions = {
    LoadBalancer = aws_lb.api.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  alarm_name          = "${local.name_prefix}-ecs-cpu-high"
  alarm_description   = "ECS service CPU utilization is high."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = var.ecs_cpu_alarm_threshold
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  alarm_actions       = local.alarm_actions

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api.name
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory_high" {
  alarm_name          = "${local.name_prefix}-ecs-memory-high"
  alarm_description   = "ECS service memory utilization is high."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = var.ecs_memory_alarm_threshold
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/ECS"
  metric_name         = "MemoryUtilization"
  statistic           = "Average"
  period              = 300
  alarm_actions       = local.alarm_actions

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api.name
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  alarm_description   = "RDS CPU utilization is high."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = var.rds_cpu_alarm_threshold
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  alarm_actions       = local.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  alarm_name          = "${local.name_prefix}-rds-connections-high"
  alarm_description   = "RDS active connections are high."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = var.rds_connections_alarm_threshold
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/RDS"
  metric_name         = "DatabaseConnections"
  statistic           = "Average"
  period              = 300
  alarm_actions       = local.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_free_storage_low" {
  alarm_name          = "${local.name_prefix}-rds-free-storage-low"
  alarm_description   = "RDS free storage is low."
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  threshold           = var.rds_free_storage_alarm_threshold_bytes
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Average"
  period              = 300
  alarm_actions       = local.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "purchase_verification_failures" {
  alarm_name          = "${local.name_prefix}-purchase-verification-failures"
  alarm_description   = "Purchase verification failures detected in application logs."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1
  treat_missing_data  = "notBreaching"
  namespace           = "Mystic/Application"
  metric_name         = aws_cloudwatch_log_metric_filter.purchase_verification_failed.metric_transformation[0].name
  statistic           = "Sum"
  period              = 300
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "bedrock_generation_failures" {
  alarm_name          = "${local.name_prefix}-bedrock-generation-failures"
  alarm_description   = "Bedrock generation failures detected in application logs."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1
  treat_missing_data  = "notBreaching"
  namespace           = "Mystic/Application"
  metric_name         = aws_cloudwatch_log_metric_filter.bedrock_generation_failed.metric_transformation[0].name
  statistic           = "Sum"
  period              = 300
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "llm_cost_high" {
  alarm_name          = "${local.name_prefix}-llm-cost-high"
  alarm_description   = "Hourly LLM cost is above the configured threshold."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = var.llm_cost_alarm_threshold_usd
  treat_missing_data  = "notBreaching"
  namespace           = "Mystic/Application"
  metric_name         = aws_cloudwatch_log_metric_filter.llm_cost_usd.metric_transformation[0].name
  statistic           = "Sum"
  period              = 3600
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "app_error_logs" {
  alarm_name          = "${local.name_prefix}-app-error-logs"
  alarm_description   = "Structured application error logs detected."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 5
  treat_missing_data  = "notBreaching"
  namespace           = "Mystic/Application"
  metric_name         = aws_cloudwatch_log_metric_filter.app_error_logs.metric_transformation[0].name
  statistic           = "Sum"
  period              = 300
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_dashboard" "operations" {
  dashboard_name = "${local.name_prefix}-operations"
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "ALB Health"
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.api.arn_suffix, "TargetGroup", aws_lb_target_group.api.arn_suffix],
            [".", "TargetResponseTime", ".", ".", ".", "."],
            [".", "UnHealthyHostCount", ".", ".", ".", "."]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "ECS Service"
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.api.name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "RDS PostgreSQL"
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.postgres.identifier],
            [".", "DatabaseConnections", ".", "."],
            [".", "FreeStorageSpace", ".", "."]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Application Errors"
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          metrics = [
            ["Mystic/Application", aws_cloudwatch_log_metric_filter.purchase_verification_failed.metric_transformation[0].name],
            [".", aws_cloudwatch_log_metric_filter.bedrock_generation_failed.metric_transformation[0].name],
            [".", aws_cloudwatch_log_metric_filter.app_error_logs.metric_transformation[0].name]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "LLM Spend"
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          metrics = [
            ["Mystic/Application", aws_cloudwatch_log_metric_filter.llm_cost_usd.metric_transformation[0].name],
            [".", aws_cloudwatch_log_metric_filter.llm_call_completed.metric_transformation[0].name]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "LLM Tokens"
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          metrics = [
            ["Mystic/Application", aws_cloudwatch_log_metric_filter.llm_input_tokens.metric_transformation[0].name],
            [".", aws_cloudwatch_log_metric_filter.llm_output_tokens.metric_transformation[0].name]
          ]
        }
      }
    ]
  })
}
