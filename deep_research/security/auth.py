"""Authentication module for LangGraph server.

This module implements OAuth2 authentication using Supabase to control access to the chatbot.
"""

import os
import logging
import httpx
from langgraph_sdk import Auth

# Set up logger
logger = logging.getLogger(__name__)

# The "Auth" object is a container that LangGraph will use to mark our authentication function
auth = Auth()

# Load Supabase configuration from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables. "
        "See SUPABASE_SETUP.md for instructions."
    )


# The `authenticate` decorator tells LangGraph to call this function as middleware
# for every request. This will determine whether the request is allowed or not
@auth.authenticate
async def get_current_user(authorization: str | None) -> Auth.types.MinimalUserDict:
    """Validate JWT tokens from Supabase and extract user information."""
    logger.info("🔐 Authentication function invoked - get_current_user called")
    logger.debug(f"Authorization header present: {authorization is not None}")
    
    if not authorization:
               raise Auth.exceptions.HTTPException(
            status_code=401, detail="Authorization header is required"
        )
    
    # Parse the Authorization header
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise Auth.exceptions.HTTPException(
                status_code=401, detail="Authorization scheme must be 'Bearer'"
            )
    except ValueError:
        raise Auth.exceptions.HTTPException(
            status_code=401, detail="Invalid Authorization header format"
        )

    try:
        # Verify token with Supabase auth provider
        logger.info("🔍 Verifying token with Supabase...")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": authorization,
                    "apikey": SUPABASE_SERVICE_KEY,
                },
                timeout=10.0,
            )
            
            logger.debug(f"Supabase response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"❌ Authentication failed: Invalid or expired token (status: {response.status_code})")
                raise Auth.exceptions.HTTPException(
                    status_code=401, detail="Invalid or expired token"
                )
            
            user = response.json()
            logger.info(f"✅ Authentication successful for user: {user.get('email', 'unknown')} (ID: {user.get('id', 'unknown')})")
            
            # Return user info if valid
            return {
                "identity": user["id"],  # Unique user identifier (UUID)
                "email": user.get("email"),
                "is_authenticated": True,
            }
    except httpx.HTTPError as e:
        logger.error(f"❌ HTTP error during authentication: {str(e)}")
        raise Auth.exceptions.HTTPException(
            status_code=503, detail=f"Authentication service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Authentication exception: {str(e)}", exc_info=True)
        raise Auth.exceptions.HTTPException(
            status_code=401, detail=f"Authentication failed: {str(e)}"
        )


# ============================================================================
# Authorization Handlers
# ============================================================================
# These handlers control access to resources (threads, runs, etc.) after
# authentication. They ensure users can only access their own resources.
#
# HOW IT WORKS:
# 1. LangGraph's internal middleware calls these handlers BEFORE processing requests
# 2. For CREATE operations: We set metadata["owner"] = user_id (saved with the resource)
# 3. For READ/SEARCH operations: We return a filter dict {"owner": user_id}
# 4. LangGraph applies the filter internally when querying the database/checkpointer
# 5. Only threads matching the filter are returned to the user


@auth.on.threads.create
async def on_threads_create(
    ctx: Auth.types.AuthContext,
    value: dict,
) -> dict:
    """Authorize thread creation - sets owner in metadata.
    
    This handler is called by LangGraph when a user creates a new thread.
    It sets the owner field in the thread's metadata so we can filter by it later.
    
    Args:
        ctx: Authentication context containing user info (ctx.user.identity = user_id)
        value: The thread creation payload
    
    Returns:
        A filter dictionary (though for create, the metadata setting is more important)
    """
    user_id = ctx.user.identity
    logger.info(f"🔒 Thread CREATE authorization for user: {user_id}")
    
    # Set owner in metadata - this gets saved with the thread in the database
    # This is the key: we're storing the owner so we can filter by it later
    metadata = value.setdefault("metadata", {})
    metadata["owner"] = user_id
    logger.debug(f"   → Set metadata['owner'] = {user_id}")
    
    # Return filter (though for create, the metadata is what matters)
    return {"owner": user_id}


@auth.on.threads.read
async def on_threads_read(
    ctx: Auth.types.AuthContext,
    value: dict,
) -> dict:
    """Authorize thread read - filters by owner.
    
    This handler is called by LangGraph when a user tries to read a specific thread.
    LangGraph uses the returned filter to check if the thread's metadata.owner matches.
    
    Args:
        ctx: Authentication context containing user info
        value: The thread being accessed (contains thread_id)
    
    Returns:
        A filter dictionary: {"owner": user_id}
        LangGraph internally checks: thread.metadata["owner"] == user_id
        If no match, the request is denied (403) or returns 404
    """
    user_id = ctx.user.identity
    thread_id = value.get("thread_id", "unknown")
    logger.info(f"🔒 Thread READ authorization for user: {user_id}, thread: {thread_id}")
    
    # Return filter - LangGraph will check if thread.metadata["owner"] == user_id
    # This happens INSIDE LangGraph's code, not in our handler
    filter_dict = {"owner": user_id}
    logger.debug(f"   → Returning filter: {filter_dict}")
    logger.debug(f"   → LangGraph will check: thread.metadata['owner'] == '{user_id}'")
    return filter_dict


@auth.on.threads.search
async def on_threads_search(
    ctx: Auth.types.AuthContext,
    value: dict,
) -> dict:
    """Authorize thread search - filters results by owner.
    
    This handler is called by LangGraph when a user searches/list threads.
    LangGraph applies the returned filter to the database query, so only threads
    with matching owner metadata are returned.
    
    Args:
        ctx: Authentication context containing user info
        value: The search parameters (limit, offset, metadata filters, etc.)
    
    Returns:
        A filter dictionary: {"owner": user_id}
        LangGraph internally modifies the query to: WHERE metadata->>'owner' = user_id
        (or equivalent for the storage backend)
    """
    user_id = ctx.user.identity
    logger.info(f"🔒 Thread SEARCH authorization for user: {user_id}")
    logger.debug(f"   → Search params: limit={value.get('limit')}, offset={value.get('offset')}")
    
    # Return filter - LangGraph will add this to the WHERE clause of the search query
    # This happens INSIDE LangGraph's database query logic
    filter_dict = {"owner": user_id}
    logger.debug(f"   → Returning filter: {filter_dict}")
    logger.debug(f"   → LangGraph will query: SELECT * FROM threads WHERE metadata->>'owner' = '{user_id}'")
    return filter_dict


@auth.on.threads
async def on_threads(
    ctx: Auth.types.AuthContext,
    value: dict,
) -> dict:
    """Fallback handler for other thread operations (update, delete).
    
    This is a catch-all for thread operations that don't have specific handlers.
    The more specific handlers (create, read, search) take precedence.
    
    Args:
        ctx: Authentication context containing user info
        value: The request payload
    
    Returns:
        A filter dictionary that restricts access to resources owned by the user
    """
    user_id = ctx.user.identity
    logger.debug(f"🔒 Thread operation (fallback) for user: {user_id} on path: {ctx.path}")
    
    # For update/delete, we want to ensure users can only modify their own threads
    metadata = value.setdefault("metadata", {})
    if "owner" not in metadata:
        metadata["owner"] = user_id
    
    return {"owner": user_id}


@auth.on.threads.create_run
async def on_threads_create_run(
    ctx: Auth.types.AuthContext,
    value: dict,
) -> dict:
    """Authorize run creation on threads.
    
    Ensures that runs can only be created on threads owned by the user.
    Runs inherit the thread's access control.
    
    Args:
        ctx: Authentication context containing user info
        value: The request payload for creating a run
    
    Returns:
        A filter dictionary that restricts access to threads owned by the user
    """
    user_id = ctx.user.identity
    logger.debug(f"🔒 Run creation authorization for user: {user_id}")
    
    # Get or create the metadata dictionary in the payload
    metadata = value.setdefault("metadata", {})
    
    # Add owner to run metadata
    metadata["owner"] = user_id
    
    # Return filters to ensure runs are only created on user's threads
    # This inherits the thread's access control
    return {"owner": user_id}

