variable "project_name" {
  type        = string
  description = "Name of the project"
  default     = "taskmanager-saas-deployment"
}

variable "project_short" {
  default = "tmsaas"
}

variable "environment" {
  type        = string
  description = "Environment (dev/staging/prod)"
  default     = "dev"
}

variable "aws_region" {
  type        = string
  description = "AWS Region"
  default     = "us-east-1"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones"
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private subnets"
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "github_repository" {
  type        = string
  description = "GitHub repository name"
  default     = "Taskflow-manager"
}

variable "github_owner" {
  type        = string
  description = "GitHub repository owner"
  default     = "mikedevcypher"
}