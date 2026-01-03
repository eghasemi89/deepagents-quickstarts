variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "deep-research-agent"
}

# EC2 Configuration
variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "ec2_key_pair_name" {
  description = "Name of existing EC2 Key Pair for SSH access"
  type        = string
}

variable "ec2_allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into EC2 instance (use your IP or 0.0.0.0/0 for testing)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "ec2_allowed_http_cidr" {
  description = "CIDR block allowed to access HTTP port (use 0.0.0.0/0 for public access)"
  type        = string
  default     = "0.0.0.0/0"
}

# ElastiCache Configuration
variable "enable_elasticache" {
  description = "Enable ElastiCache Redis cluster"
  type        = bool
  default     = true
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "elasticache_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

# ECR Configuration
variable "ecr_image_scanning" {
  description = "Enable image scanning on push"
  type        = bool
  default     = true
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

