# Dockerfile for LangGraph Deep Research Agent
# This Dockerfile is optimized for AWS deployment (ECS, EKS, EC2, etc.)
#
# IMPORTANT: This Dockerfile only builds the LangGraph API image.
# Redis must be deployed separately (e.g., AWS ElastiCache, separate container, etc.)
# The REDIS_URI environment variable must point to your Redis instance.
#
# ENVIRONMENT VARIABLES:
# Environment variables are NOT hardcoded in this Dockerfile for security reasons.
# They must be provided at runtime via:
#   - Docker: -e KEY=value or --env-file .env
#   - ECS: Task definition environment section
#   - EKS: ConfigMap/Secrets
#   - docker-compose: environment: or env_file: sections
#
# Required environment variables:
#   - POSTGRES_URI: PostgreSQL/Supabase connection string
#   - REDIS_URI: Redis connection string (e.g., redis://host:6379)
#   - OPENAI_API_KEY: OpenAI API key
#   - TAVILY_API_KEY: Tavily search API key
#   - LANGSMITH_API_KEY: LangSmith API key (required for self-hosted lite license, even if tracing disabled)
#   - LANGGRAPH_CLOUD_LICENSE_KEY: Enterprise license key (alternative to LANGSMITH_API_KEY)
#
# Optional environment variables:
#   - ANTHROPIC_API_KEY: If using Claude models
#   - LANGGRAPH_CLOUD_LICENSE_KEY: For enterprise features

# Use the official LangGraph API base image
FROM langchain/langgraph-api:3.11

# Set working directory
WORKDIR /deps/deep_research

# Copy project files
COPY . /deps/deep_research

# Install dependencies explicitly (matching langgraph.json)
# Using uv pip for faster, more reliable installs
# Install all dependencies first, then install local package
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir \
    langchain>=1.0.0 \
    langchain-google-genai>=3.1.0 \
    langchain-openai>=1.0.2 \
    langchain-anthropic>=1.0.3 \
    langchain-tavily>=0.2.13 \
    deepagents>=0.2.6 \
    python-dotenv>=1.0.0 \
    pydantic>=2.0.0 \
    tavily-python>=0.5.0 \
    markdownify>=1.2.0 \
    httpx>=0.28.1 \
    fastapi>=0.100.0

# Install local package in editable mode
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -e .

# Expose the API port (LangGraph runs on port 8000 inside container)
EXPOSE 8000

# Health check for AWS ECS/EKS
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/docs', timeout=5)" || exit 1

# The base image already has the entrypoint configured
# It will automatically detect langgraph.json and start the server
# No need to specify CMD or ENTRYPOINT

