#!/bin/bash
# Final docker run command - uses environment variables from .env file
# IMPORTANT: Never commit secrets! Use environment variables or .env file

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

docker stop langgraph-api 2>/dev/null
docker rm langgraph-api 2>/dev/null

docker run -d \
  --name langgraph-api \
  --network langgraph-test-net \
  --env-file .env \
  -e LANGSMITH_LANGGRAPH_API_VARIANT="${LANGSMITH_LANGGRAPH_API_VARIANT:-local_dev}" \
  -e POSTGRES_URI="${POSTGRES_URI:-${POSTGRES_URI_CUSTOM}}" \
  -e REDIS_URI="${REDIS_URI:-redis://redis-test:6379}" \
  -e LANGGRAPH_HTTP="${LANGGRAPH_HTTP:-'{\"app\": \"/api/webapp_advanced.py:app\"}'}" \
  -e LANGGRAPH_AUTH="${LANGGRAPH_AUTH:-'{\"path\": \"/api/security/auth.py:auth\"}'}" \
  -e SUPABASE_URL="${SUPABASE_URL}" \
  -e SUPABASE_SERVICE_KEY="${SUPABASE_SERVICE_KEY}" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e TAVILY_API_KEY="${TAVILY_API_KEY}" \
  -e LANGSMITH_API_KEY="${LANGSMITH_API_KEY}" \
  -e LANGSMITH_TRACING="${LANGSMITH_TRACING:-false}" \
  -e LANGSMITH_PROJECT="${LANGSMITH_PROJECT:-deep-agents-from-scratch}" \
  -p 8123:8000 \
  test-docker:latest

echo "✅ Container started"
echo "Check logs with: docker logs -f langgraph-api"
echo ""
echo "Note: Make sure your .env file contains all required API keys:"
echo "  - OPENAI_API_KEY"
echo "  - TAVILY_API_KEY"
echo "  - LANGSMITH_API_KEY"
echo "  - POSTGRES_URI or POSTGRES_URI_CUSTOM"
echo "  - SUPABASE_URL (if using auth)"
echo "  - SUPABASE_SERVICE_KEY (if using auth)"
