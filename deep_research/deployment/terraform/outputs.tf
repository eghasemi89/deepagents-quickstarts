output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.main.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.main.arn
}

output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.main.id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.main.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.main.public_dns
}

output "ec2_ssh_command" {
  description = "SSH command to connect to EC2 instance"
  value       = "ssh -i ~/.ssh/${var.ec2_key_pair_name}.pem ec2-user@${aws_instance.main.public_ip}"
}

output "redis_endpoint" {
  description = "Redis endpoint (if ElastiCache is enabled)"
  value       = var.enable_elasticache ? aws_elasticache_replication_group.redis[0].configuration_endpoint_address : null
}

output "redis_port" {
  description = "Redis port"
  value       = var.enable_elasticache ? aws_elasticache_replication_group.redis[0].port : null
}

output "redis_uri" {
  description = "Redis connection URI"
  value       = var.enable_elasticache ? "redis://${aws_elasticache_replication_group.redis[0].configuration_endpoint_address}:${aws_elasticache_replication_group.redis[0].port}" : null
}

output "deployment_summary" {
  description = "Summary of deployed infrastructure"
  value = {
    ecr_repository = aws_ecr_repository.main.repository_url
    ec2_instance   = aws_instance.main.public_ip
    ec2_dns        = aws_instance.main.public_dns
    redis_endpoint = var.enable_elasticache ? aws_elasticache_replication_group.redis[0].configuration_endpoint_address : "Not enabled (using local Redis container)"
  }
}

