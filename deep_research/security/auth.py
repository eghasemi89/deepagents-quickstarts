"""Authentication module for LangGraph server.

This module implements OAuth2 authentication using Supabase to control access to the chatbot.
"""

import os
import httpx
from langgraph_sdk import Auth

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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": authorization,
                    "apikey": SUPABASE_SERVICE_KEY,
                },
                timeout=10.0,
            )
            
            if response.status_code != 200:
                raise Auth.exceptions.HTTPException(
                    status_code=401, detail="Invalid or expired token"
                )
            
            user = response.json()
            
            # Return user info if valid
            return {
                "identity": user["id"],  # Unique user identifier (UUID)
                "email": user.get("email"),
                "is_authenticated": True,
            }
    except httpx.HTTPError as e:
        raise Auth.exceptions.HTTPException(
            status_code=503, detail=f"Authentication service unavailable: {str(e)}"
        )
    except Exception as e:
        raise Auth.exceptions.HTTPException(
            status_code=401, detail=f"Authentication failed: {str(e)}"
        )

