"""Research Agent - Standalone script for LangGraph deployment.

This module creates a deep research agent with custom tools and prompts
for conducting web research with strategic thinking and context management.
"""

import os
from datetime import datetime

from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
# PostgresSaver import removed - LangGraph server handles persistence via POSTGRES_URI
from deepagents import create_deep_agent

from research_agent.prompts import (
    RESEARCHER_INSTRUCTIONS,
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from research_agent.tools import tavily_search, think_tool

# Limits
max_concurrent_research_units = 3
max_researcher_iterations = 3

# Get current date
current_date = datetime.now().strftime("%Y-%m-%d")

# Combine orchestrator instructions (RESEARCHER_INSTRUCTIONS only for sub-agents)
INSTRUCTIONS = (
    RESEARCH_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_research_units,
        max_researcher_iterations=max_researcher_iterations,
    )
)

# Create research sub-agent
research_sub_agent = {
    "name": "research-agent",
    "description": "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
    "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [tavily_search, think_tool],
}

# Model Gemini 3 
# model = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)

# Model Claude 4.5
#model = init_chat_model(ChatOpenAI(model="gpt-4o"))

# Setup checkpointer for Supabase (Postgres) persistence
# NOTE: When using langgraph dev, the server automatically handles persistence.
# Instead of passing a checkpointer to create_deep_agent, set the POSTGRES_URI
# environment variable. The LangGraph server will use it automatically.
#
# For local development without langgraph dev, you can still use a custom checkpointer.
# Set USE_CUSTOM_CHECKPOINTER=true to enable this.

# Get database connection string from environment variable
DB_URI = os.getenv("SUPABASE_DB_URI")
if not DB_URI:
    # Fallback: construct from individual Supabase connection parameters
    supabase_host = os.getenv("SUPABASE_DB_HOST")
    supabase_port = os.getenv("SUPABASE_DB_PORT", "5432")
    supabase_db = os.getenv("SUPABASE_DB_NAME", "postgres")
    supabase_user = os.getenv("SUPABASE_DB_USER", "postgres")
    supabase_password = os.getenv("SUPABASE_DB_PASSWORD", "")
    
    # Only construct connection string if we have a host
    if supabase_host:
        if supabase_password:
            DB_URI = f"postgresql://{supabase_user}:{supabase_password}@{supabase_host}:{supabase_port}/{supabase_db}?sslmode=require"
        else:
            # If no password provided, use default (for local development)
            DB_URI = f"postgresql://{supabase_user}@{supabase_host}:{supabase_port}/{supabase_db}?sslmode=disable"

# Ensure sslmode is set if not present
if DB_URI and "sslmode" not in DB_URI:
    separator = "&" if "?" in DB_URI else "?"
    DB_URI = f"{DB_URI}{separator}sslmode=require"

# Check for Postgres URI (try both POSTGRES_URI and POSTGRES_URI_CUSTOM)
# Note: langgraph dev uses in-memory by default. For Postgres persistence,
# you may need to use langgraph up for deployment, or manually configure checkpointer.
POSTGRES_URI = os.getenv("POSTGRES_URI_CUSTOM") or os.getenv("POSTGRES_URI")
if not POSTGRES_URI and DB_URI:
    # If POSTGRES_URI is not set but we have DB_URI, set it
    # Try both variable names for compatibility
    os.environ["POSTGRES_URI"] = DB_URI
    os.environ["POSTGRES_URI_CUSTOM"] = DB_URI
    POSTGRES_URI = DB_URI
    print("⚠️  NOTE: langgraph dev defaults to in-memory storage.")
    print("   Set POSTGRES_URI_CUSTOM in .env for deployment with langgraph up")
    print(f"   POSTGRES_URI_CUSTOM={DB_URI}")
elif POSTGRES_URI:
    print(f"✓ Postgres URI found - Will be used if server supports it")
    print(f"  Database: {POSTGRES_URI.split('@')[1] if '@' in POSTGRES_URI else 'configured'}")
    print("  ⚠️  Note: langgraph dev may still use in-memory storage")
    print("     For Postgres persistence, consider using langgraph up for deployment")
else:
    print("⚠️  No database configuration found.")
    print("   Set POSTGRES_URI_CUSTOM in your .env file")

# Create the agent without a checkpointer
# The LangGraph server will handle persistence automatically using POSTGRES_URI
agent = create_deep_agent(
    model=ChatOpenAI(model="gpt-4o"),
    tools=[tavily_search, think_tool],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
    # Don't pass checkpointer - LangGraph server handles it via POSTGRES_URI
)
