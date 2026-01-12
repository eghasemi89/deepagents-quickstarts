#!/usr/bin/env python3
"""Generate LANGGRAPH_AUTH and LANGGRAPH_HTTP from langgraph.json

This script reads langgraph.json and converts relative paths to absolute Docker paths.
This allows you to update langgraph.json without manually updating GitHub secrets.
"""

import json
import sys
from pathlib import Path

def convert_path_to_docker(relative_path: str) -> str:
    """Convert relative path (./file.py:obj) to Docker absolute path (/api/file.py:obj)"""
    if relative_path.startswith("./"):
        # Remove ./ prefix and add /api/ prefix
        docker_path = relative_path.replace("./", "/api/", 1)
    elif relative_path.startswith("../"):
        # Handle parent directory paths (less common)
        docker_path = relative_path.replace("../", "/api/", 1)
    else:
        # Already absolute or relative without ./
        docker_path = relative_path if relative_path.startswith("/") else f"/api/{relative_path}"
    return docker_path

def main():
    # Find langgraph.json (should be in deep_research directory)
    script_dir = Path(__file__).parent
    langgraph_json = script_dir.parent / "langgraph.json"
    
    if not langgraph_json.exists():
        print(f"Error: langgraph.json not found at {langgraph_json}", file=sys.stderr)
        sys.exit(1)
    
    # Read langgraph.json
    try:
        with open(langgraph_json, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in langgraph.json: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading langgraph.json: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract auth and http configs
    auth_config = config.get("auth")
    http_config = config.get("http")
    
    # Generate environment variable values
    env_vars = {}
    
    if auth_config:
        if "path" in auth_config:
            docker_path = convert_path_to_docker(auth_config["path"])
            env_vars["LANGGRAPH_AUTH"] = json.dumps({"path": docker_path})
        else:
            print("Warning: 'auth.path' not found in langgraph.json", file=sys.stderr)
    
    if http_config:
        if "app" in http_config:
            docker_path = convert_path_to_docker(http_config["app"])
            env_vars["LANGGRAPH_HTTP"] = json.dumps({"app": docker_path})
        else:
            print("Warning: 'http.app' not found in langgraph.json", file=sys.stderr)
    
    # Output as shell export statements (for use in GitHub Actions)
    # This allows the workflow to use: eval $(python3 generate_langgraph_env.py)
    for key, value in env_vars.items():
        # Escape the value for shell (JSON strings need proper escaping)
        # The value is already a JSON string, so we need to escape it for shell
        # Escape backslashes, quotes, and dollar signs
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')
        print(f'export {key}="{escaped_value}"')
    
    # Also output in format for .env file (for debugging)
    if "--env-format" in sys.argv:
        print("\n# For .env file:", file=sys.stderr)
        for key, value in env_vars.items():
            print(f"{key}={value}", file=sys.stderr)

if __name__ == "__main__":
    main()

