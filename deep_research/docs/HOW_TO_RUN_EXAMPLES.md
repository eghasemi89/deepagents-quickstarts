# How to Run the Custom Endpoint Examples

This guide shows you how to run and test the different custom endpoint examples.

## Prerequisites

1. Make sure you're in the `deep_research` directory:
   ```bash
   cd deepagents-quickstarts/deep_research
   ```

2. Ensure dependencies are installed:
   ```bash
   uv sync
   ```

3. Set up your environment variables (create a `.env` file or export them):
   ```bash
   export OPENAI_API_KEY=your_key_here
   export TAVILY_API_KEY=your_key_here  # Optional
   ```

## Running an Example

### Step 1: Choose an Example

You have an example file:

- **`webapp_advanced.py`** - Advanced router pattern with multiple route groups

### Step 2: Update `langgraph.json`

Edit `langgraph.json` to point to your chosen example:

```json
{
  "dependencies": ["."],
  "graphs": {
    "research": "./agent.py:agent"
  },
  "env": ".env",
  "http": {
    "app": "./webapp_advanced.py:app"
  }
}
```

**Change the `"app"` path to match your chosen example:**
- `"./webapp_advanced.py:app"` for the advanced example

### Step 3: Start the Server

Run the LangGraph development server:

```bash
langgraph dev --no-browser
```

You should see output like:
```
╦  ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬
║  ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤
╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴  ┴ ┴

- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs
```

The server is now running on `http://127.0.0.1:2024`

## Testing the Endpoints

### Option 1: Using curl (Command Line)

**Test LangGraph default endpoints (these should always work):**
```bash
# List threads
curl http://localhost:2024/threads

# Get API documentation
curl http://localhost:2024/docs
```

**Test your custom endpoints:**

For `webapp_advanced.py`:
```bash
# Simple hello endpoint
curl http://localhost:2024/hello

# Health check
curl http://localhost:2024/api/v1/health

# Stats endpoint
curl http://localhost:2024/api/v1/stats

# Admin status
curl http://localhost:2024/admin/status

# Root endpoint
curl http://localhost:2024/
```

### Option 2: Using Swagger UI (Recommended)

Open your browser and navigate to:
```
http://localhost:2024/docs
```

You'll see:
- **All LangGraph default endpoints** (threads, assistants, streaming, etc.)
- **Your custom endpoints** organized by tags (custom-api, admin, etc.)

You can:
- View all available endpoints
- See request/response schemas
- Test endpoints directly in the browser
- See which endpoints are LangGraph defaults vs your custom ones

### Option 3: Using Python requests

```python
import requests

# Test custom endpoint
response = requests.get("http://localhost:2024/api/v1/health")
print(response.json())

# Test LangGraph default endpoint
response = requests.get("http://localhost:2024/threads")
print(response.json())
```

## Example: Running `webapp_advanced.py`

Here's a complete walkthrough:

1. **Update `langgraph.json`:**
   ```json
   {
     "dependencies": ["."],
     "graphs": {
       "research": "./agent.py:agent"
     },
     "env": ".env",
     "http": {
       "app": "./webapp_advanced.py:app"
     }
   }
   ```

2. **Start the server:**
   ```bash
   langgraph dev --no-browser
   ```

3. **Test endpoints:**
   ```bash
   # Custom endpoints
   curl http://localhost:2024/hello
   curl http://localhost:2024/api/v1/health
   curl http://localhost:2024/api/v1/stats
   curl http://localhost:2024/admin/status
   
   # LangGraph defaults (still work!)
   curl http://localhost:2024/threads
   ```

4. **View in browser:**
   - Open `http://localhost:2024/docs` to see all endpoints
   - You'll see both LangGraph defaults and your custom endpoints

## Switching Between Examples

To try a different example:

1. **Stop the server** (Ctrl+C)

2. **Edit `langgraph.json`** and change the `"app"` path:
   ```json
   "http": {
     "app": "./webapp_advanced.py:app"  // Change this line
   }
   ```

3. **Restart the server:**
   ```bash
   langgraph dev --no-browser
   ```

4. **Test the new endpoints** - they may be different depending on the example

## Troubleshooting

### Error: "Failed to import app module"

- Make sure the file path in `langgraph.json` is correct
- Check that the file exists and has an `app` variable
- Ensure FastAPI is installed: `uv sync`

### Error: "ModuleNotFoundError: No module named 'fastapi'"

Run:
```bash
uv sync
```

This will install FastAPI and all other dependencies.

### Endpoints not showing up in `/docs`

- Make sure the server started without errors
- Check that `langgraph.json` has the correct `"http.app"` configuration
- Restart the server after changing `langgraph.json`

### Custom endpoints work but LangGraph defaults don't

This shouldn't happen - both should work. If it does:
- Check server logs for errors
- Make sure `langgraph.json` has the `"graphs"` configuration
- Verify the agent file exists and is correct

## Quick Reference

| Command | Description |
|---------|-------------|
| `langgraph dev --no-browser` | Start the server |
| `curl http://localhost:2024/hello` | Test custom endpoint |
| `curl http://localhost:2024/threads` | Test LangGraph default |
| `http://localhost:2024/docs` | View all endpoints in browser |

## Next Steps

- Try different examples by changing the `"app"` path in `langgraph.json`
- Add your own custom endpoints to any of the example files
- Explore the Swagger UI at `/docs` to see all available endpoints
- Check the `CREATE_APP_GUIDE.md` for more details on how it all works

