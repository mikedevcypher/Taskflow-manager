# Networking Outputs
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.networking.private_subnet_ids
}

output "nat_gateway_ips" {
  description = "List of NAT Gateway public IPs"
  value       = module.networking.nat_gateway_ips
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = module.networking.vpc_cidr_block
}

# Frontend/ALB Outputs
output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = module.frontend.alb_dns_name
}

output "alb_arn" {
  description = "The ARN of the load balancer"
  value       = module.frontend.alb_arn
}

output "alb_target_group_arn" {
  description = "The ARN of the target group"
  value       = module.frontend.target_group_arn
}

output "alb_security_group_id" {
  description = "The ID of the ALB security group"
  value       = module.frontend.alb_security_group_id
}

# Compute Outputs
output "asg_name" {
  description = "Name of the Auto Scaling Group"
  value       = module.compute.asg_name
}

output "launch_template_id" {
  description = "ID of the Launch Template"
  value       = module.compute.launch_template_id
}

output "ec2_security_group_id" {
  description = "ID of the EC2 security group"
  value       = module.compute.security_group_id
}

# CICD Outputs
output "ecr_repository_url" {
  description = "The URL of the ECR repository"
  value       = module.cicd.repository_url
}

output "github_connection_arn" {
  description = "The ARN of the GitHub CodeStar connection"
  value       = module.cicd.github_connection_arn
}

output "github_source_details" {
  description = "GitHub repository details"
  value       = module.cicd.github_source_details
}

output "codebuild_project_name" {
  description = "Name of the CodeBuild project"
  value       = module.cicd.codebuild_project_name
}

output "codepipeline_name" {
  description = "Name of the CodePipeline"
  value       = module.cicd.codepipeline_name
}

output "artifacts_bucket_name" {
  description = "Name of the artifacts S3 bucket"
  value       = module.cicd.artifacts_bucket_name
}

# Additional Useful Outputs
output "environment" {
  description = "Current environment"
  value       = var.environment
}

output "project_name" {
  description = "Name of the project"
  value       = var.project_name
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "db_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = module.data.rds_endpoint
}

output "cache_endpoint" {
  description = "The configuration endpoint for the ElastiCache cluster"
  value       = module.data.memcached_endpoint
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket"
  value       = module.data.s3_bucket_name
}

output "db_secret_arn" {
  description = "The ARN of the database credentials secret"
  value       = module.data.db_secret_arn
}

output "rds_security_group_id" {
  description = "The ID of the RDS security group"
  value       = module.data.rds_security_group_id
}

output "cache_security_group_id" {
  description = "The ID of the ElastiCache security group"
  value       = module.data.cache_security_group_id
}

output "ec2_role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = module.security_monitoring.ec2_role_arn
}

output "ec2_role_name" {
  description = "Name of the EC2 IAM role"
  value       = module.security_monitoring.ec2_role_name
}

output "cloudwatch_log_groups" {
  description = "Map of CloudWatch Log Group names"
  value       = module.security_monitoring.cloudwatch_log_groups
}

output "secret_arns" {
  description = "Map of Secret ARNs"
  value       = module.security_monitoring.secret_arns
}

output "ssm_parameter_name" {
  description = "Name of the SSM Parameter"
  value       = module.security_monitoring.ssm_parameter_name
}
