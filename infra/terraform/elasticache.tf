

# amazon's redis managed service

resource "aws_elasticache_subnet_group" "main" {
  name = "${var.environment}-${var.project_name}-redis-subnet-group"
  subnet_ids = [
    aws_subnet.database_1.id,
    aws_subnet.database_2.id,
  ]
  tags = merge(
    var.tags,
    {
      "Name" = "${var.environment}-${var.project_name}-redis-subnet-group"
    }
  )
}

//let terraform generate a strong password
resource "random_password" "redis_token" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>?/" //should exclude characters that cause problems
}

//optional parameters
resource "aws_elasticache_parameter_group" "redis" {
  name   = "${var.environment}-${var.project_name}-redis-params"
  family = "redis7" # Redis 8.x uses redis7 parameter family

  # Timeout for idle connections (seconds)
  parameter {
    name  = "timeout"
    value = "300" # 5 minutes
  }

  # Max memory policy - evict least recently used keys when memory full
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = var.tags
}


// replication group, (the actual redis cluster/instance)
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "${var.environment}-${var.project_name}-redis"
  description          = "Redis cluster for Machi Quest"

  # Engine configuration
  engine               = "redis"
  engine_version       = "8.2" # Latest Redis version (Nov 2025)
  node_type            = var.redis_node_type
  num_cache_clusters   = var.redis_num_cache_nodes # Use num_cache_clusters, not num_node_groups
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  port                 = 6379

  # Network configuration
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  # Security - AUTH token
  auth_token                 = random_password.redis_token.result
  transit_encryption_enabled = true # Required for AUTH token
  at_rest_encryption_enabled = true # Encrypt data on disk

  # High availability
  automatic_failover_enabled = false # Set to true for multi-node (costs 2x)
  multi_az_enabled           = false # Set to true with automatic_failover for HA

  # Maintenance and backups
  maintenance_window       = "sun:05:00-sun:06:00"
  snapshot_window          = "03:00-04:00"
  snapshot_retention_limit = 5 # Keep 5 days of backups

  # Auto minor version upgrades
  auto_minor_version_upgrade = true

  tags = merge(
    var.tags,
    {
      "Name" = "${var.environment}-${var.project_name}-redis"
    }
  )
}


resource "aws_secretsmanager_secret" "redis_token" {
  name        = "${var.environment}/${var.project_name}/redis/token"
  description = "redis auth token"

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "redis_token" {
  secret_id     = aws_secretsmanager_secret.redis_token.id
  secret_string = random_password.redis_token.result
}
