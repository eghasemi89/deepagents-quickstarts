# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "redis" {
  count      = var.enable_elasticache ? 1 : 0
  name       = "${var.project_name}-redis-subnet"
  subnet_ids = data.aws_subnets.default.ids
}

# Get default subnets
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ElastiCache Redis Cluster
# Using replication_group for flexibility (works for single and multi-node)
resource "aws_elasticache_replication_group" "redis" {
  count                         = var.enable_elasticache ? 1 : 0
  replication_group_id          = "${var.project_name}-redis"
  description                   = "Redis cluster for ${var.project_name}"
  engine                        = "redis"
  engine_version                = "7.1"
  node_type                     = var.elasticache_node_type
  port                          = 6379
  parameter_group_name          = "default.redis7"
  num_cache_clusters            = var.elasticache_num_cache_nodes
  automatic_failover_enabled    = var.elasticache_num_cache_nodes > 1 ? true : false
  multi_az_enabled              = var.elasticache_num_cache_nodes > 1 ? true : false
  subnet_group_name             = aws_elasticache_subnet_group.redis[0].name
  security_group_ids            = [aws_security_group.redis[0].id]
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = false # Set to true for production with auth
  snapshot_retention_limit      = 1
  snapshot_window               = "03:00-05:00"

  tags = {
    Name = "${var.project_name}-redis"
  }
}

