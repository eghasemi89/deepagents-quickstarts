# GitHub CI/CD Setup for AWS Deployment

This guide will help you set up GitHub Actions to automatically build and deploy your Docker Compose application to AWS.

## 🎯 One-Time Setup vs Automated Deployment

### ✅ ONE-TIME SETUP (Do this once)
These steps are done **once** during initial setup. After completing them, you won't need to repeat them:

| Step | What | Where | Time Required |
|------|------|-------|---------------|
| 0 | Install AWS CLI on Mac | Mac terminal | 5-10 minutes |
| 1.1 | Create ECR repository | AWS Console | 5 minutes |
| 1.2 | Set up EC2 instance | AWS Console | 15-20 minutes |
| 1.3 | Configure EC2 IAM role | AWS Console → IAM | 10 minutes |
| 1.4 | Set up ElastiCache Redis | AWS Console → ElastiCache | 15-20 minutes |
| 2 | Add GitHub Secrets | GitHub Repository → Settings | 15-20 minutes |
| 3 | Generate SSH keys | Local terminal | 5 minutes |
| 4 | Push workflow file | Git push | 2 minutes |

**Total one-time setup:** ~1 hour

### 🤖 AUTOMATED (Happens automatically after setup)
Once setup is complete, these happen **automatically** every time you push code:

| Action | When | How |
|--------|------|-----|
| Build Docker image | On every push to main/master | GitHub Actions |
| Push to ECR | After build completes | GitHub Actions |
| Deploy to EC2 | After image push | GitHub Actions |
| Health check | After deployment | GitHub Actions |

**You do NOT need to do anything manually for each deployment** - just push your code!

### 📝 Quick Answer: Do I Have to Do This Every Time?

**NO!** Here's the breakdown:

- **One-time setup:** ~1 hour (Steps 1-4) - Do this once
- **Each deployment:** 0 minutes - Just push code, deployment is automatic
- **Manual trigger:** Optional - Can trigger manually from GitHub Actions UI if needed

**After setup, deploying is as simple as:**
```bash
git push origin main
```

That's it! The rest happens automatically.

## 📋 Quick Start Checklist

### One-Time Setup (Do Once)
- [ ] **Step 0:** Install AWS CLI on Mac
- [ ] **Step 1.1:** Create ECR repository in AWS
- [ ] **Step 1.2:** Launch EC2 instance with Docker and Docker Compose
- [ ] **Step 1.3:** Create and attach IAM role to EC2 for ECR access
- [ ] **Step 1.4:** Set up ElastiCache Redis - OR use local Redis container
- [ ] **Step 2:** Add all required secrets to GitHub repository
- [ ] **Step 3:** Generate SSH key pair for EC2 access
- [ ] **Step 4:** Push workflow file to repository
- [ ] **Step 5:** Test deployment

### After Setup (Automatic)
- ✅ Every push to main/master triggers automatic deployment
- ✅ Manual trigger available via GitHub Actions UI

## Prerequisites

1. **AWS Account** with appropriate permissions
   - Sign up at https://aws.amazon.com (if you don't have one)
   - You'll need a credit card, but the free tier covers most initial setup
2. **Mac computer** with terminal access
3. **GitHub Repository** with Actions enabled
4. **Basic familiarity** with terminal/command line

## Step 0: Install AWS CLI on Mac

**📍 WHERE:** Your Mac terminal

**⏱️ WHEN:** One-time setup (do this first)

**🔧 WHAT:** AWS CLI lets you run AWS commands from your terminal

### Option A: Using Homebrew (Recommended - Easiest)

1. **Install Homebrew** (if you don't have it):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
   - Follow the prompts and enter your Mac password when asked
   - This may take a few minutes

2. **Install AWS CLI:**
   ```bash
   brew install awscli
   ```

3. **Verify installation:**
   ```bash
   aws --version
   ```
   - You should see something like: `aws-cli/2.x.x Python/3.x.x ...`

### Option B: Using the AWS Installer

1. **Download the installer:**
   - Go to: https://awscli.amazonaws.com/AWSCLIV2.pkg
   - Or visit: https://aws.amazon.com/cli/ → Click "Download the installer"

2. **Run the installer:**
   - Double-click the downloaded `.pkg` file
   - Follow the installation wizard
   - Click "Install" and enter your Mac password

3. **Verify installation:**
   ```bash
   aws --version
   ```

### Configure AWS CLI

After installation, configure it with your AWS credentials:

1. **Get your AWS Access Keys:**
   - Go to AWS Console: https://console.aws.amazon.com
   - Click your username (top right) → **"Security credentials"**
   - Scroll to **"Access keys"** section
   - Click **"Create access key"**
   - ~Choose **"Command Line Interface (CLI)"**~
   - Click **"Next"** → **"Create access key"**
   - **⚠️ IMPORTANT:** Copy both the Access Key ID and Secret Access Key immediately (you won't see the secret again!)

2. **Configure AWS CLI:**
   ```bash
   aws configure
   ```
   
   You'll be prompted for:
   - **AWS Access Key ID:** Paste your access key ID
   - **AWS Secret Access Key:** Paste your secret access key
   - **Default region name:** Enter `us-east-1` (or your preferred region)
   - **Default output format:** Press Enter (uses `json` by default)

3. **Test the configuration:**
   ```bash
   aws sts get-caller-identity
   ```
   - Should return your AWS account ID and user info
   - If you see an error, check your credentials

**✅ AWS CLI is now installed and configured!**

## Step 1: Create AWS Resources

### 1.1 Create ECR Repository

**📍 WHERE:** AWS Console → ECR Service (or AWS CLI)

**⏱️ WHEN:** One-time setup

**🔧 WHAT:** Create a Docker image repository where your built images will be stored

#### Option A: Using AWS Console (Easier)

1. **Go to ECR Console:**
   - In AWS Console search bar, type "ECR"
   - Click on **"Elastic Container Registry"** service

2. **Create Repository:**
   - Click **"Get started"** (if first time) or **"Create repository"** button
   - **Visibility settings:** Select **"Private"** (recommended)
   - **Repository name:** Enter `deep-research-agent`
   - **Tag immutability:** Leave default (optional)
   - **Scan on push:** Check **"Enable scan on push"** (recommended for security)
   - **Encryption:** Leave default (AWS managed encryption key)
   - Click **"Create repository"**

3. **Get Repository URI:**
   - After creation, click on your repository name
   - At the top, you'll see **"Repository URI"**
   - Copy this URI (format: `<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent`)
   - **📝 Note:** You'll need this later, but the workflow handles it automatically

#### Option B: Using AWS CLI (Command Line)

If you prefer using the terminal:

```bash
aws ecr create-repository \
  --repository-name deep-research-agent \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true
```

**Output will show:**
- `repositoryUri`: Copy this value (format: `<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/deep-research-agent`)

**✅ ECR Repository is now created!**

**📝 Note:** The repository URI format is: `<YOUR_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/deep-research-agent`

### 1.2 Set Up EC2 Instance

**📍 WHERE:** AWS Console → EC2 Service

**⏱️ WHEN:** One-time setup

**🔧 WHAT:** Launch a virtual server (EC2 instance) where your application will run

#### Step-by-Step: Launch EC2 Instance

1. **Go to AWS Console:**
   - Open: https://console.aws.amazon.com
   - Sign in with your AWS account

2. **Navigate to EC2:**
   - In the search bar at the top, type "EC2"
   - Click on **"EC2"** service (under Services)

3. **Launch Instance:**
   - Click the orange **"Launch Instance"** button (top right)
   - Or click **"Instances"** in the left sidebar, then **"Launch Instance"**

4. **Configure Instance Details:**

   **a. Name your instance:**
   - In the **"Name"** field, enter: `deep-research-agent` (or any name you prefer)

   **b. Choose an AMI (Amazon Machine Image):**
   - Click **"Browse more AMIs"** or scroll down
   - For **Amazon Linux 2023**: Search for "Amazon Linux 2023" → Select **"Amazon Linux 2023 AMI"**
   - For **Ubuntu**: Search for "Ubuntu" → Select **"Ubuntu Server 22.04 LTS"**
   - **Recommendation:** Use Amazon Linux 2023 (it's optimized for AWS)

   **c. Choose Instance Type:**
   - Select **"t3.medium"** (2 vCPU, 4 GB RAM) - this is sufficient for most use cases
   - For testing, you can use **"t3.micro"** (free tier eligible, but may be slower)
   - For production, consider **"t3.large"** or larger

   **d. Create or Select Key Pair:**
   - Under **"Key pair (login)"**, click **"Create new key pair"**
   - **Key pair name:** Enter `deep-research-key` (or any name)
   - **Key pair type:** Select **"RSA"**
   - **Private key file format:** Select **".pem"** (for Mac/Linux)
   - Click **"Create key pair"**
   - **⚠️ IMPORTANT:** The `.pem` file will download automatically - save it securely! You'll need it to SSH into the instance.

   **e. Network Settings:**
   - Click **"Edit"** next to Network settings
   - **VPC:** Leave default (or select your VPC)
   - **Subnet:** Leave default
   - **Auto-assign Public IP:** Select **"Enable"**
   - **Firewall (security groups):** Select **"Create security group"**
     - **Security group name:** `deep-research-sg`
     - **Description:** `Security group for deep research agent`
     - **Inbound rules:** Add these rules:
       - **SSH (22):** 
         - Type: SSH
         - Source: **"My IP"** (automatically fills your IP) OR **"Anywhere-IPv4"** (0.0.0.0/0) for testing
       - **HTTP (8123):**
         - Type: Custom TCP
         - Port: 8123
         - Source: **"Anywhere-IPv4"** (0.0.0.0/0) OR **"My IP"** for security
       - **HTTPS (443):** (Optional, if using SSL)
         - Type: HTTPS
         - Source: **"Anywhere-IPv4"** (0.0.0.0/0)
     - **Outbound rules:** Leave default (all traffic allowed)

   **f. Configure Storage:**
   - **Size (GiB):** 20 GB is usually sufficient (free tier includes 30 GB)
   - **Volume type:** gp3 (default, cheaper) or gp2
   - You can increase this later if needed

   **g. Advanced Details - User Data:**
   - Expand **"Advanced details"** section at the bottom
   - Scroll to **"User data"** field
   - Paste the following script (this installs Docker and Docker Compose automatically):

```bash
#!/bin/bash
# Update system
yum update -y  # For Amazon Linux
# OR: apt-get update && apt-get upgrade -y  # For Ubuntu

# Install Docker
yum install -y docker  # For Amazon Linux
# OR: apt-get install -y docker.io  # For Ubuntu
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user  # For Amazon Linux
# OR: usermod -a -G docker ubuntu  # For Ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI (if not pre-installed)
yum install -y aws-cli  # For Amazon Linux
# OR: apt-get install -y awscli  # For Ubuntu

# Configure AWS CLI (you'll need to do this manually or use IAM roles)
# aws configure

# Create directory for application
mkdir -p /home/ec2-user/deep-research
chown ec2-user:ec2-user /home/ec2-user/deep-research
```

   **h. Review and Launch:**
   - Scroll to the bottom and click **"Launch Instance"**
   - You'll see a confirmation page
   - Click **"View all instances"** or **"View instance"**

5. **Wait for Instance to Start:**
   - In the EC2 Instances page, you'll see your instance
   - **Instance State:** Will show "Pending" → then "Running" (takes 1-2 minutes)
   - **Status Checks:** Will show "Initializing" → then "2/2 checks passed"

6. **Get Your Instance Details:**
   - Click on your instance to select it
   - In the details panel below, find:
     - **Public IPv4 address:** This is your `EC2_HOST` (copy this!)
     - **Public IPv4 DNS:** Alternative hostname (you can use this too)
     - **Instance ID:** Note this for reference

**✅ EC2 Instance is now running!**

**📝 Note:** You'll need the Public IPv4 address for the `EC2_HOST` GitHub secret in Step 2.

### 1.3 Configure EC2 IAM Role (Recommended)

**📍 WHERE:** AWS Console → IAM Service

**⏱️ WHEN:** One-time setup (do this after creating EC2 instance)

**🔧 WHAT:** IAM role allows EC2 to access ECR (to pull Docker images) without storing credentials

#### Step-by-Step: Create IAM Role

1. **Go to IAM Console:**
   - In AWS Console search bar, type "IAM"
   - Click on **"IAM"** service

2. **Create Role:**
   - In the left sidebar, click **"Roles"**
   - Click the orange **"Create role"** button (top right)

3. **Select Trusted Entity:**
   - Under **"Trusted entity type"**, select **"AWS service"**
   - Under **"Use case"**, select **"EC2"**
   - Click **"Next"**

4. **Add Permissions:**
   - In the search box, type "ECR"
   - Check the box next to **"AmazonEC2ContainerRegistryReadOnly"**
   - This allows EC2 to pull images from ECR
   - Click **"Next"**

5. **Name the Role:**
   - **Role name:** Enter `ec2-ecr-access-role` (or any name you prefer)
   - **Description:** `Allows EC2 to pull images from ECR`
   - Click **"Create role"**

6. **Add ECR Login Permission (Optional but Recommended):**
   - Click on the role you just created
   - Click **"Add permissions"** → **"Create inline policy"**
   - Click **"JSON"** tab
   - Paste this policy:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ecr:GetAuthorizationToken"
         ],
         "Resource": "*"
       }
     ]
   }
   ```
   - Click **"Next"**
   - **Policy name:** `ECRLoginPolicy`
   - Click **"Create policy"**

7. **Attach Role to EC2 Instance:**
   - Go back to **EC2 Console** → **Instances**
   - Select your EC2 instance
   - Click **"Actions"** button (top right) → **"Security"** → **"Modify IAM role"**
   - Under **"IAM role"**, select the role you just created (`ec2-ecr-access-role`)
   - Click **"Update IAM role"**

**✅ IAM Role is now attached to your EC2 instance!**

**📝 Note:** With this role, your EC2 instance can pull Docker images from ECR without needing AWS credentials stored on the instance.

### 1.4 Set Up Redis (ElastiCache)

**📍 WHERE:** AWS Console → ElastiCache Service

**⏱️ WHEN:** One-time setup

**🔧 WHAT:** Create a managed Redis cache for your application

**⚠️ IMPORTANT:** You have two options:
- **Option A:** Use ElastiCache (managed Redis) - Better for production, costs money (~$15/month)
- **Option B:** Use local Redis container in docker-compose - Free, simpler setup

**For this guide, we'll show Option A (ElastiCache).** If you prefer Option B, skip this step and use `deep_research/deployment/docker-compose.aws.yml` which includes a Redis container.

**📝 Note:** In the ElastiCache console, you'll see three cache types:
- **Valkey caches** - Newer fork of Redis (recommended for new deployments)
- **Redis OSS caches** - Original Redis open-source (also works fine)
- **Memcached caches** - Different caching engine (not compatible with Redis)

For this guide, we'll use **Redis OSS caches**, but **Valkey caches** will work the same way.

#### Step-by-Step: Create ElastiCache Redis

1. **Go to ElastiCache Console:**
   - In AWS Console search bar, type "ElastiCache"
   - Click on **"ElastiCache"** service

2. **Create Subnet Group (First Time Only):**
   - In the left sidebar, click **"Subnet groups"**
   - Click **"Create subnet group"** button
   - **Name:** `langgraph-redis-subnet`
   - **Description:** `Subnet group for LangGraph Redis`
   - **VPC:** Select your default VPC (or the VPC where your EC2 is)
   - **Subnets:** Select at least 2 subnets (ElastiCache requires multiple subnets for high availability)
     - To find your subnets: Go to VPC Console → Subnets
     - Select subnets from different Availability Zones (e.g., `us-east-1a` and `us-east-1b`)
   - Click **"Create"**

3. **Create Security Group for Redis:**
   - Go to **VPC Console** (search "VPC" in AWS Console)
   - Click **"Security Groups"** in left sidebar
   - Click **"Create security group"**
   - **Name:** `redis-sg`
   - **Description:** `Security group for Redis cache`
   - **VPC:** Select same VPC as your EC2 instance
   - **Inbound rules:** Add rule:
     - **Type:** Custom TCP
     - **Port:** 6379
     - **Source:** Select the security group of your EC2 instance (e.g., `deep-research-sg`)
       - This allows only your EC2 to access Redis
   - **Outbound rules:** Leave default
   - Click **"Create security group"**
   - **Note the Security Group ID** (e.g., `sg-0123456789abcdef0`)

4. **Create Redis Cache:**
   - Go back to **ElastiCache Console**
   - In the left sidebar, under **"Resources"**, click **"Redis OSS caches"** (or **"Valkey caches"** if you prefer Valkey)
   - Click **"Create Redis cache"** button (or **"Create Valkey cache"** if using Valkey)
   - **Note:** Valkey is a newer fork of Redis with similar compatibility. Both work for this use case.

5. **Configure Redis Cache:**
   
   **a. Engine Selection:**
   - **Engine:** Select **"Redis OSS"** (or **"Valkey - recommended"** for 20-33% cost savings)
   - Both work identically for this use case
   
   **b. Deployment Option:**
   - **Deployment option:** Select **"Node-based cluster"** (not Serverless)
   
   **c. Creation Method:**
   - **Creation method:** Select **"Easy create"** (recommended for simplicity)
   
   **d. Configuration Preset:**
   - **For testing/development:** Select **"Demo"** (uses `cache.t4g.micro`, ~$10-15/month)
   - **For production:** Select **"Dev/Test"** (uses `cache.r7g.large`, ~$50-70/month) or **"Production"** (uses `cache.r7g.xlarge`, ~$100-150/month)
   - **⚠️ IMPORTANT:** Start with **"Demo"** or **"Dev/Test"** for initial setup - you can scale up later if needed
   - The **"Production"** preset uses `cache.r7g.xlarge` (26.32 GiB) which is expensive and likely overkill
   
   **e. Cache Settings (if using Easy create, you can modify these after creation):**
   - **Name:** `langgraph-redis`
   - **Description:** `Redis cache for LangGraph deep research agent`
   - **Engine version:** Select the latest Redis version (or Valkey version if using Valkey)

   **f. Location:**
   - **Region:** Select your region (e.g., `us-east-1`)
   - **Availability Zone:** Select any zone (e.g., `us-east-1a`)

   **g. Network Settings:**
   - **VPC:** Select same VPC as your EC2 instance
   - **Subnet group:** Select `langgraph-redis-subnet` (created in step 2)
   - **Security groups:** Select `redis-sg` (created in step 3)
   - **Availability Zone:** Select any zone
   
   **h. Replicas (if not using Easy create):**
   - **Number of replicas:** 0 (for cost savings, or 1 for high availability)

   **i. Encryption and Backup (Optional):**
   - **Encryption:** Can leave default (encryption at rest is optional for testing)
   - **Backup:** Can disable for cost savings, or enable for production

   **j. Maintenance:**
   - **Maintenance window:** Leave default or customize

6. **Review and Create:**
   - Review all settings
   - Click **"Create"** button
   - Wait for cache to be created (takes 5-10 minutes)
   - Status will show "Creating" → "Available"

7. **Get Redis Endpoint:**
   - Once status is "Available", click on your cache name in the list
   - In the details panel, find **"Primary endpoint"** or **"Configuration endpoint"**
   - Copy the endpoint (format: `langgraph-redis.xxxxx.cache.amazonaws.com:6379`)
   - **⚠️ IMPORTANT:** You'll need this for the `REDIS_URI` GitHub secret
   - The format for `REDIS_URI` is: `redis://langgraph-redis.xxxxx.cache.amazonaws.com:6379`
   - **Note:** The endpoint may not include the port number in the console - add `:6379` when creating the `REDIS_URI`

**✅ ElastiCache Redis is now set up!**

**📝 Note:** 
- The Redis endpoint will be something like: `langgraph-redis.xxxxx.cache.amazonaws.com`
- Use this in your `REDIS_URI` secret as: `redis://langgraph-redis.xxxxx.cache.amazonaws.com:6379`
- Make sure your EC2 security group allows outbound traffic to the Redis security group

#### Alternative: Using Local Redis Container (Free Option)

If you don't want to set up ElastiCache, you can use the local Redis container included in `deep_research/deployment/docker-compose.aws.yml`:
- No additional AWS setup needed
- Redis runs in a Docker container on your EC2 instance
- Free (no ElastiCache costs)
- Use `REDIS_URI=redis://redis:6379` in your GitHub secrets
- This is fine for development and small deployments

## Step 2: Configure GitHub Secrets

**📍 WHERE:** GitHub Repository → Settings → Secrets and variables → Actions

**⏱️ WHEN:** One-time setup (do this once, secrets persist)

**🔐 WHAT:** These secrets store your API keys, credentials, and configuration. They are encrypted and only accessible to GitHub Actions workflows.

### How to Add Secrets (Step-by-Step)

1. **Navigate to your GitHub repository** in a web browser
2. Click on the **"Settings"** tab (top navigation bar)
3. In the left sidebar, click **"Secrets and variables"**
4. Click **"Actions"** (under Secrets and variables)
5. Click the **"New repository secret"** button (green button, top right)
6. Enter the secret **Name** (exactly as shown below)
7. Enter the secret **Value** (paste your actual key/credential)
8. Click **"Add secret"**
9. Repeat for each secret listed below

### Secrets to Add

### AWS Credentials

**📍 WHERE TO GET THESE:**
1. Log in to AWS Console: https://console.aws.amazon.com
2. Click your username (top right) → **"Security credentials"**
3. Scroll to **"Access keys"** section
4. Click **"Create access key"**
5. Choose **"Command Line Interface (CLI)"** or **"Application running outside AWS"**
6. Copy the **Access key ID** and **Secret access key** (you'll only see the secret once!)

**⚠️ IMPORTANT:** Save these securely - you won't be able to see the secret key again!

- **Secret Name:** `AWS_ACCESS_KEY_ID`
  - **Value:** Your AWS access key ID (e.g., `AKIAIOSFODNN7EXAMPLE`)
  
- **Secret Name:** `AWS_SECRET_ACCESS_KEY`
  - **Value:** Your AWS secret access key (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

### EC2 Connection

**📍 WHERE TO GET THESE:**

**EC2_HOST:**
1. Go to AWS Console → **EC2** → **Instances**
2. Select your EC2 instance
3. In the details panel, find **"Public IPv4 address"** or **"Public IPv4 DNS"**
4. Copy either the IP address (e.g., `54.123.45.67`) or DNS name (e.g., `ec2-54-123-45-67.compute-1.amazonaws.com`)

**EC2_USER:**
- For **Amazon Linux**: Use `ec2-user`
- For **Ubuntu**: Use `ubuntu`
- For **Debian**: Use `admin`
- Check your AMI documentation if unsure

**EC2_SSH_PRIVATE_KEY:**
- This is the private key you'll generate in Step 3
- For now, you can skip this and come back after Step 3

- **Secret Name:** `EC2_HOST`
  - **Value:** Your EC2 instance public IP or DNS (e.g., `ec2-54-123-45-67.compute-1.amazonaws.com` or `54.123.45.67`)
  
- **Secret Name:** `EC2_USER`
  - **Value:** `ec2-user` (for Amazon Linux) or `ubuntu` (for Ubuntu)
  
- **Secret Name:** `EC2_SSH_PRIVATE_KEY`
  - **Value:** Your SSH private key (complete content from Step 3, including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`)
  - **⚠️ IMPORTANT:** Copy the ENTIRE key, including the header and footer lines

### Database & Services

**📍 WHERE TO GET POSTGRES_URI (Supabase):**
1. Go to your Supabase project: https://supabase.com/dashboard
2. Select your project
3. Go to **"Settings"** → **"Database"**
4. Scroll to **"Connection string"** section
5. Select **"Connection pooling"** tab
6. Copy the **"URI"** connection string (starts with `postgresql://`)
7. Replace `[YOUR-PASSWORD]` with your actual database password

**Example format:**
```
postgresql://postgres.ltbwpsjgivrwxoevnolj:your_password@aws-1-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require
```

**📍 WHERE TO GET REDIS_URI:**
- **If using ElastiCache:** See Step 1.4 for how to get the endpoint
- **If using local Redis container:** Use `redis://redis:6379` (already configured in docker-compose)

- **Secret Name:** `POSTGRES_URI`
  - **Value:** Your complete PostgreSQL connection string
  - **Example:** `postgresql://postgres.xxxxx:password@aws-1-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require`
  
- **Secret Name:** `REDIS_URI`
  - **Value:** Your Redis connection string
  - **ElastiCache example:** `redis://langgraph-redis.xxxxx.cache.amazonaws.com:6379`
  - **Local Redis example:** `redis://redis:6379` (if using docker-compose with local Redis)

### API Keys (Required)

**📍 WHERE TO GET LANGSMITH_API_KEY:**
1. Go to LangSmith: https://smith.langchain.com
2. Sign in or create an account
3. Click your profile icon (top right) → **"Settings"**
4. Go to **"API Keys"** section
5. Click **"Create API Key"**
6. Copy the key (starts with `lsv2_pt_...` or similar)
7. **⚠️ IMPORTANT:** Save it immediately - you won't see it again!

**📍 WHERE TO GET OPENAI_API_KEY:**
1. Go to OpenAI: https://platform.openai.com
2. Sign in or create an account
3. Click your profile icon → **"API keys"**
4. Click **"Create new secret key"**
5. Give it a name (e.g., "GitHub Actions Deployment")
6. Copy the key (starts with `sk-...`)
7. **⚠️ IMPORTANT:** Save it immediately - you won't see it again!

**📍 WHERE TO GET TAVILY_API_KEY:**
1. Go to Tavily: https://tavily.com
2. Sign in or create an account
3. Go to **"API Keys"** section in dashboard
4. Click **"Create API Key"** or copy existing key
5. Copy the key

- **Secret Name:** `LANGSMITH_API_KEY`
  - **Value:** Your LangSmith API key (e.g., `lsv2_pt_abc123def456...`)
  
- **Secret Name:** `OPENAI_API_KEY`
  - **Value:** Your OpenAI API key (e.g., `sk-proj-abc123def456...`)
  
- **Secret Name:** `TAVILY_API_KEY`
  - **Value:** Your Tavily API key

### API Keys (Optional - Only add if you use these services)

**📍 WHERE TO GET ANTHROPIC_API_KEY:**
1. Go to Anthropic Console: https://console.anthropic.com
2. Sign in or create an account
3. Go to **"API Keys"** section
4. Click **"Create Key"**
5. Copy the key (starts with `sk-ant-...`)

**📍 WHERE TO GET LANGGRAPH_CLOUD_LICENSE_KEY:**
- This is an enterprise license key from LangGraph
- Only needed if you have an enterprise license (alternative to LANGSMITH_API_KEY)
- Contact LangGraph sales if you need this

- **Secret Name:** `ANTHROPIC_API_KEY` (optional)
  - **Value:** Your Anthropic API key (only if using Claude models)
  
- **Secret Name:** `LANGGRAPH_CLOUD_LICENSE_KEY` (optional)
  - **Value:** Your enterprise license key (only if you have one)

### Application Configuration

**📍 WHERE TO GET THESE:**
These are fixed configuration values for your application. Copy them exactly as shown:

- **Secret Name:** `LANGGRAPH_AUTH`
  - **Value:** `{"path": "/api/security/auth.py:auth"}`
  - **⚠️ IMPORTANT:** Copy exactly, including the curly braces and quotes

- **Secret Name:** `LANGGRAPH_HTTP`
  - **Value:** `{"app": "/api/webapp_advanced.py:app"}`
  - **⚠️ IMPORTANT:** Copy exactly, including the curly braces and quotes

### Supabase Authentication (Required if using auth.py)

**📍 WHERE TO GET SUPABASE_URL:**
1. Go to your Supabase project: https://supabase.com/dashboard
2. Select your project
3. Go to **"Settings"** → **"API"**
4. Find **"Project URL"** (starts with `https://`)
5. Copy the complete URL

**📍 WHERE TO GET SUPABASE_SERVICE_KEY:**
1. In the same **"Settings"** → **"API"** page
2. Find **"Project API keys"** section
3. Look for **"service_role"** key (⚠️ NOT the anon key!)
4. Click **"Reveal"** to show the key
5. Copy the complete key
6. **⚠️ SECURITY WARNING:** This key has admin access - keep it secret!

- **Secret Name:** `SUPABASE_URL`
  - **Value:** Your Supabase project URL (e.g., `https://xxxxx.supabase.co`)
  
- **Secret Name:** `SUPABASE_SERVICE_KEY`
  - **Value:** Your Supabase service role key (the long key starting with `eyJ...`)

## Step 3: Generate SSH Key Pair for EC2

**⏱️ WHEN:** One-time setup (do this once)

**📍 WHERE:** Run these commands on your local machine (terminal/command prompt)

**🔐 WHAT:** This creates an SSH key that GitHub Actions will use to connect to your EC2 instance for deployment.

### Step-by-Step Instructions

1. **Open a terminal** on your local computer (Mac/Linux/WSL)

2. **Generate the SSH key pair:**
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key
   ```
   - When prompted for a passphrase, you can press Enter (no passphrase needed for automation)
   - This creates two files:
     - `~/.ssh/github_deploy_key` (private key - keep secret!)
     - `~/.ssh/github_deploy_key.pub` (public key - safe to share)

3. **Copy the public key to your EC2 instance:**
   - You need the `.pem` file that was generated before
   - You can test if you can login to the EC2 instance using the pem file by running the command below
   ```bash
   ssh -i ~/Downloads/deep-research-key.pem ec2-user@YOUR_EC2_HOST
   ```
   - If that works then you can copy the public key using the following command
   ```bash
   ssh-copy-id -i ~/.ssh/github_deploy_key.pub -o "IdentityFile=~/Downloads/deep-research-key.pem" ec2-user@YOUR_EC2_HOST
   ```
   - Replace `ec2-user` with your EC2 username (`ubuntu` for Ubuntu, `ec2-user` for Amazon Linux)
   - Replace `YOUR_EC2_HOST` with your EC2 public IP or DNS name
   - You'll be prompted for your EC2 password or existing SSH key
   **⚠️ IMPORTANT:** 
   - If you get a warning that key already exist but it's first time trying just add a `-f` to the command. so `ssh-copy-id -f -i ...`

4. **Display the private key to copy to GitHub:**
   ```bash
   cat ~/.ssh/github_deploy_key
   ```
   - This will show the complete private key
   - **Copy the ENTIRE output**, including:
     - `-----BEGIN RSA PRIVATE KEY-----`
     - All the key content in between
     - `-----END RSA PRIVATE KEY-----`

5. **Add the private key to GitHub Secrets:**
   - Go back to GitHub → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - **Name:** `EC2_SSH_PRIVATE_KEY`
   - **Value:** Paste the ENTIRE private key you just copied
   - Click "Add secret"

**⚠️ IMPORTANT:** 
- Never share your private key (`github_deploy_key`) publicly
- The private key should only be in GitHub Secrets
- Keep the public key (`github_deploy_key.pub`) - you may need it later

## Step 4: Push Workflow File to Repository

**⏱️ WHEN:** One-time setup (do this once)

**📍 WHERE:** Your local repository, then push to GitHub

**🤖 WHAT:** The workflow file must be in `.github/workflows/deploy-aws.yml` at the **repository root**. The repository root is `deepagents-quickstarts/`, so the workflow should be at `deepagents-quickstarts/.github/workflows/deploy-aws.yml`. GitHub Actions only detects workflows in the root `.github/workflows/` directory.

### Step-by-Step Instructions

1. **Verify the workflow file exists:**
   - **Repository Root:** `deepagents-quickstarts/`
   - The workflow file should be at: `deepagents-quickstarts/.github/workflows/deploy-aws.yml`
   - **⚠️ IMPORTANT:** GitHub Actions will NOT detect workflows in subdirectories like `deep_research/.github/workflows/`
   - GitHub Actions only looks for workflows in the repository root `.github/workflows/` directory
   - The file is already in the correct location and ready to use

2. **Choose your Docker Compose file:**
   - **Option A:** `deep_research/deployment/docker-compose.aws.yml` - Uses local Redis container (good for testing)
   - **Option B:** `deep_research/deployment/docker-compose.aws-production.yml` - Uses ElastiCache Redis (better for production)
   - The workflow is configured for Option A by default
   - If you want Option B, edit `.github/workflows/deploy-aws.yml` and change the `scp` command to use `deep_research/deployment/docker-compose.aws-production.yml`

3. **Commit and push the workflow file:**
   ```bash
   # Navigate to repository root (deepagents-quickstarts/)
   cd .  # If already in repository root
   # OR if in a subdirectory:
   # cd ../..  # Adjust based on your current location
   git add .github/workflows/deploy-aws.yml
   git commit -m "Add GitHub Actions workflow for AWS deployment"
   git push origin main
   ```
   (Replace `main` with `master` if that's your default branch)
   
   **📝 Note:** 
   - The workflow file must be in `.github/workflows/` at the repository root (`deepagents-quickstarts/.github/workflows/`)
   - The docker-compose files remain in `deep_research/deployment/` directory
   - All paths in the workflow are relative to the repository root

**✅ After this step:** The workflow is now active and will run automatically on every push!

## Step 5: Test the Workflow (First Deployment)

**⏱️ WHEN:** One-time test after initial setup, then automatic on every push

**📍 WHERE:** GitHub repository → Actions tab

**🤖 WHAT:** Trigger the workflow manually or push code to test the deployment

### Option A: Manual Trigger (Recommended for First Test)

1. **Go to your GitHub repository** in a web browser
2. Click on the **"Actions"** tab (top navigation bar)
3. In the left sidebar, you should see **"Deploy to AWS"** workflow
4. Click on **"Deploy to AWS"**
5. Click the **"Run workflow"** button (top right, dropdown)
6. Select your branch (usually `main` or `master`)
7. Click the green **"Run workflow"** button
8. Watch the workflow run in real-time
9. Check each step for success/failure

### Option B: Automatic Trigger (After First Test)

1. **Make any change** to your code (or just add a comment)
2. **Commit and push:**
   ```bash
   git add .
   git commit -m "Test deployment"
   git push origin main
   ```
3. **Go to Actions tab** in GitHub
4. You'll see a new workflow run automatically started
5. Watch it deploy automatically!

**✅ After successful deployment:** Every time you push to main/master, deployment happens automatically - no manual steps needed!

## Step 6: Verify Deployment

**⏱️ WHEN:** After first deployment, or whenever you want to check status

**📍 WHERE:** SSH into your EC2 instance

**🔍 WHAT:** Verify that containers are running and the service is healthy

### Step-by-Step Verification

1. **SSH into your EC2 instance:**
   ```bash
   ssh -i ~/.ssh/github_deploy_key ec2-user@YOUR_EC2_HOST
   ```
   - Replace `ec2-user` with your EC2 username
   - Replace `YOUR_EC2_HOST` with your EC2 public IP or DNS

2. **Check if containers are running:**
   ```bash
   docker-compose -f docker-compose.aws.yml ps
   ```
   - You should see `langgraph-api` (and `redis` if using local Redis) with status "Up"

3. **Check container logs:**
   ```bash
   docker-compose -f docker-compose.aws.yml logs -f langgraph-api
   ```
   - Press `Ctrl+C` to exit log viewing
   - Look for any error messages

4. **Test the health endpoint:**
   ```bash
   curl http://localhost:8123/docs
   ```
   - Should return HTML (the API documentation page)
   - If you get a response, the service is working!

5. **Test from outside EC2:**
   - Open a browser and go to: `http://YOUR_EC2_PUBLIC_IP:8123/docs`
   - Replace `YOUR_EC2_PUBLIC_IP` with your actual EC2 public IP
   - You should see the API documentation page

**✅ Success indicators:**
- Containers show status "Up"
- No errors in logs
- Health endpoint responds
- API docs accessible from browser

## 🎉 Setup Complete!

**Congratulations!** Your CI/CD pipeline is now set up. Here's what happens now:

### ✅ What's Automated (No Action Needed)

Every time you push code to the `main` or `master` branch:
1. ✅ GitHub Actions automatically detects the push
2. ✅ Builds your Docker image
3. ✅ Pushes to Amazon ECR
4. ✅ Deploys to EC2 automatically
5. ✅ Verifies deployment health

**You don't need to do anything manually for deployments!**

### 🔄 How to Deploy Updates

**Simple:** Just push your code!
```bash
git add .
git commit -m "Your changes"
git push origin main
```

The deployment happens automatically in the background. Check the **Actions** tab in GitHub to see the progress.

### 🛑 Manual Deployment (If Needed)

If you want to trigger a deployment manually without pushing code:
1. Go to GitHub → **Actions** tab
2. Click **"Deploy to AWS"** workflow
3. Click **"Run workflow"** button
4. Select branch and click **"Run workflow"**

## Troubleshooting

### Workflow Fails at ECR Login

- Verify AWS credentials are correct
- Check IAM permissions for ECR access
- Ensure ECR repository exists in the correct region

### Workflow Fails at SSH Connection

- Verify EC2_HOST is correct (use public IP or public DNS)
- Check security group allows SSH from GitHub Actions IPs
- Verify SSH private key is correctly formatted in secrets
- Test SSH connection manually: `ssh -i ~/.ssh/github_deploy_key ec2-user@YOUR_EC2_HOST`

### Deployment Fails on EC2

- Check EC2 instance has Docker and Docker Compose installed
- Verify IAM role allows ECR pull access
- Check EC2 security group allows necessary ports
- Review EC2 logs: `journalctl -u docker` or `docker logs`

### Container Won't Start

- Verify all environment variables are set correctly
- Check Redis is accessible from EC2 (security groups)
- Check PostgreSQL connection string is correct
- Review container logs: `docker-compose -f docker-compose.aws.yml logs langgraph-api`
  - **Note:** Run this on your EC2 instance where the containers are running

### Health Check Fails

- Wait longer (service may need more time to start)
- Check if port 8000 is accessible inside container
- Verify the health check endpoint exists: `/docs`

## Security Best Practices

1. **Use IAM Roles**: Prefer IAM roles over access keys when possible
2. **Rotate Secrets**: Regularly rotate API keys and credentials
3. **Limit SSH Access**: Restrict SSH access to specific IPs in security groups
4. **Use Secrets Manager**: Consider using AWS Secrets Manager instead of GitHub Secrets for sensitive data
5. **Enable ECR Image Scanning**: Already enabled in the ECR creation command
6. **Use Private Subnets**: Deploy EC2 in private subnets with NAT gateway for better security
7. **Enable VPC Flow Logs**: Monitor network traffic

## Advanced Configuration

### Using AWS Secrets Manager

Instead of storing secrets in GitHub, you can use AWS Secrets Manager:

1. Store secrets in AWS Secrets Manager
2. Update the workflow to fetch secrets from AWS
3. Use IAM role with Secrets Manager read permissions

### Using ECS Instead of EC2

For better scalability, consider using AWS ECS:
- Create ECS task definition
- Use ECS service instead of EC2
- Update workflow to deploy to ECS instead

### Multi-Environment Deployment

Create separate workflows for staging and production:
- `.github/workflows/deploy-staging.yml` (at repository root: `deepagents-quickstarts/.github/workflows/`)
- `.github/workflows/deploy-production.yml` (at repository root: `deepagents-quickstarts/.github/workflows/`)
- Use different secrets for each environment

## Workflow Customization

The workflow file (`.github/workflows/deploy-aws.yml` at repository root: `deepagents-quickstarts/.github/workflows/deploy-aws.yml`) can be customized:

- **Change trigger branches**: Modify `on.push.branches`
- **Add manual approval**: Use GitHub Environments with required reviewers
- **Add notifications**: Add Slack/email notifications on success/failure
- **Add rollback**: Implement automatic rollback on health check failure

## Monitoring

Set up monitoring for your deployment:

1. **CloudWatch Logs**: Forward Docker logs to CloudWatch
2. **CloudWatch Alarms**: Set up alarms for service health
3. **GitHub Actions Status**: Monitor workflow success/failure
4. **Application Monitoring**: Use application-level monitoring tools

## Cost Optimization

1. **Use Spot Instances**: For non-critical deployments
2. **Right-size Instances**: Monitor and adjust instance sizes
3. **Auto-scaling**: Implement auto-scaling based on load
4. **Reserved Instances**: For predictable workloads

## Next Steps

1. Set up monitoring and alerting
2. Configure backup strategies
3. Implement blue-green deployments
4. Set up staging environment
5. Configure custom domain and SSL certificate

