# AWS Deployment Guide for LangGraph Deep Research Agent

This guide covers deploying your LangGraph agent to various AWS services.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Docker installed locally (for building images)
- AWS account with appropriate permissions

## Important: Redis is NOT Included in the Dockerfile

**Critical Understanding:**
- The `Dockerfile` only builds the **LangGraph API image** - it does NOT include Redis
- Redis is a **separate service** that must be deployed independently
- For AWS, you need to set up Redis using **ElastiCache** (recommended) or run it in a separate container

**Why Redis is Separate:**
- Redis is a stateful service that requires persistence
- It's better to use managed services (ElastiCache) for production
- Multiple API instances can share the same Redis cluster
- Easier to scale and manage independently

**What the Dockerfile Contains:**
- ✅ LangGraph API server
- ✅ Your application code
- ✅ All Python dependencies
- ❌ Redis (must be deployed separately)

## Building the Docker Image

### Option 1: Build Locally and Push to ECR

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name deep-research-agent --region us-east-1

# 2. Get login token and authenticate Docker
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# 3. Build the image
docker build -t deep-research-agent:latest .

# 4. Tag for ECR
docker tag deep-research-agent:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent:latest

# 5. Push to ECR
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent:latest
```

### Option 2: Build Using AWS CodeBuild

Create a `buildspec.yml`:

```yaml
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
```

## Deployment Options

### Option 1: AWS ECS (Elastic Container Service)

#### Step 1: Create Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "deep-research-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "langgraph-api",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "POSTGRES_URI",
          "value": "postgresql://postgres.ltbwpsjgivrwxoevnolj:password@aws-1-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require"
        },
        {
          "name": "REDIS_URI",
          "value": "redis://your-redis-endpoint:6379"
        },
        {
          "name": "LANGSMITH_API_KEY",
          "value": "your_langsmith_key"
        },
        {
          "name": "OPENAI_API_KEY",
          "value": "your_openai_key"
        },
        {
          "name": "TAVILY_API_KEY",
          "value": "your_tavily_key"
        }
      ],
      "secrets": [
        {
          "name": "POSTGRES_URI",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:langgraph/postgres-uri"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:langgraph/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/deep-research-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "python -c \"import httpx; httpx.get('http://localhost:8000/docs', timeout=5)\""],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Step 2: Register Task Definition

```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

#### Step 3: Create ECS Service

```bash
aws ecs create-service \
  --cluster your-cluster-name \
  --service-name deep-research-agent \
  --task-definition deep-research-agent \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=langgraph-api,containerPort=8000"
```

#### Step 4: Set Up Redis (ElastiCache) - REQUIRED

**Redis is NOT included in the Dockerfile** - you must set it up separately.

```bash
# Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id langgraph-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxx \
  --subnet-group-name your-subnet-group
```

**Get the Redis endpoint:**
```bash
aws elasticache describe-cache-clusters \
  --cache-cluster-id langgraph-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address'
```

**Update REDIS_URI in task definition** with ElastiCache endpoint:
- Format: `redis://<endpoint>:6379`
- Example: `redis://langgraph-redis.xxxxx.cache.amazonaws.com:6379`

### Option 2: AWS EKS (Elastic Kubernetes Service)

#### Step 1: Create Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deep-research-agent
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: deep-research-agent
  template:
    metadata:
      labels:
        app: deep-research-agent
    spec:
      containers:
      - name: langgraph-api
        image: <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_URI
          valueFrom:
            secretKeyRef:
              name: langgraph-secrets
              key: postgres-uri
        - name: REDIS_URI
          valueFrom:
            secretKeyRef:
              name: langgraph-secrets
              key: redis-uri
        - name: LANGSMITH_API_KEY
          valueFrom:
            secretKeyRef:
              name: langgraph-secrets
              key: langsmith-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: langgraph-secrets
              key: openai-api-key
        - name: TAVILY_API_KEY
          valueFrom:
            secretKeyRef:
              name: langgraph-secrets
              key: tavily-api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /docs
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /docs
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: deep-research-agent-service
spec:
  selector:
    app: deep-research-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### Step 2: Create Secrets

```bash
kubectl create secret generic langgraph-secrets \
  --from-literal=postgres-uri="your_postgres_uri" \
  --from-literal=redis-uri="your_redis_uri" \
  --from-literal=langsmith-api-key="your_key" \
  --from-literal=openai-api-key="your_key" \
  --from-literal=tavily-api-key="your_key"
```

#### Step 3: Deploy

```bash
kubectl apply -f k8s-deployment.yaml
```

### Option 3: AWS EC2 with Docker

#### Step 1: Launch EC2 Instance

```bash
# Launch EC2 instance with Docker pre-installed (use Amazon Linux 2023 AMI)
aws ec2 run-instances \
  --image-id ami-xxx \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxx \
  --user-data file://ec2-user-data.sh
```

#### Step 2: Create User Data Script

Create `ec2-user-data.sh`:

```bash
#!/bin/bash
# Install Docker
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Pull and run
docker pull <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent:latest
docker run -d \
  -p 80:8000 \
  -e POSTGRES_URI="your_postgres_uri" \
  -e REDIS_URI="your_redis_uri" \
  -e LANGSMITH_API_KEY="your_key" \
  -e OPENAI_API_KEY="your_key" \
  -e TAVILY_API_KEY="your_key" \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent:latest
```

## Required AWS Resources

### 1. Redis (ElastiCache)

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id langgraph-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxx \
  --subnet-group-name your-subnet-group
```

### 2. Application Load Balancer (for ECS/EKS)

```bash
aws elbv2 create-load-balancer \
  --name langgraph-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx
```

### 3. CloudWatch Logs

```bash
aws logs create-log-group --log-group-name /ecs/deep-research-agent
```

## Environment Variables

Store sensitive values in AWS Secrets Manager or Parameter Store:

### Using AWS Secrets Manager

```bash
# Create secret
aws secretsmanager create-secret \
  --name langgraph/secrets \
  --secret-string '{
    "POSTGRES_URI": "your_postgres_uri",
    "REDIS_URI": "your_redis_uri",
    "LANGSMITH_API_KEY": "your_key",
    "OPENAI_API_KEY": "your_key",
    "TAVILY_API_KEY": "your_key"
  }'
```

### Using Systems Manager Parameter Store

```bash
aws ssm put-parameter --name "/langgraph/postgres-uri" --value "your_uri" --type "SecureString"
aws ssm put-parameter --name "/langgraph/redis-uri" --value "your_uri" --type "SecureString"
aws ssm put-parameter --name "/langgraph/langsmith-api-key" --value "your_key" --type "SecureString"
```

## Security Best Practices

1. **Use IAM Roles**: Don't hardcode AWS credentials
2. **Secrets Management**: Use AWS Secrets Manager or Parameter Store
3. **VPC Configuration**: Run containers in private subnets
4. **Security Groups**: Restrict access to necessary ports only
5. **Encryption**: Enable encryption at rest and in transit
6. **Network Isolation**: Use VPC endpoints for AWS services

## Monitoring and Logging

### CloudWatch Logs

Logs are automatically sent to CloudWatch if configured in task definition.

### CloudWatch Metrics

Monitor:
- CPU utilization
- Memory utilization
- Request count
- Error rate
- Response time

### Health Checks

The Dockerfile includes a health check. Ensure your load balancer/ECS health checks match:
- Path: `/docs` or `/`
- Port: `8000` (container) or `80` (ALB)
- Interval: 30 seconds
- Timeout: 5 seconds

## Cost Optimization

1. **Use Fargate Spot** for non-critical workloads
2. **Right-size instances** based on actual usage
3. **Use ElastiCache** instead of running Redis in ECS
4. **Enable auto-scaling** based on CPU/memory
5. **Use Reserved Instances** for predictable workloads

## Troubleshooting

### Container won't start

1. Check CloudWatch logs: `/ecs/deep-research-agent`
2. Verify environment variables are set correctly
3. Check security group rules allow traffic
4. Verify Redis and PostgreSQL are accessible

### Connection refused errors

1. Verify REDIS_URI and POSTGRES_URI are correct
2. Check security groups allow connections
3. Ensure containers are in the same VPC/subnet

### High memory usage

1. Increase task memory in ECS task definition
2. Monitor with CloudWatch
3. Consider using larger instance types

## Quick Start Commands

```bash
# Build and push to ECR
docker build -t deep-research-agent:latest .
docker tag deep-research-agent:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent:latest

# Deploy to ECS
aws ecs update-service --cluster your-cluster --service deep-research-agent --force-new-deployment

# View logs
aws logs tail /ecs/deep-research-agent --follow
```

## Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [AWS ElastiCache Documentation](https://docs.aws.amazon.com/elasticache/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

