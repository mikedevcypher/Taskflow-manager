output "rds_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.main.endpoint
}

output "memcached_endpoint" {
  description = "The configuration endpoint for the ElastiCache cluster"
  value       = aws_elasticache_cluster.main.configuration_endpoint
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket"
  value       = aws_s3_bucket.logs.bucket
}

output "db_secret_arn" {
  description = "The ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "rds_security_group_id" {
  description = "The ID of the RDS security group"
  value       = aws_security_group.rds.id
}

output "cache_security_group_id" {
  description = "The ID of the ElastiCache security group"
  value       = aws_security_group.cache.id
}