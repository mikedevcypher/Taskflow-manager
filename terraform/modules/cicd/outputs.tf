output "repository_url" {
  description = "The URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "github_connection_arn" {
  description = "The ARN of the GitHub CodeStar connection"
  value       = aws_codestarconnections_connection.github.arn
}

output "codebuild_project_name" {
  description = "Name of the CodeBuild project"
  value       = aws_codebuild_project.app.name
}

output "codepipeline_name" {
  description = "Name of the CodePipeline"
  value       = aws_codepipeline.app.name
}

output "artifacts_bucket_name" {
  description = "Name of the artifacts S3 bucket"
  value       = aws_s3_bucket.artifacts.bucket
}

output "github_source_details" {
  description = "GitHub repository details"
  value       = "${var.github_owner}/${var.github_repository}"
}
