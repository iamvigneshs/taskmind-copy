provider "aws" {
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.67.0"
    }
  }

  required_version = ">= 1.4.2"
}

module "ECS" {
  source             = "../modules/ecs"
  public_subnet_ids  = var.public_subnet_ids
  vpc_id             = var.vpc_id
  aws_region         = var.aws_region
  environment_name   = var.environment_name
  project_name       = var.project_name
  ecs_cluster_arn    = var.ecs_cluster_arn
  cpu                = var.cpu
  memory             = var.memory
  task_role_arn      = var.task_role_arn
  execution_role_arn = var.execution_role_arn
  ecs_sg_id          = var.ecs_sg_id
  IMAGE_URI          = var.image_uri
  tags               = var.tags
  domain_name        = var.domain_name
  alb_arn            = var.alb_arn
  https_listener_arn = var.https_listener_arn
  ecs_cluster_name   = var.ecs_cluster_name
  priority_number    = var.priority_number
}
