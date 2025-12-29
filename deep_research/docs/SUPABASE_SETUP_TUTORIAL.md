# Supabase Database Setup Tutorial

This tutorial will guide you through setting up Supabase database persistence for your LangGraph agent. You'll learn how to find your connection string and database password.

## Prerequisites

- A Supabase account and project
- Access to your Supabase project dashboard

## Step 1: Access Your Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and sign in
2. Select your project from the dashboard
3. You should see your project overview page

## Step 2: Find Your Database Password

### Option A: If You Already Have a Password

1. In the left sidebar, navigate to **Database** → **Settings**
2. Scroll to the **"Database password"** section at the top
3. If you see a password field, it will be masked (shown as dots/asterisks)
4. **Important**: Supabase doesn't allow you to view existing passwords for security reasons
5. If you don't remember your password, proceed to **Option B**

### Option B: Reset Your Database Password

1. Go to **Database** → **Settings**
2. Find the **"Database password"** section
3. Click the **"Reset database password"** button (located on the right side of the section)
4. A new password will be generated and displayed
5. **⚠️ CRITICAL**: Copy this password immediately and save it securely
   - You will NOT be able to view it again after closing the dialog
   - If you lose it, you'll need to reset it again
6. Save the password in a secure location (password manager, `.env` file, etc.)

## Step 3: Get Your Connection String

There are two ways to get your connection string:

### Method 1: Using the Connect Button (Recommended)

1. At the top of your Supabase dashboard, click the **"Connect"** button
   - This button is usually next to your project name in the top navigation bar
2. A modal/dialog will open showing connection information
3. You'll see several connection string options:
   - **Direct connection**: `db.[PROJECT_REF].supabase.co:5432` (IPv6 required, may not work on all networks)
   - **Session mode**: Via connection pooler (port 5432) - **Recommended for LangGraph**
   - **Transaction mode**: Via connection pooler (port 6543) - for serverless
4. **For LangGraph, use Session mode** (connection pooler, port 5432):
   - More reliable than direct connection
   - Works with IPv4 networks
   - Better for persistent connections
   - Connection string format: `postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres`
5. Copy the Session mode connection string
6. Replace `[YOUR-PASSWORD]` with the actual password you obtained in Step 2
7. Add `?sslmode=require` to the end if it's not already there

### Method 2: Construct It Manually

If you prefer to build the connection string yourself:

1. **Get your project reference**:
   - Look at your Supabase dashboard URL: `supabase.com/dashboard/project/YOUR_PROJECT_REF/...`
   - The `YOUR_PROJECT_REF` is the unique identifier for your project
   - Example: If URL is `supabase.com/dashboard/project/ajrbwkcuthywfihaarmflo/...`, then `ajrbwkcuthywfihaarmflo` is your project ref

2. **Get your database password** (from Step 2)

3. **Construct the connection string**:
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres?sslmode=require
   ```
   
   Example:
   ```
   postgresql://postgres:mypassword123@db.ajrbwkcuthywfihaarmflo.supabase.co:5432/postgres?sslmode=require
   ```

## Step 4: Configure Your Environment Variables

Now that you have your connection string and password, add them to your `.env` file:

### Option 1: Using Full Connection String (Recommended for `langgraph up`)

1. Open or create a `.env` file in the `deep_research` directory
2. Add your connection string using **Session mode (pooler)**:
   ```bash
   POSTGRES_URI_CUSTOM=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
   ```
   Replace:
   - `[PROJECT_REF]` with your Supabase project reference (e.g., `ltbwpsjgivrwxoevnolj`)
   - `[PASSWORD]` with your database password
   - `[REGION]` with your Supabase region (e.g., `us-east-2`)
   
   Example:
   ```bash
   POSTGRES_URI_CUSTOM=postgresql://postgres.ltbwpsjgivrwxoevnolj:my_password@aws-0-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require
   ```

   **Note**: For `langgraph up`, use `POSTGRES_URI_CUSTOM` (not `SUPABASE_DB_URI`).

### Option 2: Using Individual Parameters

Alternatively, you can use separate environment variables:

```bash
SUPABASE_DB_HOST=db.your_project_ref.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your_actual_password
```

**Note**: If using individual parameters, make sure to replace `your_project_ref` and `your_actual_password` with your actual values.

## Step 5: Choose Your Deployment Method

**IMPORTANT**: There are two different ways to run LangGraph, and they handle persistence differently:

### Option A: Using `langgraph up` (Recommended for Production)

`langgraph up` is designed for deployment and properly supports external PostgreSQL databases like Supabase.

1. **Set `POSTGRES_URI_CUSTOM` in your `.env` file**:
   ```bash
   POSTGRES_URI_CUSTOM=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
   ```
   Replace:
   - `[PROJECT_REF]` with your Supabase project reference
   - `[PASSWORD]` with your database password
   - `[REGION]` with your Supabase region (e.g., `us-east-2`)

2. **Start the server**:
   ```bash
   cd deepagents-quickstarts/deep_research
   POSTGRES_URI=$(grep "^POSTGRES_URI_CUSTOM=" .env | cut -d'=' -f2-)
   langgraph up --recreate --postgres-uri "$POSTGRES_URI"
   ```
   
   **Note**: 
   - Use `--recreate` to force a rebuild (especially after changing dependencies)
   - The `--postgres-uri` flag explicitly sets the database connection
   - Alternatively, `langgraph up` will read `POSTGRES_URI_CUSTOM` from your `.env` file automatically

3. **Note**: `langgraph up` will automatically:
   - Create the database schema with proper migrations
   - Use your Supabase database for persistence
   - Run on port **8123** by default (not 2024)

### Option B: Using `langgraph dev` (Development Only)

`langgraph dev` is for local development and **uses in-memory storage by default**. It ignores `POSTGRES_URI` and does not persist data.

**⚠️ Important**: If you need persistence, use `langgraph up` instead.

If you still want to use `langgraph dev` for testing:
1. Run `setup_db.py` first to initialize the schema
2. Note that `langgraph dev` may still use in-memory storage
3. Data will NOT persist across restarts

## Step 6: Initialize Database Schema (Only for `langgraph up`)

**If using `langgraph up`**: You do NOT need to run `setup_db.py`. The server will automatically create the schema with proper migrations.

**If you previously ran `setup_db.py`** and are switching to `langgraph up`:
1. **You MUST clean up the old schema first**:
   ```bash
   uv run python cleanup_old_schema.py
   ```
   - This script drops all old tables created by `PostgresSaver.setup()`
   - It also removes migration tracking tables that may cause conflicts
   - **⚠️ WARNING**: This will delete all existing checkpoints and threads
   - The script will ask for confirmation before proceeding

2. **Why cleanup is necessary**:
   - `PostgresSaver.setup()` creates tables with `thread_id` as `text` type
   - `langgraph up` migrations expect `thread_id` as `uuid` type
   - Without cleanup, you'll get migration errors like: `Key columns "thread_id" and "thread_id" are of incompatible types: text and uuid`

3. **Then start `langgraph up`** as described in Step 5:
   ```bash
   POSTGRES_URI=$(grep "^POSTGRES_URI_CUSTOM=" .env | cut -d'=' -f2-)
   langgraph up --recreate --postgres-uri "$POSTGRES_URI"
   ```

## Step 7: Verify the Setup

1. **Start your LangGraph server using `langgraph up`**:
   ```bash
   cd deepagents-quickstarts/deep_research
   POSTGRES_URI=$(grep "^POSTGRES_URI_CUSTOM=" .env | cut -d'=' -f2-)
   langgraph up --recreate --postgres-uri "$POSTGRES_URI"
   ```
   
   **Important flags:**
   - `--recreate`: Forces Docker image rebuild (use when dependencies change)
   - `--postgres-uri`: Explicitly sets the database connection (optional if `POSTGRES_URI_CUSTOM` is in `.env`)

2. **You should see**:
   ```
   - API: http://localhost:8123
   - Docs: http://localhost:8123/docs
   - LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123
   ```
   **Note**: `langgraph up` uses port **8123** by default (not 2024 like `langgraph dev`)

3. **Check the logs for successful startup**:
   - ✅ `Using langgraph_runtime_postgres` (confirms Postgres is being used)
   - ✅ `Applied database migration` messages for migrations 1-5 (confirms schema was created)
   - ✅ `Postgres pool stats` (confirms database connection is active)
   - ✅ `Starting Postgres runtime` (confirms runtime is initialized)
   - ❌ No errors about missing tables, type mismatches, or migration failures
   - ❌ No `ModuleNotFoundError` for your dependencies

4. **Update your frontend configuration**:
   - If using the Deep Agents UI, set the **Deployment URL** to: `http://localhost:8123`
   - The **Assistant ID** should be the graph ID from your `langgraph.json` (e.g., `research`)
   - These settings are saved in browser localStorage

## Troubleshooting

### "Could not connect to Supabase database"

**Possible causes:**
- Incorrect password - try resetting it in Database Settings
- Wrong project reference - double-check your project ref in the URL
- Network/firewall issues - ensure your network can reach Supabase
- SSL mode mismatch - make sure `sslmode=require` is included

**Solution:**
1. Verify your connection string format
2. Test the connection string using a PostgreSQL client (like `psql`)
3. Check Supabase project status (make sure it's not paused)

### "Password authentication failed"

**Solution:**
1. Reset your database password in Database Settings
2. Update your `.env` file with the new password
3. Make sure there are no extra spaces or special characters

### "Connection refused" or "failed to resolve host"

**Possible causes:**
- Project is paused
- Network connectivity issues
- Wrong host/port
- Direct connection using IPv6 (not supported on your network)

**Solution:**
1. Check if your Supabase project is active (not paused)
2. **Use Session mode (pooler) connection string instead of Direct**
   - Direct connection (`db.*.supabase.co`) requires IPv6
   - Session mode (`aws-0-*.pooler.supabase.com`) works with IPv4
3. Verify the connection string host matches your project
4. Ensure you're using the correct region in the pooler URL

### "Migration failed" or "relation does not exist" errors

**Possible causes:**
- Old schema from `PostgresSaver.setup()` conflicts with `langgraph up` migrations
- Inconsistent migration state (migration tracking thinks migrations ran, but tables don't exist)
- Type mismatches (e.g., `thread_id` as `text` vs `uuid`)

**Common error messages:**
- `Key columns "thread_id" and "thread_id" are of incompatible types: text and uuid`
- `relation "checkpoints" does not exist` (when migration 5 tries to run but tables from migrations 1-4 don't exist)
- `Failed to apply database migration 5`

**Solution:**
1. **Clean up the old schema completely**:
   ```bash
   uv run python cleanup_old_schema.py
   ```
   - This drops ALL tables including migration tracking tables
   - Ensures a completely fresh start
   - The script will find and drop any LangGraph-related tables

2. **Restart with `--recreate`**:
   ```bash
   POSTGRES_URI=$(grep "^POSTGRES_URI_CUSTOM=" .env | cut -d'=' -f2-)
   langgraph up --recreate --postgres-uri "$POSTGRES_URI"
   ```
   - `--recreate` forces a fresh Docker build
   - `langgraph up` will run all migrations from the beginning (1-5)
   - All tables will be created with the correct schema

3. **Verify migrations completed**:
   - Check logs for: `Applied database migration` messages
   - Should see migrations 1, 2, 3, 4, and 5 all applied successfully
   - No errors about missing tables or type mismatches

### "ModuleNotFoundError" when using `langgraph up`

**Possible causes:**
- Dependencies not explicitly listed in `langgraph.json`
- Docker build not installing packages from `pyproject.toml`
- Docker image not rebuilt after adding dependencies

**Solution:**
1. **Add explicit dependencies to `langgraph.json`**:
   - `langgraph up` does NOT automatically install all dependencies from `pyproject.toml`
   - You must explicitly list all required packages in the `dependencies` array
   - Example:
     ```json
     {
       "dependencies": [
         ".",
         "langchain>=1.0.0",
         "langchain-google-genai>=3.1.0",
         "langchain-openai>=1.0.2",
         "langchain-anthropic>=1.0.3",
         "langchain-tavily>=0.2.13",
         "deepagents>=0.2.6",
         "python-dotenv>=1.0.0",
         "pydantic>=2.0.0",
         "tavily-python>=0.5.0",
         "markdownify>=1.2.0",
         "httpx>=0.28.1"
       ]
     }
     ```
   - Include ALL packages that your code imports, not just the main ones
   - The `"."` entry installs your local package, but explicit dependencies are still needed

2. **Rebuild the Docker image**:
   ```bash
   langgraph up --recreate
   ```
   - The `--recreate` flag forces a complete rebuild
   - This is required whenever you add or change dependencies in `langgraph.json`
   - Without `--recreate`, Docker may use cached layers that don't include new dependencies

3. **Verify dependencies are installed**:
   - Check the Docker build logs for the installation step
   - Look for: `RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system ...`
   - All packages listed in `dependencies` should appear in this command

### Can't Find the Connect Button

**Alternative:**
1. Go to Database → Settings
2. Look for "Connection string" or "Connection info" section
3. Or construct it manually using Method 2 from Step 3

## Security Best Practices

1. **Never commit your `.env` file to version control**
   - Add `.env` to your `.gitignore` file
   - Use `.env.example` (without real credentials) for documentation

2. **Use environment variables in production**
   - Don't hardcode credentials in your code
   - Use secure secret management (e.g., GitHub Secrets, AWS Secrets Manager)

3. **Rotate passwords regularly**
   - Reset your database password periodically
   - Update all applications using the old password

4. **Use SSL connections**
   - Always include `?sslmode=require` in your connection string
   - This encrypts data in transit

## Quick Reference

### Connection String Format

```
postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]?sslmode=require
```

### Default Values

- **User**: `postgres`
- **Database**: `postgres`
- **Port**: `5432` (Direct/Session) or `6543` (Transaction)
- **Host**: `db.[PROJECT_REF].supabase.co` (Direct) or `aws-0-[REGION].pooler.supabase.com` (Pooler)

### Where to Find Information

| Information | Location |
|------------|----------|
| Database Password | Database → Settings → Database password section |
| Connection String | Top navigation → Connect button |
| Project Reference | Dashboard URL or project settings |
| Connection Pooler Settings | Database → Settings → Connection pooling configuration |

## Important Notes

### `langgraph dev` vs `langgraph up`

| Feature | `langgraph dev` | `langgraph up` |
|---------|----------------|----------------|
| **Storage** | In-memory (default) | PostgreSQL (via `POSTGRES_URI_CUSTOM`) |
| **Persistence** | ❌ Data lost on restart | ✅ Data persists |
| **Port** | 2024 | 8123 (default) |
| **Use Case** | Local development/testing | Production deployment |
| **Schema Setup** | Requires `setup_db.py` | Automatic migrations |
| **Dependencies** | Installed from `pyproject.toml` | Must be explicit in `langgraph.json` |
| **Docker** | No Docker | Uses Docker containers |
| **Rebuild** | N/A | Use `--recreate` flag when dependencies change |

### Key Differences in Dependency Management

**`langgraph dev`:**
- Automatically installs dependencies from `pyproject.toml`
- No need to explicitly list dependencies
- Runs directly in your Python environment

**`langgraph up`:**
- **Requires explicit dependencies in `langgraph.json`**
- Does NOT automatically install all packages from `pyproject.toml`
- Builds a Docker image, so dependencies must be specified
- Use `--recreate` flag to rebuild when adding/removing dependencies

**For Supabase persistence, always use `langgraph up`.**

### Connection String Types

- **Direct Connection**: `db.[PROJECT_REF].supabase.co:5432`
  - Requires IPv6 support
  - May not work on all networks
  - Not recommended for LangGraph

- **Session Mode (Pooler)**: `aws-0-[REGION].pooler.supabase.com:5432` ✅ **Recommended**
  - Works with IPv4
  - More reliable
  - Better for persistent connections
  - Use this for `langgraph up`

## Next Steps

After completing this setup:

1. ✅ Your agent will now store all threads and checkpoints in Supabase
2. ✅ Data will persist across server restarts
3. ✅ You can view and manage checkpoints in your Supabase database
4. ✅ Multiple instances can share the same database
5. ✅ Use `langgraph up` for production deployments with Supabase

## Quick Troubleshooting Checklist

If something isn't working, check:

1. **Dependencies**:
   - ✅ All imported packages listed in `langgraph.json` dependencies?
   - ✅ Used `--recreate` flag after adding dependencies?
   - ✅ Check Docker build logs for package installation

2. **Database**:
   - ✅ `POSTGRES_URI_CUSTOM` set in `.env` file?
   - ✅ Using Session mode (pooler) connection string?
   - ✅ Ran `cleanup_old_schema.py` if switching from `setup_db.py`?
   - ✅ Check logs for successful migrations (1-5)

3. **Connection**:
   - ✅ Frontend configured with correct port (8123, not 2024)?
   - ✅ Assistant ID matches graph ID in `langgraph.json`?
   - ✅ Server logs show `Using langgraph_runtime_postgres`?

4. **Common Commands**:
   ```bash
   # Rebuild and start with Supabase
   POSTGRES_URI=$(grep "^POSTGRES_URI_CUSTOM=" .env | cut -d'=' -f2-)
   langgraph up --recreate --postgres-uri "$POSTGRES_URI"
   
   # Clean up old schema
   uv run python cleanup_old_schema.py
   
   # Check what's in your .env
   grep POSTGRES_URI_CUSTOM .env
   ```

## Advanced: Building Docker Images

If you want to build a Docker image separately (useful for CI/CD or custom deployments), use `langgraph build`:

```bash
langgraph build -t my-langgraph-image
```

### `langgraph build` Options

| Option | Default | Description | Example |
|--------|---------|-------------|---------|
| `-t, --tag TEXT` | *Required* | Tag for the Docker image | `langgraph build -t my-image` |
| `--platform TEXT` | | Target platform(s) to build for | `langgraph build --platform linux/amd64,linux/arm64` |
| `--pull / --no-pull` | `--pull` | Build with latest remote Docker image. Use `--no-pull` for locally built images | `langgraph build --no-pull -t my-image` |
| `-c, --config FILE` | `langgraph.json` | Path to configuration file | `langgraph build -c custom-config.json -t my-image` |
| `--build-command TEXT*` | | Build command to run from the `langgraph.json` directory | `langgraph build --build-command "yarn run turbo build" -t my-image` |
| `--install-command TEXT*` | | Install command to run from where you call `langgraph build` | `langgraph build --install-command "yarn install" -t my-image` |
| `--help` | | Display command documentation | `langgraph build --help` |

**Notes:**
- The `-t` (tag) option is **required** - you must specify a tag for your image
- `--build-command` runs from the directory where your `langgraph.json` file lives
- `--install-command` runs from the directory where you call `langgraph build` from
- Use `--no-pull` when you want to use locally built base images (faster builds)

### Examples

**Basic build:**
```bash
# Build image with custom tag
langgraph build -t deep-research-agent:latest
```

**Multi-platform build (for different architectures):**
```bash
# Build for both AMD64 and ARM64
langgraph build -t deep-research-agent:latest --platform linux/amd64,linux/arm64
```

**Build with custom install/build commands:**
```bash
# If you need custom installation steps
langgraph build -t my-agent \
  --install-command "pip install -r requirements.txt" \
  --build-command "python setup.py build"
```

**Build without pulling latest base image:**
```bash
# Use locally cached base images (faster)
langgraph build --no-pull -t deep-research-agent:latest
```

**Use the built image with `langgraph up`:**
```bash
# Build the image first
langgraph build -t deep-research-agent:latest

# Then use it with langgraph up (skips building)
POSTGRES_URI=$(grep "^POSTGRES_URI_CUSTOM=" .env | cut -d'=' -f2-)
langgraph up --image deep-research-agent:latest --postgres-uri "$POSTGRES_URI"
```

**When to use `langgraph build`:**
- ✅ CI/CD pipelines where you want to build images separately
- ✅ Building for multiple platforms/architectures
- ✅ Custom build processes that need specific commands
- ✅ Pre-building images to speed up deployments
- ✅ Sharing images across different environments

**Note**: When using `--image` with `langgraph up`, it skips building and uses the pre-built image directly. This is useful when you've already built the image and want to avoid rebuilding.

### Why Redis is Required

**Redis is used by LangGraph for:**
- **Checkpoint management**: Efficient storage and retrieval of agent state checkpoints
- **Memory management**: Short-term and long-term memory storage for agents
- **Low-latency operations**: Fast in-memory operations for real-time agent interactions
- **Distributed coordination**: Managing state across multiple instances

**For `langgraph up` with Postgres runtime**: Redis is **required** - the Postgres runtime uses Redis for checkpoint coordination and caching.

**For `langgraph dev`**: Redis is **not required** - it uses in-memory storage by default.

**Important**: Redis is a **service** (like PostgreSQL), not a Python package. You do **NOT** need to add Redis to your `pyproject.toml` file. The Redis Python client libraries are already included in the LangGraph Docker base image. When you use `langgraph up`, it automatically runs Redis as a separate container/service.

### Running Without Redis (Using `langgraph dev`)

If you want to avoid Redis, you can use `langgraph dev` instead, but note:
- ❌ Data will NOT persist (in-memory only)
- ❌ Not suitable for production
- ✅ No Redis required
- ✅ Simpler setup

```bash
# No Redis needed!
cd deepagents-quickstarts/deep_research
langgraph dev
```

**Note**: `langgraph dev` uses in-memory storage and ignores `POSTGRES_URI_CUSTOM`. For persistence with Supabase, you must use `langgraph up` which requires Redis.

### Running Docker Image Directly (Without `langgraph up`)

You can run your built Docker image directly using `docker run` or `docker compose`, but you'll need to handle environment variables and dependencies manually. **Note: Redis is required for the Postgres runtime.**

#### Option 1: Using `docker run` (Requires Redis separately)

**Prerequisites:**
- Redis must be running (either locally or in another container)
- All environment variables must be passed

**Basic command (using Docker network - recommended):**
```bash
# Create a Docker network
docker network create langgraph-net

# Start Redis in the network
docker run -d --name redis --network langgraph-net -p 6379:6379 redis:7-alpine

# Then start LangGraph API in the same network
docker run -d \
  --name langgraph-api \
  --network langgraph-net \
  -p 8123:8000 \
  -e POSTGRES_URI="postgresql://postgres.ltbwpsjgivrwxoevnolj:password@aws-1-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require" \
  -e LANGSMITH_API_KEY="your_langsmith_key" \
  -e LANGCHAIN_TRACING_V2="false" \
  -e LANGSMITH_TRACING="false" \
  -e REDIS_URI="redis://redis:6379" \
  -e TAVILY_API_KEY="your_tavily_key" \
  -e OPENAI_API_KEY="your_openai_key" \
  test-docker:latest
```

**Important notes:**
- Use `POSTGRES_URI` (not `POSTGRES_URI_CUSTOM`) when running directly with Docker
- Use `REDIS_URI` (not `REDIS_URL`) 
- Port mapping is `8123:8000` (host:container) - the server runs on port 8000 inside the container
- Use `--network` to connect containers - this is more reliable than `host.docker.internal`
- Use `redis://redis:6379` (container name) when both containers are on the same network

**With environment file:**
```bash
# Create a Docker network
docker network create langgraph-net

# Start Redis in the network
docker run -d --name redis --network langgraph-net -p 6379:6379 redis:7-alpine

# Load environment variables from .env file
set -a
source .env
set +a

# Convert POSTGRES_URI_CUSTOM to POSTGRES_URI (required by container)
POSTGRES_URI="$POSTGRES_URI_CUSTOM"

docker run -d \
  --name langgraph-api \
  --network langgraph-net \
  -p 8123:8000 \
  -e POSTGRES_URI="$POSTGRES_URI" \
  -e LANGSMITH_API_KEY="$LANGSMITH_API_KEY" \
  -e LANGCHAIN_TRACING_V2="${LANGCHAIN_TRACING_V2:-false}" \
  -e LANGSMITH_TRACING="${LANGSMITH_TRACING:-false}" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e TAVILY_API_KEY="$TAVILY_API_KEY" \
  -e REDIS_URI="redis://redis:6379" \
  test-docker:latest
```

**Note**: 
- Use Docker networking (`--network`) for reliable container-to-container communication
- Use `redis://redis:6379` (container name) when both containers are on the same network
- The container expects `POSTGRES_URI`, not `POSTGRES_URI_CUSTOM`
- Port mapping is `8123:8000` because the server runs on port 8000 inside the container

#### Option 2: Using `docker compose` (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  langgraph-api:
    image: test-docker:latest
    ports:
      - "8123:8000"
    environment:
      - POSTGRES_URI=${POSTGRES_URI_CUSTOM}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2:-false}
      - LANGSMITH_TRACING=${LANGSMITH_TRACING:-false}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - REDIS_URI=redis://redis:6379
    depends_on:
      - redis
    env_file:
      - .env

volumes:
  redis-data:
```

**Run with docker compose:**
```bash
docker compose up -d
```

**Stop:**
```bash
docker compose down
```

#### Option 3: Using `docker run` with Docker network (Same as Option 1)

This is the same approach as Option 1 above. Using Docker networking is the recommended method for connecting containers.

**Key points:**
- Create a Docker network: `docker network create langgraph-net`
- Start Redis in the network: `--network langgraph-net`
- Start LangGraph API in the same network: `--network langgraph-net`
- Use container name for Redis: `redis://redis:6379` (not `host.docker.internal`)
- This is more reliable than `host.docker.internal` which doesn't work on all systems

#### Required Environment Variables

When running directly with Docker, you need these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_URI` | ✅ Yes | Supabase database connection string (use `POSTGRES_URI`, not `POSTGRES_URI_CUSTOM`) |
| `LANGSMITH_API_KEY` | ✅ Yes | LangSmith API key (required for self-hosted lite license, even if tracing disabled) |
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key (if using OpenAI models) |
| `TAVILY_API_KEY` | ✅ Yes | Tavily API key (required for search functionality) |
| `REDIS_URI` | ✅ Yes | Redis connection URL (use `REDIS_URI`, not `REDIS_URL`) |
| `ANTHROPIC_API_KEY` | ⚠️ Optional | Anthropic API key (if using Claude) |
| `LANGCHAIN_TRACING_V2` | ⚠️ Optional | Set to `false` to disable LangSmith tracing (default: enabled) |
| `LANGSMITH_TRACING` | ⚠️ Optional | Set to `false` to disable LangSmith tracing (alternative to `LANGCHAIN_TRACING_V2`) |

**Important**: When running with `docker run` directly:
- Use `POSTGRES_URI` (not `POSTGRES_URI_CUSTOM`)
- Use `REDIS_URI` (not `REDIS_URL`)
- Port mapping should be `8123:8000` (host:container)
- `LANGSMITH_API_KEY` is still required even if tracing is disabled (needed for license verification)

#### Why Use `langgraph up` Instead?

**Advantages of `langgraph up`:**
- ✅ Automatically sets up Redis (required for Postgres runtime)
- ✅ Handles networking between services
- ✅ Reads environment from `.env` file automatically
- ✅ Manages container lifecycle
- ✅ Handles health checks and restarts
- ✅ Simpler command line
- ✅ Properly configures all required services

**When to run directly:**
- ✅ Custom orchestration (Kubernetes, ECS, etc.)
- ✅ CI/CD pipelines with specific requirements
- ✅ Integration with existing Docker infrastructure
- ✅ Need fine-grained control over container configuration
- ⚠️ **Note**: You still need Redis - it's required for the Postgres runtime

**Alternative: Use `langgraph dev` to avoid Redis:**
- ✅ No Redis required
- ✅ Simpler setup
- ❌ No persistence (in-memory only)
- ❌ Not for production use

## Important `langgraph up` Flags

| Flag | Description | When to Use |
|------|-------------|-------------|
| `--recreate` | Recreate containers even if configuration hasn't changed | After changing dependencies in `langgraph.json` |
| `--postgres-uri TEXT` | Explicitly set Postgres URI | When `.env` file isn't being read or for CI/CD |
| `--port INTEGER` | Set custom port (default: 8123) | When port 8123 is already in use |
| `--pull / --no-pull` | Pull latest images (default: `--pull`) | Use `--no-pull` with locally built images |
| `--wait` | Wait for services to start before returning | For scripts that need to wait for readiness |
| `--verbose` | Show more output from server logs | When debugging issues |

**Example with multiple flags:**
```bash
langgraph up --recreate --postgres-uri "$POSTGRES_URI" --port 9000 --verbose
```

## Dockerfile for AWS Deployment

A standalone `Dockerfile` is included in this project for AWS deployment (ECS, EKS, EC2, etc.).

**Build the image:**
```bash
docker build -t deep-research-agent:latest .
```

**Test locally with docker-compose:**
```bash
docker compose -f docker-compose.aws.yml up
```

**For detailed AWS deployment instructions**, see `AWS_DEPLOYMENT.md` which includes:
- ECS (Fargate) deployment
- EKS (Kubernetes) deployment
- EC2 deployment
- ElastiCache Redis setup
- Secrets management
- Monitoring and logging

## Disabling LangSmith Tracing

If you want to keep the free self-hosted lite license but disable tracing/observability:

### Understanding the Requirements

- ✅ **`LANGSMITH_API_KEY` is still required** - Even if tracing is disabled, the API key is needed for license verification (self-hosted lite mode)
- ✅ **Tracing can be disabled** - You can prevent data from being sent to LangSmith while keeping the license
- ⚠️ **To completely remove LangSmith** - You need an enterprise license (`LANGGRAPH_CLOUD_LICENSE_KEY`)

### How to Disable Tracing

**Option 1: In `.env` file (Recommended)**

Add these lines to your `.env` file:

```bash
# Required for self-hosted lite license (even if tracing disabled)
LANGSMITH_API_KEY=lsv2_pt_...

# Disable tracing/observability
LANGCHAIN_TRACING_V2=false
LANGSMITH_TRACING=false
```

**Option 2: In Docker run command**

```bash
docker run -d \
  --name langgraph-api \
  --network langgraph-net \
  -p 8123:8000 \
  -e POSTGRES_URI="..." \
  -e REDIS_URI="redis://redis:6379" \
  -e LANGSMITH_API_KEY="lsv2_pt_..." \  # Still needed for license
  -e LANGCHAIN_TRACING_V2="false" \      # Disable tracing
  -e LANGSMITH_TRACING="false" \         # Also disable (optional)
  -e OPENAI_API_KEY="..." \
  -e TAVILY_API_KEY="..." \
  deep-research-agent:latest
```

**Option 3: In Docker Compose**

```yaml
services:
  langgraph-api:
    environment:
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LANGCHAIN_TRACING_V2=false
      - LANGSMITH_TRACING=false
```

**Option 4: In AWS ECS/EKS**

Add to your task definition or ConfigMap:

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

### Verifying Tracing is Disabled

**1. Check logs:**
```bash
# Should NOT see LangSmith API calls for tracing
docker logs langgraph-api | grep "api.smith.langchain.com"
# Should return nothing (or only license verification, not tracing)

# With tracing enabled, you'd see:
# "HTTP Request: POST https://api.smith.langchain.com/v1/traces"
# With tracing disabled, you won't see these calls
```

**2. Test the API:**
```bash
# Make a request
curl http://localhost:8123/

# Check LangSmith dashboard - should NOT see new traces
```

**3. Use the test script:**
```bash
cd deepagents-quickstarts/deep_research
./test-tracing-disabled.sh
```

### Important Notes

- **License verification still requires `LANGSMITH_API_KEY`** - Even with tracing disabled, the API key is needed for the self-hosted lite license
- **Both variables work** - You can use `LANGCHAIN_TRACING_V2=false` or `LANGSMITH_TRACING=false` (or both)
- **No data sent to LangSmith** - When disabled, no trace data is sent, but license verification still occurs
- **Enterprise license removes dependency** - To completely remove LangSmith, you need `LANGGRAPH_CLOUD_LICENSE_KEY` (requires contacting LangChain sales)

For more details, see `LANGSMITH_LICENSE_GUIDE.md`.

## Additional Resources

- [Supabase Database Connection Docs](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [LangGraph Checkpoint Documentation](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- [PostgreSQL Connection String Format](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [LangGraph CLI Documentation](https://langchain-ai.github.io/langgraph/platform/langgraph-cli/)
- [AWS Deployment Guide](./AWS_DEPLOYMENT.md) - Complete guide for deploying to AWS
- [LangSmith License Guide](./LANGSMITH_LICENSE_GUIDE.md) - Understanding license requirements and tracing

---

**Need Help?** If you encounter issues not covered here, check:
1. Supabase project status and logs
2. LangGraph server logs for detailed error messages
3. Network connectivity to Supabase servers

