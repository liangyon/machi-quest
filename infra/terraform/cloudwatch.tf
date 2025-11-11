


resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.environment}-${var.project_name}-frontend"
  retention_in_days = 3
  tags = merge(
    var.tags,
    {
      name        = "${var.environment}-${var.project_name}-frontend-logs"
      ServiceType = "Frontend"
    }
  )
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.environment}-${var.project_name}-backend"
  retention_in_days = 3
  tags = merge(
    var.tags,
    {
      name        = "${var.environment}-${var.project_name}-backend-logs"
      ServiceType = "Backend"
    }
  )
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.environment}-${var.project_name}-worker"
  retention_in_days = 3
  tags = merge(
    var.tags,
    {
      name        = "${var.environment}-${var.project_name}-worker-logs"
      ServiceType = "Worker"
    }
  )
}