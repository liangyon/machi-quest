
# General variables
variable "project_name" {
  description = "name of project, prefixes all resources"
  type        = string
  default     = "machi-quest"
}
variable "environment" {
  description = "environment name (dev, staging, production)"
  type        = string
  default     = "production"
}



# AWS variables
variable "aws_region" {
  description = "aws_region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC (your network address space)"
  type        = string
  default     = "10.0.0.0/16" # Gives you 65,536 IP addresses
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}


# Database variables
variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t4g.micro" # Cheapest, ARM-based
}

variable "db_allocated_storage" {
  description = "Database storage in GB"
  type        = number
  default     = 20 # 20GB is minimum
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "machiquest"
}

variable "db_username" {
  description = "Master username for database"
  type        = string
  default     = "machiquest_admin"
}


# Redis 
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro" # Cheapest option
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1 # Single node for cost savings
}


#ECS config
variable "app_count" {
  description = "Number of container instances to run"
  type        = number
  default     = 1 # Start with 1, scale up later
}
#at 3 containers, its about 22 USD/month
variable "fargate_cpu" {
  description = "Fargate CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 256 # 0.25 vCPU - cheapest option
}

variable "fargate_memory" {
  description = "Fargate memory in MB"
  type        = number
  default     = 512 # 512MB RAM - minimum for 256 CPU
}


variable "domain_name" {
  description = "value"
  type        = string
  default     = "machi.quest"
}



variable "tags" {
  description = "common tags"
  type        = map(string)
  default = {
    Owner       = "Machi Quest"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Project     = "Machi Quest"
  }
}