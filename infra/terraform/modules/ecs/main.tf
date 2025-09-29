provider "aws" {
  region = "us-east-1"
}


resource "aws_cloudwatch_log_group" "tasksmind_loggroup" {
  name = "tasksmind-loggroup-${var.environment_name}"
  tags = var.tags
}

# Create Target Group for Port 8000
resource "aws_lb_target_group" "tasksmind-targetgroup" {
  name        = "${var.project_name}-${var.environment_name}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    interval            = 60
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 20
    unhealthy_threshold = 3
    healthy_threshold   = 3
  }
  tags = var.tags
}

#https listener rule for frontend custom domain
resource "aws_lb_listener_rule" "https_host_header_rule" {
  listener_arn = var.https_listener_arn
  priority     = var.priority_number

  condition {
    host_header {
      values = ["${var.domain_name}"]
    }
  }
  condition {
    path_pattern {
      values = ["/*"]
    }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tasksmind-targetgroup.arn
  }
  tags = var.tags
}

resource "aws_ecs_task_definition" "task_definition" {
  family                   = "${var.project_name}-task-definition-${var.environment_name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([

    # UI Container
    {
      name  = "${var.project_name}-container-${var.environment_name}"
      image = var.image_uri

      portMappings = [
        {
          containerPort = 8000
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-region        = var.aws_region
          awslogs-group         = aws_cloudwatch_log_group.tasksmind_loggroup.name
          awslogs-stream-prefix = "ecs"
        }
      }

      environment = [
        {
          name  = "TEST"
          value = "test"
        }
      ]
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
  }
}

resource "aws_ecs_service" "tasksmind_service" {
  name            = "${var.project_name}-frontend-service-${var.environment_name}"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.task_definition.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  tags            = var.tags
  # Deployment configuration
  deployment_controller {
    type = "ECS"
  }

  # Health check grace period
  health_check_grace_period_seconds = 500

  # Network configuration
  network_configuration {
    assign_public_ip = true
    subnets          = var.public_subnet_ids
    security_groups  = var.ecs_sg_id
  }

  # Load balancer configuration
  load_balancer {
    target_group_arn = aws_lb_target_group.tasksmind-targetgroup.arn
    container_name   = "${var.project_name}-container-${var.environment_name}"
    container_port   = 8000
  }

  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"
}