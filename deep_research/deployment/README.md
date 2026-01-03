# Deployment Guides

This directory contains comprehensive deployment guides for the Deep Agents project.

## 📍 Important: Repository Structure

**Repository Root:** `deepagents-quickstarts/`

All paths in these guides are relative to the repository root (`deepagents-quickstarts/`):
- Workflows: `deepagents-quickstarts/.github/workflows/`
- Deployment files: `deepagents-quickstarts/deep_research/deployment/`
- Terraform: `deepagents-quickstarts/deep_research/deployment/terraform/`

## 📚 Available Guides

### Backend Deployment

**[AWS Backend Deployment](./AWS_BACKEND_DEPLOYMENT.md)**
- Complete guide for deploying the LangGraph backend to AWS using GitHub Actions CI/CD
- Includes setup for EC2, ECR, ElastiCache, and IAM roles
- Step-by-step instructions with exact locations and commands
- One-time setup vs automated deployment clearly explained

### Frontend Deployment

**[Vercel Frontend Deployment](./VERCEL_FRONTEND_DEPLOYMENT.md)**
- Complete guide for deploying the Next.js frontend to Vercel
- Automatic CI/CD with GitHub integration
- Environment variable configuration
- Step-by-step instructions with screenshots descriptions

### Infrastructure as Code

**[Terraform Infrastructure Deployment](./TERRAFORM_DEPLOYMENT.md)**
- Automate AWS infrastructure provisioning with Terraform
- Creates EC2, ECR, ElastiCache, IAM roles, and security groups automatically
- Step-by-step guide for setup and deployment
- Cost optimization and best practices

## 🚀 Quick Start

### Option A: Manual Setup (Step-by-Step)

1. **Deploy Backend Infrastructure:**
   - Follow [AWS Backend Deployment](./AWS_BACKEND_DEPLOYMENT.md) for manual setup
   - OR use [Terraform Infrastructure Deployment](./TERRAFORM_DEPLOYMENT.md) for automated setup
   - Get your backend URL (e.g., `http://your-ec2-ip:8123`)

2. **Deploy Frontend:**
   - Follow [Vercel Frontend Deployment](./VERCEL_FRONTEND_DEPLOYMENT.md)
   - Configure the frontend to connect to your backend URL

### Option B: Automated Infrastructure (Recommended)

1. **Use Terraform to create infrastructure:**
   - Follow [Terraform Infrastructure Deployment](./TERRAFORM_DEPLOYMENT.md)
   - This automates all AWS resource creation

2. **Deploy application:**
   - GitHub Actions will automatically deploy on code push
   - Frontend deploys automatically via Vercel

## 📝 Important Notes

- Both guides assume your code is in a GitHub repository
- Backend deployment requires AWS account and EC2 instance
- Frontend deployment requires Vercel account (free tier available)
- **Repository Root:** `deepagents-quickstarts/`
- All paths in the guides are relative to the repository root (`deepagents-quickstarts/`)
- Workflows must be at: `deepagents-quickstarts/.github/workflows/`

## 📁 Directory Structure

This `deployment/` directory contains:

```
deployment/
├── README.md                              # This file
├── AWS_BACKEND_DEPLOYMENT.md              # Backend deployment guide
├── VERCEL_FRONTEND_DEPLOYMENT.md         # Frontend deployment guide
├── docker-compose.aws.yml                 # Docker Compose for AWS (local Redis)
└── docker-compose.aws-production.yml      # Docker Compose for AWS (ElastiCache)
```

**GitHub Actions Workflows** (in repository root `deepagents-quickstarts/.github/workflows/`):
- `.github/workflows/deploy-aws.yml` - GitHub Actions workflow for AWS backend
- `.github/workflows/deploy-vercel.yml` - GitHub Actions workflow for Vercel frontend (optional)

## 🔗 Related Files

**Backend Files:**
- `.github/workflows/deploy-aws.yml` - GitHub Actions workflow for AWS (at repository root: `deepagents-quickstarts/.github/workflows/`)
- `deep_research/deployment/docker-compose.aws.yml` - Docker Compose for AWS (local Redis)
- `deep_research/deployment/docker-compose.aws-production.yml` - Docker Compose for AWS (ElastiCache)
- `deep_research/deployment/terraform/` - Terraform infrastructure as code

**Frontend Files:**
- `.github/workflows/deploy-vercel.yml` - Optional GitHub Actions workflow for Vercel (at repository root: `deepagents-quickstarts/.github/workflows/`)
- `deep-agents-ui/` - Next.js frontend application (if in this repository)

**Frontend Files (in repository root):**
- `deep-agents-ui/` - Next.js frontend application
- `deep-agents-ui/package.json` - Frontend dependencies

**⚠️ CRITICAL - Workflow File Location:**
- **Repository Root:** The repository root is `deepagents-quickstarts/`
- GitHub Actions **ONLY** detects workflows in the repository root `.github/workflows/` directory
- Workflows must be at: `deepagents-quickstarts/.github/workflows/` (relative to repository root)
- Workflows in subdirectories (like `deep_research/.github/workflows/`) will **NOT** be detected
- Both workflow files must be in `.github/workflows/` at the repository root (`deepagents-quickstarts/.github/workflows/`)
- The AWS workflow is required for backend deployments
- The Vercel workflow is optional. Vercel has built-in CI/CD that works automatically when you connect your GitHub repo. Only use the GitHub Actions workflow if you need custom build steps or more control.

## 🆘 Need Help?

- Check the troubleshooting sections in each guide
- Review the "Common Issues" sections
- Verify all prerequisites are met
- Ensure environment variables are correctly set

