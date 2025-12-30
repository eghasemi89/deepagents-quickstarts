# LangSmith and License Guide

## Understanding LangGraph License Requirements

LangGraph self-hosted deployment has **two modes**:

### 1. Self-Hosted Lite (Free, with LangSmith API Key)
- ✅ **Free** - No enterprise license needed
- ✅ Requires **LangSmith API key** (`LANGSMITH_API_KEY`)
- ✅ Supports up to **1 million nodes executed**
- ✅ Suitable for most development and small-to-medium production workloads
- ⚠️ **LangSmith API key is required** for license verification (even if you disable tracing)

### 2. Self-Hosted Enterprise (Requires License)
- ✅ **Full features** - No limits
- ✅ Requires **Enterprise License Key** (`LANGGRAPH_CLOUD_LICENSE_KEY`)
- ✅ **No LangSmith API key needed**
- ⚠️ Must contact LangChain sales team to obtain license

## Current Status

Your setup is running in **Self-Hosted Lite mode**, which requires `LANGSMITH_API_KEY` for license verification. Even if you disable tracing, you still need the API key for the lite license.

## Can You Remove LangSmith Dependency?

### Option 1: Keep LangSmith (Recommended for Most Cases)

**Pros:**
- ✅ Free (no enterprise license needed)
- ✅ Works with current setup
- ✅ Optional tracing/observability
- ✅ Easy to set up

**Cons:**
- ⚠️ Requires LangSmith account (free to sign up)
- ⚠️ API key needed for license verification

**Configuration:**
```bash
# Required for license verification (even if tracing is disabled)
LANGSMITH_API_KEY=lsv2_pt_...

# Optional: Disable tracing if you don't want observability
LANGCHAIN_TRACING_V2=false
# or
LANGSMITH_TRACING=false
```

### Option 2: Get Enterprise License (Remove LangSmith)

**Pros:**
- ✅ No LangSmith dependency
- ✅ No limits
- ✅ Full enterprise features

**Cons:**
- ⚠️ Requires contacting LangChain sales
- ⚠️ May have costs (depends on agreement)
- ⚠️ More complex setup

**Configuration:**
```bash
# Remove LANGSMITH_API_KEY
# Add enterprise license key instead
LANGGRAPH_CLOUD_LICENSE_KEY=your_enterprise_license_key
```

### Option 3: Use LangGraph Cloud (Managed Service)

**Pros:**
- ✅ No self-hosting needed
- ✅ Managed by LangChain
- ✅ Built-in observability

**Cons:**
- ⚠️ Requires LangGraph Cloud account
- ⚠️ May have usage costs
- ⚠️ Less control over infrastructure

## How to Disable LangSmith Tracing (Keep License Verification)

If you want to keep the free lite license but disable tracing/observability:

### Step 1: Keep LANGSMITH_API_KEY (Required for License)

```bash
# Still required for self-hosted lite license
LANGSMITH_API_KEY=lsv2_pt_...
```

### Step 2: Disable Tracing

You can disable tracing using **either** of these environment variables:

```bash
# Option 1: Use LANGCHAIN_TRACING_V2 (recommended)
LANGCHAIN_TRACING_V2=false

# Option 2: Use LANGSMITH_TRACING
LANGSMITH_TRACING=false
```

**Note:** Setting either to `false` will disable tracing. You can use both for extra certainty.

### Step 3: Update Your Configuration

**In `.env` file:**
```bash
# Required for self-hosted lite license (even if tracing disabled)
LANGSMITH_API_KEY=lsv2_pt_...

# Disable tracing/observability
LANGCHAIN_TRACING_V2=false
LANGSMITH_TRACING=false

# Optional: Remove or comment out project name (not needed if tracing disabled)
# LANGSMITH_PROJECT=deep-agents-from-scratch
```

**In Docker run command:**
```bash
docker run -d \
  --name langgraph-api \
  --network langgraph-net \
  -p 8123:8000 \
  -e POSTGRES_URI="..." \
  -e REDIS_URI="redis://redis:6379" \
  -e LANGSMITH_API_KEY="lsv2_pt_..." \  # Still needed for license
  -e LANGCHAIN_TRACING_V2="false" \      # Disable tracing
  -e LANGSMITH_TRACING="false" \         # Also disable (optional, for extra certainty)
  -e OPENAI_API_KEY="..." \
  -e TAVILY_API_KEY="..." \
  deep-research-agent:latest
```

**In Docker Compose:**
```yaml
services:
  langgraph-api:
    environment:
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LANGCHAIN_TRACING_V2=false
      - LANGSMITH_TRACING=false
```

**In AWS ECS Task Definition:**
```json
{
  "environment": [
    {
      "name": "LANGSMITH_API_KEY",
      "value": "lsv2_pt_..."
    },
    {
      "name": "LANGCHAIN_TRACING_V2",
      "value": "false"
    },
    {
      "name": "LANGSMITH_TRACING",
      "value": "false"
    }
  ]
}
```

### Step 4: Test That Tracing is Disabled

**Quick Test Script:**
```bash
cd deepagents-quickstarts/deep_research
./test-tracing-disabled.sh
```

**Manual Test:**
1. Start container with tracing disabled
2. Check logs - should NOT see LangSmith API calls
3. Make a request to your API
4. Check LangSmith dashboard - should NOT see new traces

**Verify in Logs:**
```bash
# Should NOT see these in logs:
docker logs langgraph-api | grep -i "langsmith\|tracing"

# Should see these (license verification, but no tracing):
# - "Using langgraph_runtime_postgres"
# - "Application startup complete"
# - But NO "HTTP Request: POST https://api.smith.langchain.com"
```

## Removing LangSmith Completely

### If You Have Enterprise License

1. **Remove `LANGSMITH_API_KEY` from `.env`**
2. **Add `LANGGRAPH_CLOUD_LICENSE_KEY`**:
   ```bash
   LANGGRAPH_CLOUD_LICENSE_KEY=your_enterprise_license_key
   ```
3. **Update Docker/ECS configuration** to use license key instead
4. **Remove LangSmith-related environment variables**

### If You Don't Have Enterprise License

**You cannot completely remove LangSmith** - the self-hosted lite mode requires it for license verification. Your options are:

1. **Keep LangSmith API key** (free, works now)
2. **Get enterprise license** (contact LangChain sales)
3. **Use LangGraph Cloud** (managed service)

## Summary

| Mode | LangSmith API Key | Enterprise License | Cost | Limits |
|------|------------------|-------------------|------|--------|
| **Self-Hosted Lite** | ✅ Required | ❌ Not needed | Free | 1M nodes |
| **Self-Hosted Enterprise** | ❌ Not needed | ✅ Required | Contact sales | None |
| **LangGraph Cloud** | ✅ Required | ❌ Not needed | Usage-based | Depends on plan |

## Recommendation

**For most users:** Keep `LANGSMITH_API_KEY` and disable tracing if you don't want observability:
- Free
- Works immediately
- No enterprise license needed
- 1M nodes is plenty for most use cases

**Only get enterprise license if:**
- You need > 1M nodes
- You have compliance requirements against LangSmith
- You have budget for enterprise license

## Testing Tracing Disabled

### Quick Test

Use the provided test script:

```bash
cd deepagents-quickstarts/deep_research
./test-tracing-disabled.sh
```

This script will:
1. ✅ Load your `.env` file
2. ✅ Start Redis if needed
3. ✅ Start LangGraph API with tracing **disabled**
4. ✅ Verify the API is working
5. ✅ Check logs to confirm no tracing calls

### Manual Test

**1. Update `.env` file:**
```bash
# Edit .env and change:
LANGSMITH_TRACING=false
# Add:
LANGCHAIN_TRACING_V2=false
```

**2. Restart your container:**
```bash
docker stop langgraph-api
docker rm langgraph-api

# Restart with updated .env
docker run -d \
  --name langgraph-api \
  --network langgraph-test-net \
  -p 8123:8000 \
  --env-file .env \
  -e LANGCHAIN_TRACING_V2="false" \
  -e LANGSMITH_TRACING="false" \
  deep-research-agent:test
```

**3. Verify tracing is disabled:**
```bash
# Check logs - should NOT see LangSmith API calls
docker logs langgraph-api | grep -i "api.smith.langchain.com"
# Should return nothing (or only license verification, not tracing)

# Make a test request
curl http://localhost:8123/

# Check LangSmith dashboard - should NOT see new traces
```

**4. Compare with tracing enabled:**
```bash
# With tracing enabled, you'd see in logs:
# "HTTP Request: POST https://api.smith.langchain.com/v1/traces"
# With tracing disabled, you won't see these calls
```

## Testing Without LangSmith (Will Fail)

If you want to test what happens without LangSmith API key:

```bash
# Remove LANGSMITH_API_KEY from environment
docker run -d \
  --name langgraph-api-test \
  --network langgraph-net \
  -p 8123:8000 \
  -e POSTGRES_URI="..." \
  -e REDIS_URI="redis://redis:6379" \
  -e OPENAI_API_KEY="..." \
  -e TAVILY_API_KEY="..." \
  # No LANGSMITH_API_KEY
  deep-research-agent:latest
```

**Expected result:** Container will fail to start with license verification error:
```
ValueError: License verification failed. Please ensure proper configuration:
- For local development, set a valid LANGSMITH_API_KEY...
```

## Getting Enterprise License

If you need to remove LangSmith completely:

1. Contact LangChain sales: https://www.langchain.com/contact
2. Request self-hosted enterprise license
3. They'll provide `LANGGRAPH_CLOUD_LICENSE_KEY`
4. Update your configuration to use license key instead of LangSmith API key

