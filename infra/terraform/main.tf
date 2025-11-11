terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.20"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }

  }

  # backend "s3" {
  #   bucket         = "machi-quest-terraform-state"
  #   key            = "production/s3/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "machi-quest-terraform-locks"
  #   encrypt        = true
  # }


}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}