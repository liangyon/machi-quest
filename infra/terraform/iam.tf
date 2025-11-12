
//iam task execution roles
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.environment}-${var.project_name}-ecs-task-execution-role"

  //trust policy - who can use this role; we want ecs tasks to use this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole" //allows sts to assume this role
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com" //the ecs service itself
        }

      }
    ]
  })

  tags = var.tags
}


// this is a policy attachment that is a default, gives permissions to pull ecr images and write
//cloudwatch logs
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
//policy_arn  = amazon resource name (unique identifier for amazon resources)
//aws:policy = aws-managed so we don't have to write the policy
//role_policy_attachment = links a policy to role


//custom policy for secrets manager
resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "${var.environment}-${var.project_name}-ecs-secrets-policy"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.environment}/${var.project_name}/*"
        ]
      }
    ]
  })
}


//iam task role (used by application code, allows fastapi/nextjs to call aws services)
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.environment}-${var.project_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags

}
//it looks identical to the task exec role, but thats because our target audience is the same
//we want ecs tasks to be able to use these roles

//sample basic policy for task roles: allow cloudwatch metrics
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.environment}-${var.project_name}-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData" //enable cloudwatch
        ]
        Resource = "*"
      }
    ]
  })
}