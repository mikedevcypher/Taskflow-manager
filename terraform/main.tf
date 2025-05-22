provider "aws" {
  profile = "taskmanager-saas"
  region  = var.aws_region
}


terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

module "networking" {
  source = "./modules/networking"

  project_name         = var.project_name
  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

module "frontend" {
    source = "./modules/frontend"

    project_name = var.project_name
    environment = var.environment
    vpc_id = module.networking.vpc_id
    public_subnet_ids = module.networking.public_subnet_ids
}

module "compute" {
  source = "./modules/compute"

  project_name          = var.project_name
  project_short         = var.project_short
  environment          = var.environment
  vpc_id              = module.networking.vpc_id
  private_subnet_ids   = module.networking.private_subnet_ids
  alb_target_group_arn = module.frontend.target_group_arn
  alb_security_group_id = module.frontend.alb_security_group_id
}

module "cicd" {
  source = "./modules/cicd"
  
  project_name      = var.project_name
  project_short      = var.project_short
  environment       = var.environment
  github_repository = "${var.github_repository}"  # Format: owner/repo
  repository_branch = "dev-fix"
}

module "data" {
  source = "./modules/data"

  project_name          = var.project_name
  environment          = var.environment
  vpc_id              = module.networking.vpc_id
  private_subnet_ids   = module.networking.private_subnet_ids
  ec2_security_group_id = module.compute.security_group_id
}

module "security_monitoring" {
  source = "./modules/security_monitoring"

  project_name   = var.project_name
  environment    = var.environment
}
