terraform {
  backend "s3" {
    bucket = "acabot-terraform-bucket"
    key    = "dev/tasksmind/terraform.tfstate"  # Separate state file for dev
    region = "us-east-1"
  }
}