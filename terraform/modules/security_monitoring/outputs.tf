output "ec2_role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.arn
}

output "ec2_role_name" {
  description = "Name of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.name
}

output "cloudwatch_log_groups" {
  description = "Map of CloudWatch Log Group names"
  value = {
    application = aws_cloudwatch_log_group.application.name
    access      = aws_cloudwatch_log_group.access.name
    error       = aws_cloudwatch_log_group.error.name
  }
}

output "secret_arns" {
  description = "Map of Secret ARNs"
  value = {
    jwt_secret    = aws_secretsmanager_secret.jwt_secret.arn
    slack_webhook = aws_secretsmanager_secret.slack_webhook.arn
  }
}

output "ssm_parameter_name" {
  description = "Name of the SSM Parameter"
  value       = aws_ssm_parameter.app_config.name
}