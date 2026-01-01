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

from fastapi import FastAPI, APIRouter, Depends, Request, HTTPException
from typing import Dict, Any, Optional
from starlette.authentication import BaseUser
import os
from datetime import datetime

# Try to import get_auth_ctx for fallback user access
try:
    from langgraph_api.utils import get_auth_ctx
    HAS_AUTH_CTX = True
except ImportError:
    HAS_AUTH_CTX = False

# Import the auth function for manual authentication
# We need to import the actual function from the auth instance
try:
    from security.auth import auth as auth_instance
    # The @auth.authenticate decorator stores the function in _authenticate_handler
    if hasattr(auth_instance, '_authenticate_handler') and auth_instance._authenticate_handler:
        authenticate_fn = auth_instance._authenticate_handler
        HAS_AUTH_FN = True
    else:
        HAS_AUTH_FN = False
        authenticate_fn = None
except (ImportError, AttributeError):
    HAS_AUTH_FN = False
    authenticate_fn = None

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


# ============================================================================
# Authentication Dependency
# ============================================================================

async def get_current_user(request: Request) -> BaseUser:
    """Dependency to get the current authenticated user.
    
    With `enable_custom_route_auth: true` in langgraph.json, LangGraph's authentication
    middleware is automatically applied to custom routes. The authenticated user is stored
    in request.scope["user"] by LangGraph's authentication middleware.
    
    This dependency provides a simple way to access the authenticated user in route handlers.
    If the middleware didn't set the user, it falls back to manual authentication.
    
    Raises:
        HTTPException: 401 if user is not authenticated
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Try to get user from scope (set by middleware if enable_custom_route_auth works)
    user = request.scope.get("user")
    
    # Fallback to auth context if available (used by LangGraph internally)
    if not user and HAS_AUTH_CTX:
        ctx = get_auth_ctx()
        if ctx and ctx.user:
            user = ctx.user
    
    # If user still not found, manually authenticate using the auth function
    # This is the reliable fallback that ensures authentication works
    if not user and HAS_AUTH_FN and authenticate_fn:
        # Extract authorization header
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        
        if auth_header:
            try:
                # Call the Supabase auth function directly
                # This is the reliable authentication method for custom routes
                user_dict = await authenticate_fn(auth_header)
                
                # Convert dict to BaseUser-like object using LangGraph's normalize_user
                from langgraph_api.auth.custom import normalize_user
                user = normalize_user(user_dict)
            except HTTPException:
                # Re-raise FastAPI HTTPException as-is
                raise
            except Exception as e:
                logger.error(f"Manual authentication failed: {str(e)}", exc_info=True)
                # Handle Auth.exceptions.HTTPException from the auth function
                from langgraph_sdk import Auth
                if isinstance(e, Auth.exceptions.HTTPException):
                    raise HTTPException(
                        status_code=e.status_code,
                        detail=e.detail
                    )
                # For other exceptions, raise 401
                raise HTTPException(
                    status_code=401,
                    detail=f"Authentication failed: {str(e)}"
                )
    
    if not user or not hasattr(user, "identity"):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return user


@custom_api_router.get("/health")
async def health_check():
    """Health check endpoint - works in parallel with LangGraph defaults."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "research-agent",
    }


@custom_api_router.get("/stats")
async def get_stats(user: BaseUser = Depends(get_current_user)):
    """Get deployment statistics with user information.
    
    This endpoint requires authentication via Bearer token in the Authorization header.
    Returns deployment stats along with the authenticated user's information.
    """
    # Extract user information - email is available from the auth handler
    user_email = getattr(user, "email", None)
    user_identity = user.identity
    user_display_name = getattr(user, "display_name", user_identity)
    
    return {
        "agent_name": "research",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "has_tavily": bool(os.getenv("TAVILY_API_KEY")),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "user": {
            "identity": user_identity,
            "email": user_email,
            "display_name": user_display_name,
        },
    }


@custom_api_router.get("/user")
async def get_user_info(user: BaseUser = Depends(get_current_user)):
    """Get authenticated user information.
    
    This endpoint demonstrates using LangGraph's built-in authentication middleware
    (enabled via enable_custom_route_auth in langgraph.json). The user is automatically
    authenticated by LangGraph's middleware before this handler is called.
    
    Returns:
        User information including identity, email, and other available attributes.
    """
    # Extract all available user information
    user_identity = user.identity
    user_email = getattr(user, "email", None)
    user_display_name = getattr(user, "display_name", None)
    user_is_authenticated = getattr(user, "is_authenticated", True)
    
    # Get any additional attributes that might be available
    user_info = {
        "identity": user_identity,
        "email": user_email,
        "display_name": user_display_name,
        "is_authenticated": user_is_authenticated,
    }
    
    # Include any other attributes that might be present
    if hasattr(user, "__dict__"):
        for key, value in user.__dict__.items():
            if key not in user_info and not key.startswith("_"):
                user_info[key] = value
    
    return {
        "user": user_info,
        "message": "Successfully authenticated via LangGraph middleware",
        "timestamp": datetime.now().isoformat(),
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

