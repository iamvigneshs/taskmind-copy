variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment_name" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
}

variable "cpu" {
  description = "CPU units for the ECS task"
  type        = string
}

variable "memory" {
  description = "Memory for the ECS task"
  type        = string
}

variable "execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}


variable "task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "image_uri" {
  description = "Docker image URI for the ECS container"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "ecs_sg_id" {
  description = "List of security group IDs"
  type        = list(string)
}

variable "vpc_id" {
  description = "Vpc ID"
  type        = string
}

variable "domain_name" {
  description = "Domain Name"
  type        = string
}

variable "alb_arn" {
  description = "ALB ARN"
  type        = string
}

variable "https_listener_arn" {
  description = "https listener ARN"
  type        = string 
}

variable "ecs_cluster_name" {
  description = "ECS Cluster Name"
  type        = string 
}

variable "priority_number" {
  description = "Host Header Priority Number"
  type        = string  
}