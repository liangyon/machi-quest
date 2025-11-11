

//telling rds which subnets it can use
resource "aws_db_subnet_group" "main" {
  name = "${var.environment}-${var.project_name}-db-subnet-group"
  subnet_ids = [
    aws_subnet.database_1.id,
    aws_subnet.database_2.id
  ]
  tags = merge(
    var.tags,
    {
      "Name" = "${var.environment}-${var.project_name}-db-subnet-group"
    }
  )
}

//let terraform generate a strong password
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>?/" //should exclude characters that cause problems
}

//rds parameter group if you want to customize parameters
resource "aws_db_parameter_group" "postgres" {
  name   = "${var.environment}-${var.project_name}-postgres-params"
  family = "postgres16"

  parameter {
    name  = "max_connections"
    value = "200"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = var.tags
}


// now for the ACTUAL rds instance
resource "aws_db_instance" "postgres" {
  identifier = "${var.environment}-${var.project_name}-postgres"

  #engine config
  engine            = "postgres"
  engine_version    = "16.4"
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  #db config
  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  #network config
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  multi_az = false //should be true for prod

  #backups 
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  #performance and monitoring
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  # parameters
  parameter_group_name = aws_db_parameter_group.postgres.name

  deletion_protection       = true //should be false for dev
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.environment}-${var.project_name}-final-snapshot"

  auto_minor_version_upgrade = true

  tags = merge(
    var.tags,
    {
      "Name" = "${var.environment}-${var.project_name}-postgres"
    }
  )


}


resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.environment}/${var.project_name}/db/password"
  description = "PostgreSQL database password"

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}


# postgresql://username:password@host:5432/database

# # Real example:
# postgresql://machiquest_admin:[PASSWORD]@production-machi-quest-postgres.abc123.us-east-1.rds.amazonaws.com:5432/machiquest
