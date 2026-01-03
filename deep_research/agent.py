"""Research Agent - Standalone script for LangGraph deployment.

This module creates a deep research agent with custom tools and prompts
for conducting web research with strategic thinking and context management.

The agent supports runtime configuration through context schema, allowing
dynamic model and tool selection without redeploying the graph.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
# PostgresSaver import removed - LangGraph server handles persistence via POSTGRES_URI
from deepagents import create_deep_agent
from langgraph.runtime import Runtime

from research_agent.prompts import (
    RESEARCHER_INSTRUCTIONS,
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from research_agent.tools import tavily_search, think_tool

# Configuration Schema for Runtime Context
@dataclass
class Context:
    """Runtime context schema for agent configuration.
    
    This allows dynamic configuration of model and tools per-run without
    creating new assistants. Values are passed via config.configurable
    when creating runs.
    """
    model_name: str = "openai:gpt-4o"
    selected_tools: list[str] = None  # None means use all available tools
    
    def __post_init__(self):
        if self.selected_tools is None:
            self.selected_tools = ["tavily_search", "think_tool"]

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

# Available tools mapping
AVAILABLE_TOOLS = {
    "tavily_search": tavily_search,
    "think_tool": think_tool,
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

def get_model_from_name(model_name: str):
    """Initialize a model from a model name string.
    
    Supports formats:
    - "openai:gpt-4o" or "gpt-4o" -> ChatOpenAI
    - "anthropic:claude-sonnet-4-5" or "claude-sonnet-4-5" -> ChatAnthropic
    - "google:gemini-3-pro-preview" or "gemini-3-pro-preview" -> ChatGoogleGenerativeAI
    
    Args:
        model_name: Model identifier string
        
    Returns:
        Initialized chat model
    """
    # Remove provider prefix if present
    if ":" in model_name:
        provider, model_id = model_name.split(":", 1)
    else:
        provider = None
        model_id = model_name
    
    # Normalize provider
    if provider:
        provider = provider.lower()
    elif model_id.startswith("gpt"):
        provider = "openai"
    elif model_id.startswith("claude"):
        provider = "anthropic"
    elif model_id.startswith("gemini"):
        provider = "google"
    
    # Initialize appropriate model
    if provider == "openai":
        return ChatOpenAI(model=model_id)
    elif provider == "anthropic":
        return init_chat_model(f"anthropic:{model_id}")
    elif provider == "google":
        return ChatGoogleGenerativeAI(model=model_id, temperature=0.0)
    else:
        # Fallback: try init_chat_model with full string
        return init_chat_model(model_name)


async def make_graph(config: dict = None):
    """Create the research agent graph with runtime configuration.
    
    This function is called by LangGraph server to create the graph dynamically.
    Configuration is read from config.configurable parameter.
    
    To use this, update langgraph.json to reference:
    "research": "./agent.py:make_graph"
    
    Args:
        config: RunnableConfig dict containing configurable values.
                The configurable dict should contain model_name and selected_tools.
                If None, uses default configuration.
    
    Returns:
        Compiled graph ready for execution
    """
    # Get configuration from config dict
    if config is not None and isinstance(config, dict):
        configurable = config.get("configurable", {})
        
        # Extract our custom configuration values
        model_name = configurable.get("model_name", "openai:gpt-4o")
        
        # Check if selected_tools was explicitly provided (even if empty)
        if "selected_tools" in configurable:
            selected_tools_names = configurable.get("selected_tools", [])
            tools_explicitly_provided = True
        else:
            # Not provided - use default (all tools)
            selected_tools_names = ["tavily_search", "think_tool"]
            tools_explicitly_provided = False
        
        # Only log if custom config is provided (not defaults)
        if "model_name" in configurable or tools_explicitly_provided:
            print(f"🔧 make_graph() - Using config: model={model_name}, tools={selected_tools_names}")
    else:
        # Default configuration when config is not available
        model_name = "openai:gpt-4o"
        selected_tools_names = ["tavily_search", "think_tool"]
        tools_explicitly_provided = False
    
    # Initialize model
    model = get_model_from_name(model_name)
    
    # Select tools based on configuration
    selected_tools = []
    for tool_name in selected_tools_names:
        if tool_name in AVAILABLE_TOOLS:
            selected_tools.append(AVAILABLE_TOOLS[tool_name])
        else:
            print(f"⚠️  Warning: Tool '{tool_name}' not found. Available: {list(AVAILABLE_TOOLS.keys())}")
    
    # If no valid tools selected:
    # - If user explicitly provided empty list: use no tools (respect user choice)
    # - If not provided (default): use all available tools
    if not selected_tools:
        if tools_explicitly_provided and selected_tools_names == []:
            # User explicitly deselected all tools - respect their choice
            print("ℹ️  No tools selected by user. Running without tools.")
        else:
            # Default case or invalid tools: use all available tools
            print("ℹ️  Using all available tools (default).")
            selected_tools = list(AVAILABLE_TOOLS.values())
    
    # Create research sub-agent with selected tools
    research_sub_agent = {
        "name": "research-agent",
        "description": "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
        "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
        "tools": selected_tools,
    }
    
    # Create the agent without a checkpointer
    # The LangGraph server will handle persistence automatically using POSTGRES_URI
    agent = create_deep_agent(
        model=model,
        tools=selected_tools,
        system_prompt=INSTRUCTIONS,
        subagents=[research_sub_agent],
        context_schema=Context,
        # Don't pass checkpointer - LangGraph server handles it via POSTGRES_URI
    )
    
    return agent


# Note: The static agent variable is NOT needed when using make_graph()
# langgraph.json now references "./agent.py:make_graph" which creates graphs dynamically
# per-run with the configuration from config.configurable
#
# If you need to switch back to a static agent (not recommended for dynamic config),
# change langgraph.json to: "research": "./agent.py:agent"
# and uncomment the code below to create a static agent variable.

# For backward compatibility only (not used when langgraph.json uses make_graph):
# Uncomment below if you need a static agent variable
# _default_model = get_model_from_name("openai:gpt-4o")
# _default_tools = list(AVAILABLE_TOOLS.values())
# _default_research_sub_agent = {
#     "name": "research-agent",
#     "description": "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
#     "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
#     "tools": _default_tools,
# }
# agent = create_deep_agent(
#     model=_default_model,
#     tools=_default_tools,
#     system_prompt=INSTRUCTIONS,
#     subagents=[_default_research_sub_agent],
#     context_schema=Context,
# )
