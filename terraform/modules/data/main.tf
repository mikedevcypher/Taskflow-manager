# Random password for RDS
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Secrets Manager for RDS credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.project_name}-${var.environment}-db-credentials"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = "dbadmin"
    password = random_password.db_password.result
  })
}

# Security Groups
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ec2_security_group_id]
  }
}

resource "aws_security_group" "cache" {
  name        = "${var.project_name}-${var.environment}-cache-sg"
  description = "Security group for ElastiCache"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 11211
    to_port         = 11211
    protocol        = "tcp"
    security_groups = [var.ec2_security_group_id]
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = var.private_subnet_ids
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier        = var.identifier
  engine            = "postgres"
  engine_version    = "14"
  instance_class    = var.db_instance_class
  allocated_storage = 10

  db_name  = var.db_name
  username = jsondecode(aws_secretsmanager_secret_version.db_credentials.secret_string)["username"]
  password = jsondecode(aws_secretsmanager_secret_version.db_credentials.secret_string)["password"]

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot = true
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Environment = var.environment
  }
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-cache-subnet"
  subnet_ids = var.private_subnet_ids
}

# ElastiCache Cluster
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "${var.project_name}-${var.environment}-cache"
  engine              = "memcached"
  node_type           = var.cache_node_type
  num_cache_nodes     = var.cache_num_nodes
  port                = 11211
  
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.cache.id]

  tags = {
    Name        = "${var.project_name}-${var.environment}-cache"
    Environment = var.environment
  }
}

# S3 Bucket
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-${var.environment}-logs"
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}