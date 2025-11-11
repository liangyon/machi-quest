
resource "aws_ecr_repository" "frontend" {
  name = "${var.environment}-${var.project_name}-frontend"

  # Image tag mutability - can you overwrite tags?
  # MUTABLE = can push same tag again (e.g., "latest" can be updated)
  # IMMUTABLE = once a tag exists, it's permanent (safer for production)
  image_tag_mutability = "MUTABLE"

  # Image scanning - automatically scan for security vulnerabilities
  image_scanning_configuration {
    scan_on_push = true # Scan every time you push an image
  }

  # Encryption at rest (security best practice)
  encryption_configuration {
    encryption_type = "AES256" # AWS managed encryption (free)
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-${var.project_name}-frontend"
      ImageType   = "Frontend"
      Application = "Next.js"
    }
  )
}

# Lifecycle policy for frontend - auto-delete old images to save money
resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name

  # Keep last 10 images, delete older ones
  # ECR charges $0.10/GB/month, so this saves storage costs
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}


# Backend Repository - for FastAPI images
resource "aws_ecr_repository" "backend" {
  name                 = "${var.environment}-${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-${var.project_name}-backend"
      ImageType   = "Backend"
      Application = "FastAPI"
    }
  )
}

# Lifecycle policy for backend
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}


# Worker Repository - for background job worker images
resource "aws_ecr_repository" "worker" {
  name                 = "${var.environment}-${var.project_name}-worker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-${var.project_name}-worker"
      ImageType   = "Worker"
      Application = "Python Worker"
    }
  )
}

# Lifecycle policy for worker
resource "aws_ecr_lifecycle_policy" "worker" {
  repository = aws_ecr_repository.worker.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

//with lifestyle policies, we can save up to 45 dollars a month, otherwise we might accumulate hundreds of images and pay a lot
# How to use these repositories:
# 
# 1. Build your Docker image locally:
#    docker build -t machi-quest-frontend ./frontend
#
# 2. Tag it for ECR:
#    docker tag machi-quest-frontend:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/production-machi-quest-frontend:latest
#
# 3. Authenticate Docker to ECR:
#    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
#
# 4. Push to ECR:
#    docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/production-machi-quest-frontend:latest
#
# 5. ECS will pull from these URLs when deploying your containers!
