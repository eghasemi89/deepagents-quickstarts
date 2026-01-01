"""Example: Using Multiple Graphs in LangGraph

This script demonstrates how to call different graphs from your application.
In production, you would typically call these via the LangGraph API from your frontend,
but this shows how to use them programmatically in Python.

Usage:
    # With authentication (recommended):
    export AUTH_TOKEN="your-supabase-jwt-token"
    python example_multiple_graphs.py

    # Or pass token as argument:
    python example_multiple_graphs.py --token "your-supabase-jwt-token"

    # Or set in .env file:
    # AUTH_TOKEN=your-supabase-jwt-token

Note: If you encounter authentication issues with this script (401 errors),
      try example_multiple_graphs_simple.py instead, which uses httpx directly
      and has more reliable authentication support.

See get_auth_token.md for instructions on how to get your authentication token.
"""

import asyncio
import os
import sys
import argparse
from dotenv import load_dotenv
from langgraph_sdk import get_client

# Load environment variables from .env file if it exists
load_dotenv()


def get_auth_token() -> str | None:
    """Get authentication token from environment variable or command line."""
    # Check command line arguments first
    parser = argparse.ArgumentParser(description="Test multiple graphs with authentication")
    parser.add_argument(
        "--token",
        type=str,
        help="Supabase JWT token for authentication (or set AUTH_TOKEN env var)",
        default=None
    )
    parser.add_argument(
        "--url",
        type=str,
        help="LangGraph server URL",
        default=os.getenv("LANGGRAPH_URL", "http://localhost:8123")
    )
    args = parser.parse_args()
    
    # Priority: command line arg > environment variable
    token = args.token or os.getenv("AUTH_TOKEN")
    return token, args.url


async def example_multiple_graphs(auth_token: str | None = None, api_url: str = "http://localhost:8123"):
    """Example of calling multiple graphs from the same application.
    
    Args:
        auth_token: Optional Supabase JWT token for authentication
        api_url: LangGraph server URL
    """
    
    # Initialize the client
    # Note: The Python SDK may not directly support headers in get_client()
    # If authentication fails, try using example_multiple_graphs_simple.py instead
    # which uses httpx directly and definitely supports headers
    
    client = get_client(api_url=api_url)
    
    if auth_token:
        print("✅ Authentication token provided")
        print("⚠️  Note: The Python SDK may require patching to support headers.")
        print("   If you get 401 errors, try example_multiple_graphs_simple.py instead")
        print("   which uses httpx directly and supports authentication.")
        print()
        
        # Try to patch the client (this may or may not work depending on SDK version)
        try:
            # Store token for potential use
            client._auth_token = auth_token
            # Try to find and update headers in the underlying HTTP client
            if hasattr(client, '_client'):
                if hasattr(client._client, 'headers'):
                    client._client.headers.update({"Authorization": f"Bearer {auth_token}"})
        except Exception as e:
            print(f"   Warning: Could not patch client headers: {e}")
            print("   Consider using example_multiple_graphs_simple.py for reliable auth")
    else:
        print("⚠️  No authentication token provided - requests may fail if backend requires auth")
        print("   Set AUTH_TOKEN environment variable or use --token argument")
        print("   See get_auth_token.md for instructions on getting a token")
    
    print("=" * 80)
    print("Example: Multiple Graphs")
    print("=" * 80)
    print()
    
    # Example 1: Call the research agent
    print("1. Calling 'research' agent (deep research with web search)...")
    print("-" * 80)
    
    research_result = await client.runs.create(
        assistant_id="research",  # Graph ID from langgraph.json
        input={
            "messages": [{
                "role": "user",
                "content": "What is LangGraph? Give me a brief overview."
            }]
        }
    )
    
    print(f"Research agent response: {research_result.get('output', {}).get('messages', [])[-1].get('content', 'No response')[:200]}...")
    print()
    
    # Example 2: Call the chat agent
    print("2. Calling 'chat' agent (simple conversation)...")
    print("-" * 80)
    
    chat_result = await client.runs.create(
        assistant_id="chat",  # Different graph ID
        input={
            "messages": [{
                "role": "user",
                "content": "Hello! Can you explain what AI agents are in simple terms?"
            }]
        }
    )
    
    print(f"Chat agent response: {chat_result.get('output', {}).get('messages', [])[-1].get('content', 'No response')[:200]}...")
    print()
    
    # Example 3: Stream from research agent
    print("3. Streaming from 'research' agent...")
    print("-" * 80)
    
    async for event in client.runs.stream(
        assistant_id="research",
        input={
            "messages": [{
                "role": "user",
                "content": "Tell me about LangChain middleware"
            }]
        }
    ):
        if "messages" in event:
            last_message = event["messages"][-1]
            if hasattr(last_message, "content"):
                print(last_message.content[:100], end="", flush=True)
    
    print("\n")
    
    # Example 4: List available assistants (graphs)
    print("4. Available graphs/assistants:")
    print("-" * 80)
    
    assistants = await client.assistants.list()
    for assistant in assistants:
        print(f"  - {assistant.get('assistant_id')}: {assistant.get('name', 'No name')}")
    
    print()
    print("=" * 80)
    print("Done!")
    print("=" * 80)


async def example_thread_management(auth_token: str | None = None, api_url: str = "http://localhost:8123"):
    """Example of managing threads for different graphs.
    
    Args:
        auth_token: Optional Supabase JWT token for authentication
        api_url: LangGraph server URL
    """
    
    # Initialize client with authentication (same approach as above)
    if auth_token:
        try:
            client = get_client(
                api_url=api_url,
                default_headers={"Authorization": f"Bearer {auth_token}"}
            )
        except TypeError:
            client = get_client(api_url=api_url)
            if hasattr(client, '_client') and hasattr(client._client, 'headers'):
                client._client.headers.update({"Authorization": f"Bearer {auth_token}"})
            elif hasattr(client, 'headers'):
                client.headers.update({"Authorization": f"Bearer {auth_token}"})
    else:
        client = get_client(api_url=api_url)
    
    print("\n" + "=" * 80)
    print("Example: Thread Management Across Multiple Graphs")
    print("=" * 80)
    print()
    
    # Create a thread for research agent
    research_thread = await client.threads.create(
        assistant_id="research"
    )
    print(f"Created research thread: {research_thread['thread_id']}")
    
    # Create a thread for chat agent
    chat_thread = await client.threads.create(
        assistant_id="chat"
    )
    print(f"Created chat thread: {chat_thread['thread_id']}")
    
    # Send messages to different threads
    await client.runs.create(
        assistant_id="research",
        thread_id=research_thread['thread_id'],
        input={
            "messages": [{"role": "user", "content": "Research Python async programming"}]
        }
    )
    
    await client.runs.create(
        assistant_id="chat",
        thread_id=chat_thread['thread_id'],
        input={
            "messages": [{"role": "user", "content": "What is async programming?"}]
        }
    )
    
    print("\nEach graph maintains its own thread state independently!")


if __name__ == "__main__":
    # Get authentication token and API URL
    auth_token, api_url = get_auth_token()
    
    if not auth_token:
        print("\n" + "=" * 80)
        print("⚠️  WARNING: No authentication token provided!")
        print("=" * 80)
        print("Your backend requires authentication. To get a token:")
        print("1. Log in through your frontend application")
        print("2. Open browser DevTools > Application > Local Storage")
        print("3. Find 'deep-agent-config' and copy the 'authToken' value")
        print("4. Run: export AUTH_TOKEN='your-token-here'")
        print("   Or: python example_multiple_graphs.py --token 'your-token-here'")
        print("=" * 80)
        response = input("\nContinue without authentication? (y/N): ")
        if response.lower() != 'y':
            print("Exiting. Please provide a token and try again.")
            sys.exit(1)
        print()
    
    # Run the examples
    try:
        asyncio.run(example_multiple_graphs(auth_token, api_url))
        # Uncomment to run thread management example:
        # asyncio.run(example_thread_management(auth_token, api_url))
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e):
            print("\n" + "=" * 80)
            print("❌ Authentication failed!")
            print("=" * 80)
            print("Please provide a valid authentication token:")
            print("  export AUTH_TOKEN='your-supabase-jwt-token'")
            print("  python example_multiple_graphs.py")
            print("=" * 80)
        else:
            print(f"\n❌ Error: {e}")
            raise

