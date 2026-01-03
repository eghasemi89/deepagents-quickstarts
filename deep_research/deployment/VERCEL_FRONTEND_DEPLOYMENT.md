# Vercel Deployment Guide for Deep Agents UI

This guide will help you deploy your Next.js frontend application to Vercel with automatic CI/CD.

## 🎯 One-Time Setup vs Automated Deployment

### ✅ ONE-TIME SETUP (Do this once)
These steps are done **once** during initial setup. After completing them, you won't need to repeat them:

| Step | What | Where | Time Required |
|------|------|-------|---------------|
| 0 | Create Vercel account | vercel.com | 2 minutes |
| 1 | Connect GitHub repository | Vercel Dashboard | 5 minutes |
| 2 | Configure project settings | Vercel Dashboard | 5 minutes |
| 3 | Add environment variables | Vercel Dashboard → Settings | 10 minutes |
| 4 | Deploy (automatic) | Vercel (automatic) | 5-10 minutes |

**Total one-time setup:** ~30 minutes

### 🤖 AUTOMATED (Happens automatically after setup)
Once setup is complete, these happen **automatically** every time you push code:

| Action | When | How |
|--------|------|-----|
| Build Next.js app | On every push to main/master | Vercel automatically |
| Run tests/linting | During build | Vercel automatically |
| Deploy to production | After successful build | Vercel automatically |
| Generate preview URLs | On pull requests | Vercel automatically |

**You do NOT need to do anything manually for each deployment** - just push your code!

### 📝 Quick Answer: Do I Have to Do This Every Time?

**NO!** Here's the breakdown:

- **One-time setup:** ~30 minutes (Steps 0-4) - Do this once
- **Each deployment:** 0 minutes - Just push code, deployment is automatic
- **Manual deployment:** Optional - Can trigger manually from Vercel Dashboard if needed

**After setup, deploying is as simple as:**
```bash
git push origin main
```

That's it! The rest happens automatically.

## 📋 Quick Start Checklist

### One-Time Setup (Do Once)
- [ ] **Step 0:** Create Vercel account
- [ ] **Step 1:** Connect GitHub repository to Vercel
- [ ] **Step 2:** Configure project settings (framework, build settings)
- [ ] **Step 3:** Add environment variables (API keys, configuration)
- [ ] **Step 4:** First deployment (automatic)
- [ ] **Step 5:** Verify deployment and get your live URL

## Prerequisites

1. **GitHub Account** with your repository
2. **Vercel Account** (free tier is sufficient)
3. **Your backend API URL** (the LangGraph deployment URL)
4. **Optional:** Supabase credentials (if using authentication)
5. **Optional:** LangSmith API key (if required by your backend)

## Step 0: Create Vercel Account

**📍 WHERE:** vercel.com

**⏱️ WHEN:** One-time setup (do this first)

**🔧 WHAT:** Create a free Vercel account to host your frontend

### Step-by-Step Instructions

1. **Go to Vercel:**
   - Open: https://vercel.com
   - Click **"Sign Up"** button (top right)

2. **Sign Up Options:**
   - **Recommended:** Click **"Continue with GitHub"** (easiest, connects directly to your GitHub)
   - **Alternative:** Sign up with email, then connect GitHub later

3. **Authorize Vercel:**
   - If using GitHub, you'll be asked to authorize Vercel
   - Click **"Authorize Vercel"** or **"Install"**
   - You can choose to authorize all repositories or select specific ones

4. **Complete Profile:**
   - Fill in your name (optional)
   - Choose your team name (or use personal account)
   - Click **"Continue"**

**✅ Vercel account is now created!**

**📝 Note:** Vercel's free tier includes:
- Unlimited deployments
- Automatic SSL certificates
- Global CDN
- Preview deployments for pull requests
- 100GB bandwidth per month

## Step 1: Connect GitHub Repository

**📍 WHERE:** Vercel Dashboard

**⏱️ WHEN:** One-time setup

**🔧 WHAT:** Connect your GitHub repository so Vercel can deploy it automatically

### Step-by-Step Instructions

1. **Go to Vercel Dashboard:**
   - After signing up, you'll be on the Vercel Dashboard
   - Or go to: https://vercel.com/dashboard

2. **Add New Project:**
   - Click the **"Add New..."** button (top right)
   - Select **"Project"** from the dropdown

3. **Import Repository:**
   - You'll see a list of your GitHub repositories
   - **Search for your repository:** Type `deep-agents-ui` (or your repo name) in the search box
   - Click on your repository when it appears
   - If you don't see it:
     - Click **"Adjust GitHub App Permissions"**
     - Make sure the repository is selected
     - Click **"Save"** and refresh

4. **Configure Project:**
   - **Project Name:** Leave default (`deep-agents-ui`) or change it
   - **Framework Preset:** Should auto-detect **"Next.js"** ✅
   - **Root Directory:** 
     - If your frontend is in `deep-agents-ui/` subdirectory: Set to `deep-agents-ui`
     - If your frontend is at the repository root (`deepagents-quickstarts/`): Leave as `./`
   - **Build Command:** Should auto-fill `next build` ✅
   - **Output Directory:** Should auto-fill `.next` ✅
   - **Install Command:** Should auto-fill `yarn install` or `npm install` ✅

5. **Environment Variables (Skip for now):**
   - We'll add these in Step 3
   - Click **"Deploy"** button to continue (you can add env vars later)

6. **Wait for First Deployment:**
   - Vercel will start building your project
   - You'll see build logs in real-time
   - This first deployment will likely fail (we haven't added env vars yet) - that's OK!
   - Build takes 2-5 minutes

**✅ Repository is now connected!**

**📝 Note:** After this step, every push to your main/master branch will trigger an automatic deployment.

## Step 2: Configure Project Settings

**📍 WHERE:** Vercel Dashboard → Your Project → Settings

**⏱️ WHEN:** One-time setup (after first deployment)

**🔧 WHAT:** Verify and adjust build settings, framework configuration

### Step-by-Step Instructions

1. **Go to Project Settings:**
   - In Vercel Dashboard, click on your project (`deep-agents-ui`)
   - Click **"Settings"** tab (top navigation)

2. **General Settings:**
   - **Project Name:** Can change if needed
   - **Framework:** Should show **"Next.js"**
   - **Node.js Version:** Should be **18.x** or **20.x** (Vercel auto-detects)
   - **Build Command:** `next build` (default, usually correct)
   - **Output Directory:** `.next` (default, usually correct)
   - **Install Command:** `yarn install` or `npm install` (auto-detected from your `package.json`)

3. **Build & Development Settings:**
   - Scroll to **"Build & Development Settings"**
   - **Framework Preset:** Next.js
   - **Root Directory:** 
     - If your frontend code is in `deep-agents-ui/` subdirectory: Set to `deep-agents-ui`
     - If your frontend code is at repository root (`deepagents-quickstarts/`): Leave as `./`
   - To change it:
     - Click **"Edit"**
     - Set **Root Directory** to `deep-agents-ui` (or your subdirectory path)
     - Click **"Save"**

4. **Environment Variables (We'll add these next):**
   - Scroll to **"Environment Variables"** section
   - We'll configure these in Step 3

**✅ Project settings are configured!**

## Step 3: Add Environment Variables

**📍 WHERE:** Vercel Dashboard → Your Project → Settings → Environment Variables

**⏱️ WHEN:** One-time setup (do this before first successful deployment)

**🔐 WHAT:** These environment variables configure your frontend to connect to your backend and services

**📝 Note:** If you're using the optional GitHub Actions workflow (see "Automatic Deployments" section), you'll also need to add a `VERCEL_TOKEN` secret to GitHub. See the workflow section for details.

### Step-by-Step Instructions

1. **Navigate to Environment Variables:**
   - In your project, go to **"Settings"** tab
   - Click **"Environment Variables"** in the left sidebar
   - Or scroll to the **"Environment Variables"** section

2. **Add Each Variable:**
   - Click **"Add New"** button
   - Enter the variable name (exactly as shown below)
   - Enter the variable value
   - Select which environments to apply to:
     - **Production:** For your live site
     - **Preview:** For pull request previews
     - **Development:** For local development (optional)
   - Click **"Save"**
   - Repeat for each variable

### Environment Variables to Add

#### Required Variables

**NEXT_PUBLIC_LANGSMITH_API_KEY** (Optional but Recommended)
- **What it is:** Your LangSmith API key for accessing LangGraph deployments
- **Where to get it:**
  1. Go to LangSmith: https://smith.langchain.com
  2. Sign in or create an account
  3. Click your profile icon (top right) → **"Settings"**
  4. Go to **"API Keys"** section
  5. Click **"Create API Key"**
  6. Copy the key (starts with `lsv2_pt_...`)
  7. **⚠️ IMPORTANT:** Save it immediately - you won't see it again!
- **Value:** `lsv2_pt_abc123def456...` (your actual key)
- **Environments:** ✅ Production, ✅ Preview

**NEXT_PUBLIC_SUPABASE_URL** (Optional - Only if using Supabase auth)
- **What it is:** Your Supabase project URL
- **Where to get it:**
  1. Go to Supabase: https://supabase.com/dashboard
  2. Select your project
  3. Go to **"Settings"** → **"API"**
  4. Find **"Project URL"** (starts with `https://`)
  5. Copy the complete URL
- **Value:** `https://xxxxx.supabase.co` (your actual URL)
- **Environments:** ✅ Production, ✅ Preview

**NEXT_PUBLIC_SUPABASE_ANON_KEY** (Optional - Only if using Supabase auth)
- **What it is:** Your Supabase anonymous/public key (NOT the service role key!)
- **Where to get it:**
  1. In the same **"Settings"** → **"API"** page
  2. Find **"Project API keys"** section
  3. Look for **"anon"** or **"public"** key (NOT service_role!)
  4. Click **"Reveal"** to show the key
  5. Copy the complete key
- **Value:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (your actual anon key)
- **Environments:** ✅ Production, ✅ Preview
- **⚠️ SECURITY WARNING:** 
  - Use the **anon/public** key, NOT the service_role key
  - The service_role key has admin access and should NEVER be in frontend code
  - The frontend code has safety checks to prevent this

### Example: Adding Environment Variables

Here's how to add the first variable:

1. Click **"Add New"** button
2. **Key:** `NEXT_PUBLIC_LANGSMITH_API_KEY`
3. **Value:** `lsv2_pt_your_actual_key_here`
4. **Environments:** Check ✅ **Production** and ✅ **Preview**
5. Click **"Save"**
6. Repeat for other variables

**✅ Environment variables are now configured!**

**📝 Important Notes:**
- Variables starting with `NEXT_PUBLIC_` are exposed to the browser (this is intentional for Next.js)
- After adding/changing environment variables, you need to **redeploy** for changes to take effect
- You can add variables at any time, but they only apply to new deployments

## Step 4: Trigger First Deployment

**📍 WHERE:** Vercel Dashboard → Your Project → Deployments

**⏱️ WHEN:** After adding environment variables

**🤖 WHAT:** Redeploy your project with the new environment variables

### Step-by-Step Instructions

1. **Go to Deployments:**
   - In your project, click **"Deployments"** tab
   - You'll see your previous deployment (likely failed or incomplete)

2. **Redeploy with New Variables:**
   - Find the latest deployment
   - Click the **"..."** menu (three dots) on the right
   - Click **"Redeploy"**
   - Or click **"Redeploy"** button at the top
   - Confirm by clicking **"Redeploy"** again

3. **Watch the Build:**
   - You'll see build logs in real-time
   - Build process:
     - Installing dependencies (`yarn install`)
     - Building Next.js app (`next build`)
     - Optimizing assets
     - Deploying to edge network
   - Build takes 2-5 minutes

4. **Check Build Status:**
   - **✅ Success:** You'll see a green checkmark and "Ready" status
   - **❌ Failure:** Check the build logs for errors
   - Common issues:
     - Missing environment variables
     - Build errors in code
     - Dependency installation failures

**✅ First deployment is complete!**

## Step 5: Verify Deployment and Get Your URL

**📍 WHERE:** Vercel Dashboard → Your Project

**⏱️ WHEN:** After successful deployment

**🔍 WHAT:** Get your live URL and verify everything works

### Step-by-Step Instructions

1. **Get Your Live URL:**
   - In your project dashboard, you'll see your deployment
   - **Production URL:** `https://your-project-name.vercel.app`
   - Or click on the deployment to see the URL
   - **Custom Domain:** You can add a custom domain later (optional)

2. **Test Your Deployment:**
   - Click on the production URL to open it in a browser
   - You should see your Deep Agents UI
   - The app will prompt you to configure:
     - **Deployment URL:** Your LangGraph backend URL (e.g., `http://your-ec2-ip:8123` or your backend URL)
     - **Assistant ID:** Your assistant ID from `langgraph.json` (e.g., `research`)
     - **LangSmith API Key:** (Optional, can use env var or enter here)
     - **Supabase URL & Key:** (Optional, if using auth)

3. **Configure the App:**
   - Enter your backend deployment URL
   - Enter your assistant ID
   - Click **"Save"** or **"Connect"**
   - The app should now connect to your backend

4. **Test Functionality:**
   - Try sending a message in the chat
   - Verify it connects to your backend
   - Check that threads are loading (if using Supabase)
   - Test authentication (if configured)

**✅ Your frontend is now live!**

**📝 Note:** 
- Your production URL is: `https://your-project-name.vercel.app`
- This URL is permanent and won't change
- You can share this URL with others
- All future deployments will update this same URL automatically

## 🤖 Automatic Deployments (After Setup)

### Option A: Vercel Built-in CI/CD (Recommended - Default)

Vercel automatically handles deployments when you connect your GitHub repository. This is the simplest and recommended approach.

### Option B: GitHub Actions Workflow (Optional - Advanced)

If you want more control over the deployment process, you can use a GitHub Actions workflow. This is optional and not required for basic deployments.

**When to use GitHub Actions:**
- You want to run custom tests before deployment
- You need custom build steps
- You want to integrate with other CI/CD tools
- You need programmatic control over deployments

**To use GitHub Actions workflow:**

1. **Get Vercel Token:**
   - Go to Vercel Dashboard: https://vercel.com/account/tokens
   - Click **"Create Token"**
   - Give it a name (e.g., "GitHub Actions Deployment")
   - Copy the token (you'll only see it once!)

2. **Add Vercel secrets to GitHub:**
   - Go to GitHub → Your Repository → Settings → Secrets and variables → Actions
   - Add these secrets:
     - **`VERCEL_TOKEN`** - Your Vercel access token (required)
     - **`VERCEL_ORG_ID`** - Your Vercel organization ID (optional, can be found in project settings)
     - **`VERCEL_PROJECT_ID`** - Your Vercel project ID (optional, can be found in project settings)

3. **Verify workflow file exists:**
   - **Repository Root:** `deepagents-quickstarts/`
   - The workflow file must be at: `deepagents-quickstarts/.github/workflows/deploy-vercel.yml`
   - **⚠️ IMPORTANT:** GitHub Actions only detects workflows in the repository root `.github/workflows/` directory
   - Workflows in subdirectories (like `deep_research/.github/workflows/`) will NOT be detected by GitHub Actions
   - GitHub Actions will automatically detect and run it when it's in the correct location

4. **The workflow will deploy automatically** on pushes to main/master that affect the `deep-agents-ui/` directory

**Note:** You can use both methods - Vercel's built-in CI/CD and GitHub Actions. They won't conflict, but you may get duplicate deployments. Consider disabling Vercel's automatic deployments if using GitHub Actions exclusively.

### How Automatic Deployments Work (Vercel Built-in)

Once setup is complete, deployments happen automatically:

1. **Push to Main/Master Branch:**
   ```bash
   git add .
   git commit -m "Update UI"
   git push origin main
   ```

2. **Vercel Automatically:**
   - Detects the push via GitHub webhook
   - Starts building your project
   - Runs tests and linting (if configured)
   - Deploys to production
   - Updates your live URL

3. **You'll Get Notifications:**
   - Email notification (if enabled)
   - GitHub commit status updates
   - Vercel dashboard shows deployment status

**No manual steps needed!**

### Preview Deployments

Vercel also creates **preview deployments** for pull requests:

1. **Create a Pull Request:**
   - Push to a feature branch
   - Create a PR on GitHub

2. **Vercel Automatically:**
   - Creates a preview deployment
   - Generates a unique URL (e.g., `your-project-git-feature-branch.vercel.app`)
   - Adds a comment to your PR with the preview URL

3. **Test Before Merging:**
   - Click the preview URL in the PR
   - Test your changes
   - Merge when ready

**Preview URLs are temporary** and deleted when the PR is closed.

## 🔧 Configuration Options

### Custom Domain (Optional)

1. **Go to Project Settings:**
   - Project → Settings → Domains

2. **Add Domain:**
   - Enter your domain (e.g., `app.yourdomain.com`)
   - Click **"Add"**

3. **Configure DNS:**
   - Vercel will show DNS records to add
   - Add them to your domain registrar
   - Wait for DNS propagation (5-60 minutes)

4. **SSL Certificate:**
   - Vercel automatically provisions SSL certificates
   - Your site will be available at `https://yourdomain.com`

### Environment-Specific Variables

You can set different values for different environments:

- **Production:** Live site (main/master branch)
- **Preview:** Pull request previews
- **Development:** Local development (optional)

To set environment-specific values:
1. Go to Settings → Environment Variables
2. When adding/editing a variable
3. Select which environments to apply to
4. You can have different values for Production vs Preview

### Build Settings

If you need to customize build settings:

1. **Go to Settings → General**
2. **Override Build Command:**
   - Default: `next build`
   - Custom: `yarn build` or `npm run build`
3. **Override Install Command:**
   - Default: `yarn install` or `npm install`
   - Custom: `yarn install --frozen-lockfile`

### Next.js Configuration

Your `next.config.ts` is automatically used. Common configurations:

```typescript
// next.config.ts
const nextConfig = {
  // Add custom headers
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
        ],
      },
    ];
  },
  // Environment variables (can also use Vercel dashboard)
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
};

export default nextConfig;
```

## 🐛 Troubleshooting

### Deployment Fails

**Check Build Logs:**
1. Go to Deployments → Click on failed deployment
2. Check the build logs for errors
3. Common issues:
   - **Missing dependencies:** Check `package.json`
   - **Build errors:** Check for TypeScript/ESLint errors
   - **Environment variables:** Make sure all required vars are set

**Common Error: "Module not found"**
- Make sure all dependencies are in `package.json`
- Run `yarn install` locally to verify
- Check that `node_modules` is in `.gitignore`

**Common Error: "Build command failed"**
- Check your build command in Settings
- Verify `next build` works locally
- Check for TypeScript errors: `yarn build` locally

### Environment Variables Not Working

**Symptoms:**
- Variables are `undefined` in the app
- App can't connect to backend

**Solutions:**
1. **Verify Variable Names:**
   - Must start with `NEXT_PUBLIC_` for client-side access
   - Check spelling (case-sensitive)

2. **Redeploy After Adding Variables:**
   - Environment variables only apply to new deployments
   - Go to Deployments → Click "..." → "Redeploy"

3. **Check Environment Selection:**
   - Make sure variables are enabled for Production/Preview
   - Go to Settings → Environment Variables → Edit variable

4. **Verify in Build Logs:**
   - Variables are shown in build logs (values are hidden)
   - Check that they appear in the logs

### App Can't Connect to Backend

**Symptoms:**
- Frontend loads but can't reach backend API
- CORS errors in browser console

**Solutions:**
1. **Check Backend URL:**
   - Make sure backend is accessible from internet
   - Test backend URL in browser: `http://your-backend-url:8123/docs`

2. **CORS Configuration:**
   - Backend needs to allow requests from Vercel domain
   - Add your Vercel URL to backend CORS settings
   - Example: `https://your-project.vercel.app`

3. **Network Issues:**
   - If backend is on private network, it won't be accessible
   - Backend must be publicly accessible
   - Check security groups/firewall rules

### Preview Deployments Not Working

**Symptoms:**
- PR previews don't deploy
- Preview URL shows 404

**Solutions:**
1. **Check GitHub Integration:**
   - Settings → Git → Verify repository is connected
   - Reconnect if needed

2. **Check Branch Settings:**
   - Settings → Git → Production Branch
   - Make sure main/master is set correctly

3. **Check Build Settings:**
   - Preview deployments use same build settings as production
   - Verify build command works

## 📊 Monitoring and Analytics

### Deployment History

View all deployments:
- Go to Deployments tab
- See build status, timing, and logs
- Click on any deployment to see details

### Real-time Logs

View application logs:
1. Go to your project
2. Click "Logs" tab
3. See real-time logs from your application
4. Filter by function, time range, etc.

### Analytics (Pro Plan)

Vercel Analytics (requires Pro plan):
- Page views and performance
- Web Vitals metrics
- User analytics
- Enable in Settings → Analytics

## 🔒 Security Best Practices

1. **Never Commit Secrets:**
   - Use Vercel environment variables
   - Add `.env.local` to `.gitignore`
   - Never commit API keys or passwords

2. **Use Environment Variables:**
   - Store all secrets in Vercel dashboard
   - Use `NEXT_PUBLIC_` prefix only for public variables
   - Keep sensitive keys server-side only

3. **Review Dependencies:**
   - Regularly update dependencies
   - Check for security vulnerabilities: `yarn audit`

4. **Enable Security Headers:**
   - Configure in `next.config.ts`
   - Use Vercel's security headers feature

5. **Monitor Deployments:**
   - Review deployment logs regularly
   - Set up email notifications for failures

## 💰 Pricing and Limits

### Free Tier (Hobby Plan)

- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Automatic SSL
- ✅ Preview deployments
- ✅ Global CDN
- ⚠️ Limited build minutes (100 hours/month)

### Pro Plan ($20/month)

- Everything in Hobby
- ✅ Unlimited bandwidth
- ✅ Team collaboration
- ✅ Analytics
- ✅ More build minutes
- ✅ Priority support

**For most projects, the free tier is sufficient!**

## 🎉 Setup Complete!

**Congratulations!** Your frontend is now deployed to Vercel. Here's what you have:

### ✅ What's Automated (No Action Needed)

Every time you push code to the `main` or `master` branch:
1. ✅ Vercel automatically detects the push
2. ✅ Builds your Next.js application
3. ✅ Runs tests and linting
4. ✅ Deploys to production automatically
5. ✅ Updates your live URL

**You don't need to do anything manually for deployments!**

### 🔄 How to Deploy Updates

**Simple:** Just push your code!
```bash
git add .
git commit -m "Update UI"
git push origin main
```

The deployment happens automatically in the background. Check the **Deployments** tab in Vercel to see progress.

### 🛑 Manual Deployment (If Needed)

If you want to trigger a deployment manually:
1. Go to Vercel Dashboard → Your Project
2. Click **"Deployments"** tab
3. Click **"Redeploy"** button
4. Select the branch/commit to deploy
5. Click **"Redeploy"**

### 📱 Your Live URLs

- **Production:** `https://your-project-name.vercel.app`
- **Preview (PRs):** `https://your-project-git-branch-name.vercel.app`
- **Custom Domain:** `https://yourdomain.com` (if configured)

### 🚀 Next Steps

1. **Add Custom Domain** (optional)
2. **Set up Analytics** (optional, Pro plan)
3. **Configure Webhooks** (optional, for notifications)
4. **Set up Team Access** (if working with others)
5. **Monitor Performance** (check logs and analytics)

Your frontend is now live and automatically deploying on every push! 🎊

