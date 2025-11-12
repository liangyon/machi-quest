


output "vpc_id" {
  description = "vpc id"
  value       = aws_vpc.main.id
}

output "rds_endpoint" {
  description = "rds endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_database_name" {
  description = "sensitive rds database name"
  value       = aws_db_instance.postgres.db_name
}

output "redis_endpoint" {
  description = "redis cluster endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}


#ecr urls 
output "ecr_repository_frontend" {
  description = "ECR repository URL for frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_repository_backend" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_repository_worker" {
  description = "ECR repository URL for worker"
  value       = aws_ecr_repository.worker.repository_url
}


#alb dns outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}