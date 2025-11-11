
//ingres is inbound rules 
//egress is outbound (where this resource can connect to)
// 433 is https, and we'll redirect 80 to 433
//protocol -1 means all protocols

//application load balancer
resource "aws_security_group" "alb" {
  name        = "${var.environment}-${var.project_name}-alb-sg"
  description = "security group for application load balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "allow HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "allow HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-alb-sg"
    }
  )
}

//ecs tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.environment}-${var.project_name}-ecs-tasks-sg"
  description = "security group for ecs tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "alb to backend"
    from_port       = 8000 //my fastapi is 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id] //only alb can connect, not the whole internet
  }

  ingress {
    description     = "alb to frontend"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  //containers have to call api and download packages
  egress {
    description = "allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]

  }
  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-ecs-tasks-sg"
    }
  )
}

//rds database
resource "aws_security_group" "rds" {
  name        = "${var.environment}-${var.project_name}-rds-sg"
  description = "security group for rds"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "allow postgres from ecs tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    description = "allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-rds-sg"
    }
  )
}

//redis
resource "aws_security_group" "redis" {
  name        = "${var.environment}-${var.project_name}-redis-sg"
  description = "security group for redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "allow redis from ecs tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    description = "allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-redis-sg"
    }
  )
}

//to help me understand later
# allowed
# User → ALB (port 443) 
# ALB → ECS Backend (port 8000) 
# ALB → ECS Frontend (port 3000) 
# ECS → RDS (port 5432) 
# ECS → Redis (port 6379) 
# ECS → Internet (for APIs, updates) 
# 

# blocked
# User → ECS directly  (must go through ALB)
# User → RDS directly  (must go through ECS)
# Internet → RDS  (no route, security group blocks)
# ALB → RDS directly  (security group blocks)
