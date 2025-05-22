# IAM Roles
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/${var.project_name}/${var.environment}/application"
  retention_in_days = var.retention_days
}

resource "aws_cloudwatch_log_group" "access" {
  name              = "/aws/${var.project_name}/${var.environment}/access"
  retention_in_days = var.retention_days
}

resource "aws_cloudwatch_log_group" "error" {
  name              = "/aws/${var.project_name}/${var.environment}/error"
  retention_in_days = var.retention_days
}

# Secrets Manager
resource "aws_secretsmanager_secret" "jwt_secret" {
  name = "${var.project_name}-${var.environment}-jwt-secret"
}

resource "random_password" "jwt_secret" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}

resource "aws_secretsmanager_secret" "slack_webhook" {
  name = "${var.project_name}-${var.environment}-slack-webhook"
}

resource "aws_secretsmanager_secret_version" "slack_webhook" {
  secret_id     = aws_secretsmanager_secret.slack_webhook.id
  secret_string = "placeholder-update-manually"  # Update this manually in AWS Console
}

# SSM Parameter Store
resource "aws_ssm_parameter" "app_config" {
  name  = "/${var.project_name}/${var.environment}/config"
  type  = "SecureString"
  value = jsonencode({
    environment = var.environment
    log_level   = "info"
  })
}