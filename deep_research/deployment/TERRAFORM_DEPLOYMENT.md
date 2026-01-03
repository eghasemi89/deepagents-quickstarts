# Terraform Infrastructure Deployment Guide

This guide will help you use Terraform to automatically provision all AWS infrastructure needed for the Deep Research Agent deployment.

## 🎯 What Terraform Creates

Terraform will automatically create:

- ✅ **ECR Repository** - Docker image registry
- ✅ **EC2 Instance** - Virtual server with Docker and Docker Compose pre-installed
- ✅ **IAM Role & Policies** - Permissions for EC2 to access ECR
- ✅ **Security Groups** - Network security rules for EC2 and Redis
- ✅ **ElastiCache Redis** - Managed Redis cluster (optional)
- ✅ **VPC Configuration** - Uses default VPC with proper subnet groups

## 📋 Prerequisites

Before you begin, you need:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured (see [AWS Backend Deployment Guide](./AWS_BACKEND_DEPLOYMENT.md) Step 0)
3. **Terraform** installed (version >= 1.0)
4. **EC2 Key Pair** created in AWS (for SSH access)

## Step 0: Install Terraform

**📍 WHERE:** Your Mac terminal

**⏱️ WHEN:** One-time setup (do this first)

**🔧 WHAT:** Terraform is a tool for building, changing, and versioning infrastructure

### Option A: Using Homebrew (Recommended)

```bash
brew install terraform
```

### Option B: Manual Installation

1. **Download Terraform:**
   - Go to: https://www.terraform.io/downloads
   - Download the macOS AMD64 version
   - Extract the zip file

2. **Install:**
   ```bash
   # Move to a directory in your PATH
   sudo mv terraform /usr/local/bin/
   
   # Verify installation
   terraform --version
   ```

**✅ Terraform is now installed!**

## Step 1: Create EC2 Key Pair

**📍 WHERE:** AWS Console → EC2 → Key Pairs

**⏱️ WHEN:** One-time setup (before running Terraform)

**🔧 WHAT:** You need an EC2 Key Pair for SSH access to your instance

### Step-by-Step Instructions

1. **Go to AWS Console:**
   - Open: https://console.aws.amazon.com
   - Navigate to **EC2** → **Key Pairs**

2. **Create Key Pair:**
   - Click **"Create key pair"** button
   - **Name:** Enter `deep-research-key` (or any name you prefer)
   - **Key pair type:** Select **"RSA"**
   - **Private key file format:** Select **".pem"** (for Mac/Linux)
   - Click **"Create key pair"**

3. **Save the Key:**
   - The `.pem` file will download automatically
   - Move it to `~/.ssh/` directory:
     ```bash
     mv ~/Downloads/deep-research-key.pem ~/.ssh/
     chmod 400 ~/.ssh/deep-research-key.pem
     ```

4. **Note the Key Name:**
   - Remember the key pair name (e.g., `deep-research-key`)
   - You'll need this for the Terraform configuration

**✅ EC2 Key Pair is now created!**

## Step 2: Configure Terraform Variables

**📍 WHERE:** `deployment/terraform/` directory

**⏱️ WHEN:** One-time setup (before first deployment)

**🔧 WHAT:** Configure Terraform with your AWS settings and preferences

### Step-by-Step Instructions

1. **Navigate to Terraform directory:**
   ```bash
   # From repository root (deepagents-quickstarts/)
   cd deep_research/deployment/terraform
   ```

2. **Copy the example variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit terraform.tfvars:**
   ```bash
   # Use your preferred editor
   nano terraform.tfvars
   # or
   vim terraform.tfvars
   # or open in VS Code
   code terraform.tfvars
   ```

4. **Update Required Variables:**
   ```hcl
   # REQUIRED: Your EC2 key pair name (created in Step 1)
   ec2_key_pair_name = "deep-research-key"
   
   # RECOMMENDED: Restrict SSH access to your IP
   # Find your IP: https://whatismyipaddress.com/
   ec2_allowed_ssh_cidr = "1.2.3.4/32"  # Replace with your IP
   
   # Optional: Customize other settings
   aws_region = "us-east-1"
   ec2_instance_type = "t3.medium"
   enable_elasticache = true
   ```

5. **Save the file**

**✅ Terraform variables are configured!**

**⚠️ Security Note:** 
- Never commit `terraform.tfvars` to git (it's in `.gitignore`)
- Use `terraform.tfvars.example` as a template
- For production, consider using AWS Secrets Manager or Parameter Store

## Step 3: Initialize Terraform

**📍 WHERE:** `deployment/terraform/` directory

**⏱️ WHEN:** One-time setup (before first deployment)

**🔧 WHAT:** Download required Terraform providers and modules

### Step-by-Step Instructions

1. **Navigate to Terraform directory:**
   ```bash
   # From repository root (deepagents-quickstarts/)
   cd deep_research/deployment/terraform
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

   This will:
   - Download the AWS provider
   - Set up the backend
   - Install required plugins

3. **Verify initialization:**
   - You should see: `Terraform has been successfully initialized!`
   - A `.terraform/` directory will be created (this is normal)

**✅ Terraform is initialized!**

## Step 4: Review Terraform Plan

**📍 WHERE:** `deployment/terraform/` directory

**⏱️ WHEN:** Before each deployment

**🔧 WHAT:** Preview what Terraform will create/modify/destroy

### Step-by-Step Instructions

1. **Generate a plan:**
   ```bash
   terraform plan
   ```

2. **Review the output:**
   - Terraform will show you all resources it plans to create
   - Review the plan carefully
   - Look for:
     - Resources to be created (marked with `+`)
     - Resources to be modified (marked with `~`)
     - Resources to be destroyed (marked with `-`)

3. **Save plan to file (optional):**
   ```bash
   terraform plan -out=tfplan
   ```
   - This saves the plan for later use
   - Useful for reviewing before applying

**✅ Plan reviewed!**

**📝 Note:** The plan shows what will happen but doesn't make any changes yet.

## Step 5: Deploy Infrastructure

**📍 WHERE:** `deployment/terraform/` directory

**⏱️ WHEN:** When ready to create/update infrastructure

**🔧 WHAT:** Actually create the AWS resources

### Step-by-Step Instructions

1. **Apply Terraform:**
   ```bash
   terraform apply
   ```

2. **Review the plan:**
   - Terraform will show the plan again
   - Type `yes` when prompted to confirm

3. **Wait for completion:**
   - Terraform will create resources one by one
   - This takes 5-15 minutes depending on resources
   - You'll see progress for each resource

4. **Note the outputs:**
   - After completion, Terraform will show outputs:
     - ECR repository URL
     - EC2 public IP
     - Redis endpoint (if enabled)
     - SSH command

**✅ Infrastructure is deployed!**

**📝 Important Outputs:**
- **EC2 Public IP:** You'll need this for `EC2_HOST` GitHub secret
- **ECR Repository URL:** Already configured in GitHub Actions workflow
- **Redis URI:** You'll need this for `REDIS_URI` GitHub secret (if using ElastiCache)

## Step 6: Get Deployment Information

**📍 WHERE:** `deployment/terraform/` directory

**⏱️ WHEN:** After deployment

**🔧 WHAT:** Retrieve important information about your infrastructure

### View All Outputs

```bash
terraform output
```

### View Specific Outputs

```bash
# EC2 Public IP
terraform output ec2_public_ip

# ECR Repository URL
terraform output ecr_repository_url

# Redis URI (if enabled)
terraform output redis_uri

# SSH Command
terraform output ec2_ssh_command
```

### Save Outputs to File

```bash
terraform output -json > outputs.json
```

**✅ You now have all the information needed for GitHub Secrets!**

## Step 7: Update GitHub Secrets

**📍 WHERE:** GitHub Repository → Settings → Secrets

**⏱️ WHEN:** After Terraform deployment

**🔧 WHAT:** Add the values from Terraform outputs to GitHub Secrets

### Required Secrets

Use the outputs from Step 6 to populate:

1. **`EC2_HOST`** - Use `ec2_public_ip` output
2. **`REDIS_URI`** - Use `redis_uri` output (if ElastiCache enabled)
3. **`ECR_REPOSITORY`** - Extract from `ecr_repository_url` output

See [AWS Backend Deployment Guide](./AWS_BACKEND_DEPLOYMENT.md) Step 2 for detailed instructions on adding GitHub Secrets.

## Step 8: Verify Infrastructure

**📍 WHERE:** AWS Console and SSH

**⏱️ WHEN:** After deployment

**🔧 WHAT:** Verify all resources were created correctly

### Verify in AWS Console

1. **ECR Repository:**
   - Go to ECR → Repositories
   - Verify `deep-research-agent` exists

2. **EC2 Instance:**
   - Go to EC2 → Instances
   - Verify instance is running
   - Check status checks (should be 2/2)

3. **ElastiCache (if enabled):**
   - Go to ElastiCache → Redis clusters
   - Verify cluster is available

4. **IAM Role:**
   - Go to IAM → Roles
   - Verify `deep-research-agent-ec2-role` exists

### Verify via SSH

```bash
# Use the SSH command from Terraform output
terraform output ec2_ssh_command

# Or manually:
ssh -i ~/.ssh/deep-research-key.pem ec2-user@<EC2_PUBLIC_IP>

# Once connected, verify Docker is installed:
docker --version
docker-compose --version
```

**✅ Infrastructure is verified!**

## 🔄 Updating Infrastructure

### Making Changes

1. **Edit Terraform files:**
   - Modify `.tf` files as needed
   - Update `terraform.tfvars` if needed

2. **Review changes:**
   ```bash
   terraform plan
   ```

3. **Apply changes:**
   ```bash
   terraform apply
   ```

### Common Updates

**Change EC2 Instance Type:**
```hcl
# In terraform.tfvars
ec2_instance_type = "t3.large"
```
Then run `terraform apply`

**Enable/Disable ElastiCache:**
```hcl
# In terraform.tfvars
enable_elasticache = false  # Use local Redis container instead
```
Then run `terraform apply`

**Update Security Group Rules:**
Edit `security_groups.tf` and run `terraform apply`

## 🗑️ Destroying Infrastructure

**⚠️ WARNING:** This will delete ALL resources created by Terraform!

### When to Destroy

- Testing/development environments
- Cost savings (stop paying for resources)
- Starting fresh

### How to Destroy

1. **Review what will be destroyed:**
   ```bash
   terraform plan -destroy
   ```

2. **Destroy infrastructure:**
   ```bash
   terraform destroy
   ```

3. **Confirm:** Type `yes` when prompted

4. **Wait for completion:**
   - All resources will be deleted
   - Takes 5-10 minutes

**✅ Infrastructure is destroyed!**

**📝 Note:** 
- ECR images will be deleted
- EC2 data will be lost
- Make sure to backup any important data first

## 📊 Terraform State Management

### Understanding State

Terraform stores state in `terraform.tfstate` file. This tracks:
- What resources exist
- Their current configuration
- Relationships between resources

### State File Location

- **Local:** `terraform.tfstate` (default, in terraform directory)
- **Remote:** Can be configured to use S3, Terraform Cloud, etc.

### Best Practices

1. **Never commit state files:**
   - They're in `.gitignore`
   - May contain sensitive information

2. **Backup state files:**
   - Copy `terraform.tfstate` before major changes
   - Store backups securely

3. **Use remote state for teams:**
   - Configure S3 backend for shared state
   - Use state locking (DynamoDB)

## 🔧 Advanced Configuration

### Using Remote State (S3 Backend)

Edit `main.tf` to add backend configuration:

```hcl
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "deep-research-agent/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### Using Workspaces

```bash
# Create a workspace
terraform workspace new dev
terraform workspace new prod

# Switch workspaces
terraform workspace select dev

# Use in configuration
resource "aws_instance" "main" {
  # ...
  tags = {
    Environment = terraform.workspace
  }
}
```

### Using Modules

For larger projects, consider organizing into modules:
- `modules/ec2/` - EC2 instance module
- `modules/ecr/` - ECR repository module
- `modules/elasticache/` - ElastiCache module

## 🐛 Troubleshooting

### Terraform Init Fails

**Error:** `Failed to query available provider packages`

**Solution:**
```bash
# Check internet connection
# Verify AWS credentials
aws sts get-caller-identity

# Try again
terraform init
```

### Terraform Apply Fails

**Error:** `Error creating EC2 instance: InvalidKeyPair.NotFound`

**Solution:**
- Verify key pair name in `terraform.tfvars` matches AWS
- Key pair must exist in the same region

**Error:** `Error creating ElastiCache: InvalidParameterValue`

**Solution:**
- Check subnet group has subnets in at least 2 availability zones
- Verify security group allows Redis access

### Resources Not Found After Apply

**Solution:**
```bash
# Refresh state
terraform refresh

# Show current state
terraform show
```

### State Lock Issues

**Error:** `Error acquiring the state lock`

**Solution:**
```bash
# If you're sure no other process is running
terraform force-unlock <LOCK_ID>
```

## 📚 Terraform Commands Reference

### Essential Commands

```bash
# Initialize
terraform init

# Plan changes
terraform plan

# Apply changes
terraform apply

# Destroy infrastructure
terraform destroy

# Show current state
terraform show

# List resources
terraform state list

# Refresh state
terraform refresh

# Validate configuration
terraform validate

# Format code
terraform fmt
```

### Output Commands

```bash
# Show all outputs
terraform output

# Show specific output
terraform output ec2_public_ip

# Show as JSON
terraform output -json
```

### State Commands

```bash
# List resources in state
terraform state list

# Show resource details
terraform state show aws_instance.main

# Remove resource from state (doesn't delete it)
terraform state rm aws_instance.main

# Import existing resource
terraform import aws_instance.main i-1234567890abcdef0
```

## 🔒 Security Best Practices

1. **Never commit sensitive data:**
   - Keep `terraform.tfvars` out of git
   - Use `.gitignore` (already configured)

2. **Restrict SSH access:**
   - Set `ec2_allowed_ssh_cidr` to your IP
   - Use format: `"1.2.3.4/32"` for single IP

3. **Use IAM roles:**
   - Terraform creates IAM roles automatically
   - Don't hardcode AWS credentials

4. **Enable encryption:**
   - ECR images are encrypted
   - EBS volumes are encrypted
   - ElastiCache encryption can be enabled

5. **Regular updates:**
   - Keep Terraform and providers updated
   - Review security groups regularly

## 💰 Cost Optimization

### Estimated Monthly Costs

- **EC2 t3.medium:** ~$30/month
- **ElastiCache cache.t3.micro:** ~$15/month
- **ECR storage:** ~$0.10/GB/month
- **Data transfer:** Varies

**Total:** ~$45-50/month (with ElastiCache)

### Cost Saving Tips

1. **Use smaller instances for testing:**
   ```hcl
   ec2_instance_type = "t3.micro"  # Free tier eligible
   ```

2. **Disable ElastiCache for testing:**
   ```hcl
   enable_elasticache = false  # Use local Redis container
   ```

3. **Use Spot Instances (advanced):**
   - Modify `ec2.tf` to use spot instances
   - Can save 70-90% on compute costs

4. **Destroy when not in use:**
   ```bash
   terraform destroy  # Stop paying for resources
   ```

## 🎉 Next Steps

After Terraform deployment:

1. ✅ **Update GitHub Secrets** with Terraform outputs
2. ✅ **Test GitHub Actions workflow** (should work automatically)
3. ✅ **Deploy frontend to Vercel** (see [Vercel Deployment Guide](./VERCEL_FRONTEND_DEPLOYMENT.md))
4. ✅ **Monitor costs** in AWS Cost Explorer
5. ✅ **Set up CloudWatch alarms** for monitoring

## 📖 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## 🆘 Need Help?

- Check the troubleshooting section above
- Review Terraform plan output carefully
- Verify AWS credentials and permissions
- Check AWS service quotas/limits
- Review CloudWatch logs for errors

Your infrastructure is now automated and ready for deployment! 🚀

