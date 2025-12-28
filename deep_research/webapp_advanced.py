"""Advanced example: Using create_app pattern with full control.

This shows how you could use create_app to get the base LangGraph app
and then extend it with your custom routes. However, note that when using
langgraph.json with the "http.app" configuration, LangGraph automatically
handles the integration.

The key insight: You can create parallel endpoints by:
1. Using APIRouter to organize your custom routes
2. Adding routes directly to your FastAPI app
3. LangGraph will mount/integrate your app alongside its defaults
"""

from fastapi import FastAPI, APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import os
from datetime import datetime

# ============================================================================
# Custom Router Pattern (Recommended for parallel routes)
# ============================================================================

# Create a router for custom API endpoints
# Using a router makes it easier to organize and maintain parallel routes
custom_api_router = APIRouter(
    prefix="/api/v1",
    tags=["custom-api"],
    responses={404: {"description": "Not found"}},
)


@custom_api_router.get("/health")
async def health_check():
    """Health check endpoint - works in parallel with LangGraph defaults."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "research-agent",
    }


@custom_api_router.get("/stats")
async def get_stats():
    """Get deployment statistics."""
    return {
        "agent_name": "research",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "has_tavily": bool(os.getenv("TAVILY_API_KEY")),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@custom_api_router.post("/custom-action")
async def custom_action(data: Dict[str, Any]):
    """Custom POST endpoint example."""
    return {
        "received": data,
        "processed_at": datetime.now().isoformat(),
        "message": "Custom action processed successfully",
    }


@custom_api_router.get("/threads/{thread_id}/custom-summary")
async def custom_thread_summary(thread_id: str):
    """
    Custom thread endpoint - works in parallel with LangGraph's /threads.
    
    Note: This is a custom endpoint. LangGraph's default /threads endpoint
    still works at /threads. This is an example of parallel routes.
    """
    return {
        "thread_id": thread_id,
        "custom_summary": "This is a custom endpoint",
        "note": "LangGraph's /threads endpoint still works normally",
    }


# ============================================================================
# Admin Router (Example of multiple parallel route groups)
# ============================================================================

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    # You could add authentication here
    # dependencies=[Depends(verify_admin_token)],
)


@admin_router.get("/status")
async def admin_status():
    """Admin-only status endpoint."""
    return {
        "admin": True,
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# Main FastAPI App
# ============================================================================

app = FastAPI(
    title="Research Agent - Advanced Custom Routes",
    description="Example showing parallel routes using router pattern",
    version="1.0.0",
)

# Include all your custom routers
# These routes will work in parallel with LangGraph's default routes
app.include_router(custom_api_router)
app.include_router(admin_router)

# You can also add routes directly to the app
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Research Agent API",
        "langgraph_endpoints": "Available at /threads, /assistants, /docs, etc.",
        "custom_endpoints": "Available at /api/v1/* and /admin/*",
    }


@app.get("/hello")
async def hello():
    """Simple hello endpoint."""
    return {"Hello": "World", "message": "Custom endpoint working!"}


# ============================================================================
# Notes on create_app pattern:
# ============================================================================
#
# If you wanted to use create_app directly (not via langgraph.json), you would:
#
# 1. Import create_app:
#    from langgraph_api.server import create_app
#    # or
#    from langgraph.server import create_app
#
# 2. Create the LangGraph app:
#    langgraph_app = create_app(config)
#
# 3. Option A: Add routes to LangGraph's app:
#    langgraph_app.get("/custom")(custom_handler)
#    app = langgraph_app
#
# 3. Option B: Mount LangGraph app in your app:
#    app = FastAPI()
#    app.mount("/", langgraph_app)  # LangGraph routes at root
#    app.get("/custom")(custom_handler)  # Your routes also at root
#
# However, when using langgraph.json with "http.app", LangGraph CLI
# automatically handles this integration for you, so you just need to
# create your FastAPI app with your routes, and LangGraph will mount
# everything correctly.
#
# The key benefit of the router pattern shown above is that it makes
# it very clear which routes are yours vs LangGraph's defaults, and
# you can organize them by concern (API, admin, etc.).

