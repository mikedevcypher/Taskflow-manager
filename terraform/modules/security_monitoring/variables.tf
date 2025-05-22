variable "project_name" {
  type        = string
  description = "Project name for resource naming"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "retention_days" {
  type        = number
  description = "CloudWatch log retention in days"
  default     = 7
}