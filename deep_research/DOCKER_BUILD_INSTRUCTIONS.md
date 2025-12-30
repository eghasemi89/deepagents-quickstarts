# Docker Build and Run Instructions

This document explains how to build and run the LangGraph Deep Research Agent using Docker.

## Files Modified/Created

The following files were created or modified to fix the license validation and graph loading issues:

### Files to Commit:
- `Dockerfile` - Modified to include license override and graph loading fix
- `langgraph_license_override/validation.py` - Noop license validation (optional, can be generated inline)
- `langgraph_license_override/__init__.py` - Package init file
- `docker-compose.yml` - Docker Compose configuration for local development
- `DOCKER_BUILD_INSTRUCTIONS.md` - This file

### Files NOT to Commit (optional/temporary):
- `patch_license_runtime.py` - Not needed (using build-time override instead)
- `Dockerfile.simple_working` - Backup/reference file
- `Dockerfile.patched` - Backup/reference file
- `Dockerfile.bak` - Backup file

## Prerequisites

1. **Docker** and **Docker Compose** installed
2. **Environment variables** set up in `.env` file (see `env.example`)
3. **PostgreSQL/Supabase** database accessible
4. **Redis** (can be run via docker-compose)

## Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Database (required)
POSTGRES_URI=postgresql://user:password@host:5432/dbname

# Redis (required - can use docker-compose redis service)
REDIS_URI=redis://redis:6379

# API Keys (required)
LANGSMITH_API_KEY=your_langsmith_key
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key

# Optional
ANTHROPIC_API_KEY=your_anthropic_key
LANGGRAPH_CLOUD_LICENSE_KEY=your_license_key

# Optional: Authentication (if using auth.py)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

## Building the Docker Image

### Option 1: Using Docker Compose (Recommended)

```bash
# Build the image
docker-compose build

# Build without cache (if you encounter issues)
docker-compose build --no-cache

# Build and start services
docker-compose up --build
```

### Option 2: Using Docker directly

```bash
# Build the image
docker build -t deep-research-api:latest .

# Build without cache (if you encounter issues)
docker build --no-cache -t deep-research-api:latest .
```

## Running the Container

### Option 1: Using Docker Compose (Recommended)

```bash
# Start all services (Redis + LangGraph API)
docker-compose up

# Start in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f langgraph-api

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Option 2: Using Docker directly

First, start Redis:
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

Then run the LangGraph API:
```bash
docker run -d \
  --name langgraph-api \
  --link redis:redis \
  -p 8000:8000 \
  --env-file .env \
  -e REDIS_URI=redis://redis:6379 \
  deep-research-api:latest
```

## Rebuilding After Changes

### When to Rebuild

Rebuild the image when you:
- Modify `Dockerfile`
- Change `langgraph.json`
- Update `agent.py` or other source files
- Modify `langgraph_license_override/validation.py`
- Change dependencies in `pyproject.toml`

### Rebuild Commands

```bash
# Using Docker Compose
docker-compose build --no-cache
docker-compose up -d

# Using Docker directly
docker build --no-cache -t deep-research-api:latest .
docker stop langgraph-api && docker rm langgraph-api
docker run -d --name langgraph-api --link redis:redis -p 8000:8000 --env-file .env -e REDIS_URI=redis://redis:6379 deep-research-api:latest
```

## Verifying the Setup

1. **Check if the container is running:**
   ```bash
   docker-compose ps
   # or
   docker ps
   ```

2. **Check the logs for graph loading:**
   ```bash
   docker-compose logs langgraph-api | grep -i "graph\|research"
   # Look for: "✅ Set LANGSERVE_GRAPHS from langgraph.json"
   ```

3. **Check the logs for license override:**
   ```bash
   docker-compose logs langgraph-api | grep -i "license\|validation"
   # Should NOT see JWT decode errors
   ```

4. **Access the API:**
   - API Docs: http://localhost:8123/docs
   - Health Check: http://localhost:8123/docs (should load)

5. **Test the research graph:**
   ```bash
   curl -X POST http://localhost:8123/assistants/search \
     -H "Content-Type: application/json" \
     -d '{"query": {"graph_id": "research"}}'
   ```

## Troubleshooting

### Graphs Not Loading

If you see `Invalid assistant: 'research'`:
1. Check logs: `docker-compose logs langgraph-api`
2. Verify `langgraph.json` exists and has correct format
3. Look for `LANGSERVE_GRAPHS` in logs
4. Rebuild with `--no-cache`

### License Validation Errors

If you see JWT decode errors:
1. Verify the license override is applied:
   ```bash
   docker-compose exec langgraph-api ls -la /api/langgraph_license/
   docker-compose exec langgraph-api ls -la /usr/local/lib/python3.11/site-packages/langgraph_license/
   ```
2. Check that both locations have `validation.py`
3. Rebuild with `--no-cache`

### Container Won't Start

1. Check logs: `docker-compose logs langgraph-api`
2. Verify environment variables are set correctly
3. Check database connectivity
4. Verify Redis is accessible

### Port Already in Use

If port 8123 is already in use:
```bash
# Change port in docker-compose.yml
ports:
  - "8124:8000"  # Use 8124 instead (or any other available port)
```

## Key Fixes Applied

1. **Graph Loading Fix:**
   - Created entrypoint wrapper (`ensure_graphs.sh`) that reads `langgraph.json` and sets `LANGSERVE_GRAPHS`
   - Ensures graphs are loaded even if base image entrypoint doesn't read `langgraph.json` correctly

2. **License Validation Fix:**
   - Overrides `langgraph_license/validation.py` in both:
     - `site-packages/langgraph_license/` (installed package)
     - `/api/langgraph_license/` (where Python imports from)
   - Provides noop validation that bypasses all license checks

## Production Deployment

For production (AWS ECS/EKS), use `docker-compose.aws.yml` as a reference, but:
1. Don't include Redis in the same compose file (use ElastiCache)
2. Set environment variables via task definitions/ConfigMaps
3. Use proper secrets management (AWS Secrets Manager, etc.)
4. Set up proper health checks and auto-scaling

## Additional Resources

- See `AWS_DEPLOYMENT.md` for AWS-specific deployment
- See `DOCKER_NETWORKING.md` for networking configuration
- See `env.example` for all environment variables

