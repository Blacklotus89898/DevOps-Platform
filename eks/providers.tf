terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Strictly locks to 5.x to prevent the v6.0 crash
    }
  }
}

provider "aws" {
  region = "us-east-1"
}