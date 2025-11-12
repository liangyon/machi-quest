

//target groups

resource "aws_alb_target_group" "backend" {
  name        = "${var.environment}-${var.project_name}-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip" //fargate required


  #health checks -alb pings this to see if ocntainer is ok
  health_check {
    enabled             = true
    healthy_threshold   = 2 // need 2 successful checks to be healthy
    unhealthy_threshold = 3 // 3 to die
    timeout             = 5 //5 seconds
    interval            = 30
    path                = "/health"
    matcher             = "200" //expect 200 ok
  }

  deregistration_delay = 30
  tags                 = var.tags

}

resource "aws_alb_target_group" "frontend" {
  name        = "${var.environment}-${var.project_name}-frontend-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip" //fargate required


  #health checks -alb pings this to see if ocntainer is ok
  health_check {
    enabled             = true
    healthy_threshold   = 2 // need 2 successful checks to be healthy
    unhealthy_threshold = 3 // 3 to die
    timeout             = 5 //5 seconds
    interval            = 30
    path                = "/"
    matcher             = "200" //expect 200 ok
  }

  deregistration_delay = 30
  tags                 = var.tags

}


// actual load balancer

resource "aws_lb" "main" {
  name               = "${var.environment}-${var.project_name}-alb"
  internal           = false #false = internet facing, vice versa
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]

  //must span two subnets in different zones
  subnets = [
    aws_subnet.public_1.id,
    aws_subnet.public_2.id
  ]

  enable_deletion_protection = false //set this to true for prod

  # Access logs (optional - adds cost) costs money
  # access_logs {
  #   bucket  = aws_s3_bucket.alb_logs.id
  #   enabled = true
  # }

  tags = var.tags
}

# HTTP Listener (Port 80) - will redirect to HTTPS later
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # Default action - forward to frontend
  default_action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.frontend.arn
  }
}

# HTTP Listener Rule - Route /api/* to backend
resource "aws_lb_listener_rule" "backend_routing" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100 # Lower number = higher priority

  condition {
    path_pattern {
      values = ["/api/*", "/docs*", "/health"] # These paths go to backend
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.backend.arn
  }
}
