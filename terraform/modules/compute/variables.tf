variable "project_name" {
  type        = string
  description = "Project name for resource naming"
}

variable "project_short" {
  type        = string
  description = "Short name for resource naming"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where resources will be created"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for ASG"
}

variable "alb_target_group_arn" {
  type        = string
  description = "ARN of ALB target group"
}

variable "alb_security_group_id" {
  type        = string
  description = "Security group ID of the ALB"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"
}

variable "min_size" {
  type        = number
  description = "Minimum size of ASG"
  default     = 1
}

variable "max_size" {
  type        = number
  description = "Maximum size of ASG"
  default     = 3
}

variable "desired_capacity" {
  type        = number
  description = "Desired capacity of ASG"
  default     = 2
}