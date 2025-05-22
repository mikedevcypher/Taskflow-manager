variable "project_name" {
  type        = string
  description = "Project name for resource naming"
}

variable "project_short" {
  type        = string
  description = "Short name for project"
  default     = "tmsaas"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where resources will be created"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "List of public subnet IDs for ALB"
}

variable "alb_port" {
  type        = number
  description = "Port ALB listens on"
  default     = 80
}

variable "health_check_path" {
  type        = string
  description = "Path for ALB health check"
  default     = "/"
}