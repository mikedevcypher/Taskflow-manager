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

variable "github_repository" {
  type        = string
  description = "GitHub repository name"
  default     = "askmanager-saas-on-aws"
}

variable "github_owner" {
  type        = string
  description = "GitHub repository owner"
  default     = "mikedevcypher"
}

variable "repository_branch" {
  type        = string
  description = "Repository branch to track"
  default     = "dev"
}

variable "build_timeout" {
  type        = string
  description = "Build timeout in minutes"
  default     = "30"
}

variable "compute_type" {
  type        = string
  description = "CodeBuild compute type"
  default     = "BUILD_GENERAL1_SMALL"
}

variable "image" {
  type        = string
  description = "CodeBuild container image"
  default     = "aws/codebuild/amazonlinux2-x86_64-standard:4.0"
}
