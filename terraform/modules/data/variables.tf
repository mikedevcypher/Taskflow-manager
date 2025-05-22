variable "project_name" {
  type        = string
  description = "Project name for resource naming"
}

variable "identifier" {
  type        = string
  description = "DB instance identifier"
  default     = "taskmanagerdb"
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "dev"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where resources will be created"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs"
}

variable "ec2_security_group_id" {
  type        = string
  description = "Security group ID of EC2 instances"
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class"
  default     = "db.t3.micro"
}

variable "db_name" {
  type        = string
  description = "Name of the database"
  default     = "taskmanagerappdb"
}

variable "cache_node_type" {
  type        = string
  description = "ElastiCache node type"
  default     = "cache.t3.micro"
}

variable "cache_num_nodes" {
  type        = number
  description = "Number of cache nodes"
  default     = 2
}