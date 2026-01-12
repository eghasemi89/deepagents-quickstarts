"""Authentication module for LangGraph server.

This module implements OAuth2 authentication using Supabase to control access to the chatbot.
"""

import os
import logging
import asyncio
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
async def get_current_user(
    authorization: str | None,
    method: str | None = None,
) -> Auth.types.MinimalUserDict:
    """Validate JWT tokens from Supabase and extract user information.
    
    Note: OPTIONS requests (CORS preflight) bypass authentication to allow
    browsers to check CORS permissions before making the actual request.
    """
    # Skip authentication for OPTIONS requests (CORS preflight)
    # Browsers send OPTIONS requests without Authorization headers to check CORS
    if method == "OPTIONS":
        logger.debug("🔓 Skipping authentication for OPTIONS preflight request")
        # Return a minimal user dict for OPTIONS requests
        # The actual request will be authenticated separately
        return {
            "identity": "preflight",
            "is_authenticated": False,
        }
    
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
    """Authorize thread creation - sets owner and organization_id in metadata.
    
    This handler is called by LangGraph when a user creates a new thread.
    It sets trusted metadata fields from the authenticated user context.
    
    Args:
        ctx: Authentication context containing user info (ctx.user.identity = user_id)
        value: The thread creation payload
    
    Returns:
        A filter dictionary (though for create, the metadata setting is more important)
    """
    user_id = ctx.user.identity
    logger.info(f"🔒 Thread CREATE authorization for user: {user_id}")
    
    # Set trusted metadata from authenticated context (not from frontend)
    # This ensures security - frontend cannot spoof these values
    metadata = value.setdefault("metadata", {})
    metadata["owner"] = user_id
    
    # Set organization_id from backend (for now, set to "na" as placeholder)
    # TODO: Extract organization_id from user context if available
    # For example: metadata["organization_id"] = ctx.user.organization_id
    metadata["organization_id"] = "na"
    
    logger.debug(f"   → Set metadata['owner'] = {user_id}")
    logger.debug(f"   → Set metadata['organization_id'] = 'na'")
    
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


async def delete_images_from_thread_metadata(thread_id: str, images: list[dict]) -> None:
    """Soft-delete images from database asynchronously.
    
    This function is called as a background task when a thread is deleted.
    It soft-deletes images from the database by setting is_active = false.
    Files in storage are NOT deleted to allow for potential recovery.
    
    Args:
        thread_id: The thread ID (for logging)
        images: List of image objects with doc_id and storage_path
    """
    if not images:
        return
    
    logger.info(f"🗑️  Starting background soft-deletion of {len(images)} images for thread {thread_id}")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Cannot delete images: Supabase configuration missing")
        return
    
    async with httpx.AsyncClient() as client:
        for image in images:
            doc_id = image.get("doc_id")
            
            if not doc_id:
                logger.warning(f"Skipping image without doc_id: {image}")
                continue
            
            try:
                # Check if image exists and is active
                get_response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/uploaded_images",
                    headers={
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Content-Type": "application/json",
                    },
                    params={
                        "doc_id": f"eq.{doc_id}",
                        "select": "doc_id,is_active",
                    },
                    timeout=10.0,
                )
                
                if get_response.status_code == 200:
                    result = get_response.json()
                    if result and len(result) > 0:
                        current_is_active = result[0].get("is_active", True)
                        if current_is_active:
                            # Soft delete: set is_active = false
                            logger.debug(f"Updating image {doc_id} is_active from {current_is_active} to False")
                            update_response = await client.patch(
                                f"{SUPABASE_URL}/rest/v1/uploaded_images",
                                headers={
                                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                                    "apikey": SUPABASE_SERVICE_KEY,
                                    "Content-Type": "application/json",
                                    "Prefer": "return=representation",
                                },
                                params={"doc_id": f"eq.{doc_id}"},
                                json={"is_active": False},
                                timeout=10.0,
                            )
                            
                            if update_response.status_code not in [200, 204]:
                                error_text = await update_response.text() if hasattr(update_response, 'text') else "Unknown error"
                                logger.error(
                                    f"Failed to soft-delete image {doc_id} from database: "
                                    f"{update_response.status_code} - {error_text}"
                                )
                            else:
                                logger.info(f"✅ Soft-deleted image {doc_id} from database (is_active = false)")
                        else:
                            logger.debug(f"Image {doc_id} already soft-deleted (is_active = {current_is_active})")
                    else:
                        logger.warning(f"Image {doc_id} not found in database")
                else:
                    logger.warning(
                        f"Failed to check image {doc_id} status: "
                        f"{get_response.status_code} - {get_response.text}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Error soft-deleting image {doc_id}: {str(e)}",
                    exc_info=True
                )
                # Continue with other images even if one fails
    
    logger.info(f"✅ Completed background soft-deletion of images for thread {thread_id}")


async def fetch_thread_metadata_for_deletion(thread_id: str) -> dict | None:
    """Fetch thread metadata before deletion to extract image references.
    
    This function attempts to get the thread metadata using the LangGraph runtime database.
    If that fails, it returns None and image deletion will be skipped.
    
    Args:
        thread_id: The thread ID to fetch
        
    Returns:
        Thread metadata dict if found, None otherwise
    """
    try:
        from langgraph_runtime.database import connect
        from langgraph_runtime.ops import Threads
        from langgraph_api.serde import json_loads, Fragment
        
        logger.info(f"   → Attempting to fetch thread {thread_id} from database...")
        async with connect() as conn:
            thread_iter = await Threads.get(conn, thread_id)
            # Fetch the first (and only) result
            thread_count = 0
            async for thread in thread_iter:
                thread_count += 1
                metadata_raw = thread.get("metadata", {})
                
                # Handle Fragment objects - they need to be parsed from bytes
                if isinstance(metadata_raw, Fragment):
                    metadata = json_loads(metadata_raw)
                    logger.info(f"   → Successfully fetched thread {thread_id}, parsed Fragment to dict with keys: {list(metadata.keys()) if isinstance(metadata, dict) else 'not a dict'}")
                elif isinstance(metadata_raw, dict):
                    metadata = metadata_raw
                    logger.info(f"   → Successfully fetched thread {thread_id}, metadata keys: {list(metadata.keys())}")
                else:
                    # Try to parse as bytes/string if it's not already a dict
                    try:
                        metadata = json_loads(metadata_raw)
                        logger.info(f"   → Successfully parsed metadata from raw format")
                    except Exception:
                        logger.warning(f"   → Metadata is in unexpected format: {type(metadata_raw)}")
                        metadata = {}
                
                return metadata if isinstance(metadata, dict) else {}
            
            if thread_count == 0:
                logger.warning(f"   → Thread {thread_id} not found in database")
            return None
    except Exception as e:
        logger.error(f"   → Could not fetch thread metadata for {thread_id}: {str(e)}", exc_info=True)
        return None


@auth.on.threads.delete
async def on_threads_delete(
    ctx: Auth.types.AuthContext,
    value: dict,
) -> dict:
    """Authorize thread deletion - ensures users can only delete their own threads.
    
    This handler is called by LangGraph when a user tries to delete a thread.
    LangGraph uses the returned filter to check if the thread's metadata.owner matches.
    
    Additionally, this handler creates a background task to delete associated images
    from the database and storage when the thread is deleted.
    
    Args:
        ctx: Authentication context containing user info
        value: The delete request payload (contains thread_id)
    
    Returns:
        A filter dictionary: {"owner": user_id}
        LangGraph internally checks: thread.metadata["owner"] == user_id
        If no match, the request is denied (403) or returns 404
    """
    user_id = ctx.user.identity
    thread_id = value.get("thread_id", "unknown")
    logger.info(f"🔒 Thread DELETE authorization for user: {user_id}, thread: {thread_id}")
    
    # Fetch thread metadata BEFORE deletion to get image references
    # We need to do this synchronously while the thread still exists
    logger.info(f"   → Fetching thread metadata for {thread_id} before deletion...")
    metadata = await fetch_thread_metadata_for_deletion(thread_id)
    
    images = []
    if metadata and isinstance(metadata, dict):
        logger.info(f"   → Thread metadata retrieved: {list(metadata.keys())}")
        images = metadata.get("images", [])
        if not isinstance(images, list):
            images = []
        logger.info(f"   → Found {len(images)} images in thread metadata")
    else:
        logger.warning(f"   → Could not retrieve thread metadata for {thread_id} (metadata: {metadata})")
    
    # Create background task to delete images after thread deletion
    if images and len(images) > 0:
        logger.info(f"   → Scheduling deletion of {len(images)} images for thread {thread_id}")
        async def delete_images_task():
            try:
                logger.info(f"   → Background task started: waiting 0.5s before deleting images...")
                # Small delay to let thread deletion complete
                await asyncio.sleep(0.5)
                logger.info(f"   → Starting image deletion for thread {thread_id}...")
                await delete_images_from_thread_metadata(thread_id, images)
            except Exception as e:
                logger.error(
                    f"Error in background image deletion task for thread {thread_id}: {str(e)}",
                    exc_info=True
                )
        
        # Create background task (fire and forget)
        asyncio.create_task(delete_images_task())
        logger.info(f"   → Background task created for deleting {len(images)} images")
    else:
        logger.info(f"   → No images found in thread {thread_id} metadata, skipping image deletion")
    
    # Return filter - LangGraph will check if thread.metadata["owner"] == user_id
    # This happens INSIDE LangGraph's code, not in our handler
    filter_dict = {"owner": user_id}
    logger.debug(f"   → Returning filter: {filter_dict}")
    logger.debug(f"   → LangGraph will check: thread.metadata['owner'] == '{user_id}'")
    return filter_dict


@auth.on.threads.update
async def on_threads_update(
    ctx: Auth.types.AuthContext,
    value: dict,
) -> dict:
    """Authorize thread update (PATCH) - ensures users can only update their own threads.
    
    This handler is called by LangGraph when a user tries to update/patch a thread.
    LangGraph uses the returned filter to check if the thread's metadata.owner matches.
    
    Args:
        ctx: Authentication context containing user info
        value: The update request payload (contains thread_id and metadata)
    
    Returns:
        A filter dictionary: {"owner": user_id}
        LangGraph internally checks: thread.metadata["owner"] == user_id
        If no match, the request is denied (403) or returns 404
    """
    user_id = ctx.user.identity
    thread_id = value.get("thread_id", "unknown")
    logger.info(f"🔒 Thread UPDATE authorization for user: {user_id}, thread: {thread_id}")
    
    # Ensure users can only modify their own threads
    # Don't override metadata.owner if it's already set (it should match user_id)
    metadata = value.setdefault("metadata", {})
    
    # Return filter - LangGraph will check if thread.metadata["owner"] == user_id
    # This happens INSIDE LangGraph's code, not in our handler
    filter_dict = {"owner": user_id}
    logger.debug(f"   → Returning filter: {filter_dict}")
    logger.debug(f"   → LangGraph will check: thread.metadata['owner'] == '{user_id}'")
    return filter_dict


@auth.on.threads
async def on_threads(
    ctx: Auth.types.AuthContext,
    value: dict,
) -> dict:
    """Fallback handler for other thread operations.
    
    This is a catch-all for thread operations that don't have specific handlers.
    The more specific handlers (create, read, search, delete, update) take precedence.
    
    Args:
        ctx: Authentication context containing user info
        value: The request payload
    
    Returns:
        A filter dictionary that restricts access to resources owned by the user
    """
    user_id = ctx.user.identity
    logger.debug(f"🔒 Thread operation (fallback) for user: {user_id} on path: {ctx.path}")
    
    # For other operations, ensure users can only access their own threads
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

