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

from fastapi import FastAPI, APIRouter, Depends, Request, HTTPException, UploadFile, File, Form, Body
from typing import Dict, Any, Optional
from starlette.authentication import BaseUser
import os
from datetime import datetime
import httpx
import uuid
import logging

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


@custom_api_router.post("/upload-image")
async def upload_image_create(
    request: Request,
    file: UploadFile = File(...),
    user: BaseUser = Depends(get_current_user),
):
    """Upload an image file for agent analysis.
    
    This endpoint:
    1. Authenticates the user
    2. Validates the file (image type, size)
    3. Uploads to Supabase Storage
    4. Saves metadata to uploaded_images table (including user_id in metadata field)
    5. Returns the image URL for use in messages
    
    Args:
        request: FastAPI request object
        file: The image file to upload
        user: Authenticated user (from dependency)
    
    Returns:
        Dict with doc_id, storage_url, and metadata
    
    Raises:
        HTTPException: 400 for invalid file, 401 for auth failure, 500 for server errors
    """
    logger = logging.getLogger(__name__)
    user_id = user.identity
    
    # Get Supabase configuration
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
    POSTGRES_URI = os.environ.get("POSTGRES_URI_CUSTOM") or os.environ.get("POSTGRES_URI")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase configuration missing")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: Supabase credentials not set"
        )
    
    if not POSTGRES_URI:
        logger.error("PostgreSQL connection string missing")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: Database connection not configured"
        )
    
    # Validate file type
    allowed_mime_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_mime_types)}"
        )
    
    # Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )
    
    try:
        # Generate storage path: user-uploads/{timestamp}-{filename}
        timestamp = int(datetime.now().timestamp() * 1000)  # milliseconds
        # Sanitize filename (remove path separators and special chars)
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")[:100]
        if not safe_filename:
            safe_filename = "image"
        # Add extension if missing
        if "." not in safe_filename:
            ext_map = {
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "image/webp": ".webp",
            }
            safe_filename += ext_map.get(file.content_type, ".jpg")
        
        storage_path = f"{timestamp}-{safe_filename}"
        
        # Upload to Supabase Storage using REST API
        # Note: httpx will handle URL encoding automatically
        storage_url = f"{SUPABASE_URL}/storage/v1/object/user-uploads/{storage_path}"
        
        async with httpx.AsyncClient() as client:
            # Upload file to storage
            # Supabase Storage requires both Authorization and apikey headers
            upload_response = await client.post(
                storage_url,
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Content-Type": file.content_type,
                    "x-upsert": "true",  # Allow overwriting
                },
                content=file_content,
                timeout=30.0,
            )
            
            if upload_response.status_code not in [200, 201]:
                logger.error(f"Storage upload failed: {upload_response.status_code} - {upload_response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file to storage: {upload_response.text}"
                )
            
            # Get public URL (or create signed URL)
            # For private buckets, we need to generate a signed URL
            # httpx will handle URL encoding automatically
            public_url_response = await client.post(
                f"{SUPABASE_URL}/storage/v1/object/sign/user-uploads/{storage_path}",
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Content-Type": "application/json",
                },
                json={"expiresIn": 31536000},  # 1 year expiration
                timeout=10.0,
            )
            
            if public_url_response.status_code == 200:
                signed_data = public_url_response.json()
                signed_path = signed_data.get('signedURL', '')
                
                # Construct full signed URL
                # Supabase sign endpoint returns signedURL in different formats:
                # - Full URL: "https://...supabase.co/storage/v1/object/sign/..."
                # - Path with /storage/v1: "/storage/v1/object/sign/..."
                # - Path without /storage/v1: "/object/sign/..." (needs fixing)
                if signed_path.startswith('http'):
                    # Already a full URL
                    signed_url = signed_path
                elif signed_path.startswith('/storage/v1'):
                    # Full path starting with /storage/v1, prepend SUPABASE_URL
                    signed_url = f"{SUPABASE_URL}{signed_path}"
                elif signed_path.startswith('/object/sign/'):
                    # Path starting with /object/sign/ but missing /storage/v1
                    # Fix by adding /storage/v1 prefix
                    signed_url = f"{SUPABASE_URL}/storage/v1{signed_path}"
                elif signed_path.startswith('/'):
                    # Other path starting with /, add /storage/v1
                    signed_url = f"{SUPABASE_URL}/storage/v1{signed_path}"
                else:
                    # Just a token or relative path, construct full URL
                    # The signed URL format should be: /storage/v1/object/sign/bucket/path?token=...
                    signed_url = f"{SUPABASE_URL}/storage/v1/object/sign/user-uploads/{storage_path}?token={signed_path}"
            else:
                # Fallback: try to use public URL if bucket is public
                # Otherwise, construct a signed URL manually
                logger.warning(f"Failed to generate signed URL: {public_url_response.status_code} - {public_url_response.text}")
                # Use the storage URL directly (will require auth, but better than nothing)
                signed_url = f"{SUPABASE_URL}/storage/v1/object/public/user-uploads/{storage_path}"
        
        # Save metadata to database using Supabase REST API
        doc_id = str(uuid.uuid4())
        uploaded_at = datetime.now()
        
        try:
            async with httpx.AsyncClient() as db_client:
                # Insert metadata using Supabase REST API
                db_response = await db_client.post(
                    f"{SUPABASE_URL}/rest/v1/uploaded_images",
                    headers={
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",  # Return inserted row
                    },
                    json={
                        "doc_id": doc_id,
                        "storage_path": storage_path,
                        "storage_url": signed_url,
                        "file_name": file.filename,
                        "file_size": file_size,
                        "mime_type": file.content_type,
                        "metadata": {
                            "user_id": user_id,
                        },
                    },
                    timeout=10.0,
                )
                
                if db_response.status_code not in [200, 201]:
                    logger.error(f"Database insert failed: {db_response.status_code} - {db_response.text}")
                    # Try to clean up uploaded file if database insert fails
                    try:
                        async with httpx.AsyncClient() as cleanup_client:
                            await cleanup_client.delete(
                                storage_url,
                                headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
                                timeout=10.0,
                            )
                    except Exception:
                        pass  # Ignore cleanup errors
                    
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to save image metadata: {db_response.text}"
                    )
                
                # Extract uploaded_at from response if available
                result = db_response.json()
                if isinstance(result, list) and len(result) > 0:
                    uploaded_at_str = result[0].get("uploaded_at")
                    if uploaded_at_str:
                        uploaded_at = datetime.fromisoformat(uploaded_at_str.replace("Z", "+00:00"))
                
                logger.info(f"Image uploaded successfully: {doc_id}")
                
                return {
                    "doc_id": doc_id,
                    "storage_url": signed_url,
                    "storage_path": storage_path,
                    "file_name": file.filename,
                    "file_size": file_size,
                    "mime_type": file.content_type,
                    "uploaded_at": uploaded_at.isoformat(),
                }
            
        except HTTPException:
            raise
        except Exception as db_error:
            logger.error(f"Database insert failed: {str(db_error)}", exc_info=True)
            # Try to clean up uploaded file if database insert fails
            try:
                async with httpx.AsyncClient() as cleanup_client:
                    await cleanup_client.delete(
                        storage_url,
                        headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
                        timeout=10.0,
                    )
            except Exception:
                pass  # Ignore cleanup errors
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save image metadata: {str(db_error)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image upload failed: {str(e)}"
        )


@custom_api_router.get("/upload-image/{doc_id}")
async def upload_image_read(
    request: Request,
    doc_id: str,
    user: BaseUser = Depends(get_current_user),
):
    """Read/retrieve image metadata by doc_id.
    
    This endpoint follows the same pattern as AssistantsRead:
    - doc_id: Path parameter (UUID) - unique identifier for the image
    
    This endpoint:
    1. Authenticates the user
    2. Retrieves image metadata from uploaded_images table
    3. Returns the image information
    
    Args:
        request: FastAPI request object
        doc_id: The document ID (UUID) of the image to retrieve
        user: Authenticated user (from dependency)
    
    Returns:
        Dict with doc_id, storage_url, and metadata
    
    Raises:
        HTTPException: 404 if image not found, 401 for auth failure, 500 for server errors
    
    Examples:
        read_params = {
            "doc_id": "123e4567-e89b-12d3-a456-426614174000",
            "metadata": {}  # Optional, for future filtering
        }
    """
    logger = logging.getLogger(__name__)
    
    # Get Supabase configuration
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase configuration missing")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: Supabase credentials not set"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # Build query params
            query_params = {
                "doc_id": f"eq.{doc_id}",
                "select": "doc_id,storage_path,storage_url,file_name,file_size,mime_type,uploaded_at,is_active,metadata",
            }
            
            # Retrieve image metadata from database
            db_response = await client.get(
                f"{SUPABASE_URL}/rest/v1/uploaded_images",
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Content-Type": "application/json",
                },
                params=query_params,
                timeout=10.0,
            )
            
            if db_response.status_code != 200:
                logger.error(f"Database query failed: {db_response.status_code} - {db_response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to query image metadata: {db_response.text}"
                )
            
            result = db_response.json()
            
            if not result or len(result) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Image with doc_id {doc_id} not found"
                )
            
            image_data = result[0]
            
            # Check if image is active
            if not image_data.get("is_active", True):
                raise HTTPException(
                    status_code=404,
                    detail=f"Image with doc_id {doc_id} has been deleted"
                )
            
            logger.info(f"Image retrieved successfully: {doc_id}")
            
            return {
                "doc_id": image_data["doc_id"],
                "storage_url": image_data["storage_url"],
                "storage_path": image_data["storage_path"],
                "file_name": image_data["file_name"],
                "file_size": image_data["file_size"],
                "mime_type": image_data["mime_type"],
                "uploaded_at": image_data["uploaded_at"],
                "is_active": image_data.get("is_active", True),
                "metadata": image_data.get("metadata", {}),
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image retrieval failed: {str(e)}"
        )


@custom_api_router.delete("/upload-image/{doc_id}")
async def upload_image_delete(
    request: Request,
    doc_id: str,
    user: BaseUser = Depends(get_current_user),
):
    """Delete an image by doc_id.
    
    This endpoint follows the same pattern as assistant/thread delete:
    - doc_id: Path parameter (UUID) - unique identifier for the image
    
    This endpoint:
    1. Authenticates the user
    2. Soft deletes the image by setting is_active = false
    3. Optionally deletes the file from storage
    
    Args:
        request: FastAPI request object
        doc_id: The document ID (UUID) of the image to delete
        user: Authenticated user (from dependency)
    
    Returns:
        Success message
    
    Raises:
        HTTPException: 404 if image not found, 401 for auth failure, 500 for server errors
    """
    logger = logging.getLogger(__name__)
    
    # Get Supabase configuration
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase configuration missing")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: Supabase credentials not set"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # First, check if image exists
            get_response = await client.get(
                f"{SUPABASE_URL}/rest/v1/uploaded_images",
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Content-Type": "application/json",
                },
                params={
                    "doc_id": f"eq.{doc_id}",
                    "select": "doc_id,storage_path,is_active",
                },
                timeout=10.0,
            )
            
            if get_response.status_code != 200:
                logger.error(f"Database query failed: {get_response.status_code} - {get_response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to query image: {get_response.text}"
                )
            
            result = get_response.json()
            
            if not result or len(result) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Image with doc_id {doc_id} not found"
                )
            
            image_data = result[0]
            
            # Check if already deleted
            if not image_data.get("is_active", True):
                raise HTTPException(
                    status_code=404,
                    detail=f"Image with doc_id {doc_id} has already been deleted"
                )
            
            # Soft delete: set is_active = false
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
                logger.error(f"Delete failed: {update_response.status_code} - {update_response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete image: {update_response.text}"
                )
            
            # Optionally delete the file from storage
            storage_path = image_data.get("storage_path")
            if storage_path:
                try:
                    storage_url = f"{SUPABASE_URL}/storage/v1/object/user-uploads/{storage_path}"
                    delete_response = await client.delete(
                        storage_url,
                        headers={
                            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                            "apikey": SUPABASE_SERVICE_KEY,
                        },
                        timeout=10.0,
                    )
                    if delete_response.status_code not in [200, 204]:
                        logger.warning(f"Failed to delete file from storage: {delete_response.status_code}")
                        # Don't fail the request if storage deletion fails
                except Exception as storage_error:
                    logger.warning(f"Error deleting file from storage: {str(storage_error)}")
                    # Don't fail the request if storage deletion fails
            
            logger.info(f"Image deleted successfully: {doc_id}")
            
            return {
                "message": "Image deleted successfully",
                "doc_id": doc_id,
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image deletion failed: {str(e)}"
        )



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

