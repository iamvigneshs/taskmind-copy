public_subnet_ids  = ["subnet-0b098996c0827eb56"]
aws_region         = "us-east-1"
environment_name   = "dev"
project_name       = "tasksmind"
cpu                = "256"
memory             = "0.5GB"
ecs_sg_id          = ["sg-07ad24c20f9483b53"]
vpc_id             = "vpc-00dc510c852034bf3"
execution_role_arn = "arn:aws:iam::992382671809:role/acabot-ecs-task-execution-role-dev"
task_role_arn      = "arn:aws:iam::992382671809:role/acabot-ecs-task-role-dev"
tags               = { applicationName = "tasksmind", clientName = "Acarin", createdBy = "tasksmind", environment = "dev" }
ecs_cluster_arn    = "arn:aws:ecs:us-east-1:992382671809:cluster/acabot-cluster-dev"
alb_arn            = "arn:aws:elasticloadbalancing:us-east-1:992382671809:loadbalancer/app/acabot-alb-dev/6864f09276da2db4"
https_listener_arn = "arn:aws:elasticloadbalancing:us-east-1:992382671809:listener/app/acabot-alb-dev/6864f09276da2db4/4633b849ac937e4a"
ecs_cluster_name   = "acabot-cluster-dev"
priority_number    = 100

image_uri            = "IMAGE_URI"
domain_name             = "dev-tasksmind.acarin.net"
