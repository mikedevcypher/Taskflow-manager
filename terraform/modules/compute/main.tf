# IAM Role and Instance Profile
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_short}-${var.environment}-ec2-role"

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

resource "aws_iam_role_policy_attachment" "ecr_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_short}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# Security Group for EC2 instances
resource "aws_security_group" "ec2" {
  name        = "${var.project_short}-${var.environment}-ec2-sg"
  description = "Security group for EC2 instances"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_short}-${var.environment}-ec2-sg"
    Environment = var.environment
  }
}

# Launch Template
resource "aws_launch_template" "main" {
  name_prefix   = "${var.project_short}-${var.environment}-lt"
  image_id      = "ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS AMI
  instance_type = var.instance_type

  network_interfaces {
    associate_public_ip_address = false
    security_groups            = [aws_security_group.ec2.id]
  }

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  user_data = base64encode(<<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io python3-pip awscli
              pip3 install PyJWT Flask-Limiter==3.12 flask_compress flask_talisman flask_mail
              systemctl start docker
              systemctl enable docker
              aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com
              docker pull 823357529591.dkr.ecr.us-east-1.amazonaws.com/taskmanager-saas-deployment-dev:27ac4aa
              docker run -d -p 5000:5000 823357529591.dkr.ecr.us-east-1.amazonaws.com/taskmanager-saas-deployment-dev:27ac4aa
              EOF
)


  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.project_short}-${var.environment}-instance"
      Environment = var.environment
    }
  }
}


# Auto Scaling Group
resource "aws_autoscaling_group" "main" {
  name                = "${var.project_short}-${var.environment}-asg"
  desired_capacity    = var.desired_capacity
  max_size            = var.max_size
  min_size            = var.min_size
  target_group_arns   = [var.alb_target_group_arn]
  vpc_zone_identifier = var.private_subnet_ids

  launch_template {
    id      = aws_launch_template.main.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_short}-${var.environment}-asg"
    propagate_at_launch = true
  }
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}