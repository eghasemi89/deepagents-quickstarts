"""Interactive Login and Test Script

This script opens a browser for you to log in, then automatically uses the token
to test your multiple graphs. No manual token copying needed!

Usage:
    python login_and_test.py

The script will:
1. Open a browser window for you to log in
2. Automatically capture your authentication token
3. Run the example_multiple_graphs script with your token
"""

import asyncio
import os
import sys
import webbrowser
import http.server
import socketserver
import urllib.parse
import json
import socket
from threading import Thread
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:8123")

# Find an available port
def find_free_port(start_port=8765, max_attempts=10):
    """Find an available port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port starting from {start_port}")

# Initialize port - will be set in main() after finding free port
CALLBACK_PORT = None
CALLBACK_URL = None

# Global variable to store the token
captured_token = None
server_running = True


class AuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Handle OAuth callback and extract token."""
    
    def do_GET(self):
        """Handle GET requests."""
        global captured_token, server_running, CALLBACK_URL
        
        if self.path.startswith("/callback"):
            # Parse query parameters
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Check for token in query params (OAuth redirect)
            token = params.get("token", [None])[0]
            
            if token:
                captured_token = token
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                    <head><title>Authentication Success</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1 style="color: green;">Authentication Successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                        <p>The token has been captured and will be used for testing.</p>
                    </body>
                    </html>
                """)
                server_running = False
                return
        
        # Serve login page
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            html = """
            <html>
            <head><title>Configuration Error</title></head>
            <body style="font-family: Arial, sans-serif; padding: 50px;">
                <h1 style="color: red;">Configuration Missing</h1>
                <p>Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file.</p>
                <p>These should match your frontend configuration.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return
        
        # Create login page with Supabase (use current CALLBACK_URL)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Deep Agents</title>
            <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 400px;
                    margin: 100px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                }}
                input {{
                    width: 100%;
                    padding: 12px;
                    margin: 10px 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }}
                button {{
                    width: 100%;
                    padding: 12px;
                    margin: 10px 0;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }}
                button:hover {{
                    background: #0056b3;
                }}
                .error {{
                    color: red;
                    margin: 10px 0;
                }}
                .success {{
                    color: green;
                    margin: 10px 0;
                }}
                .toggle {{
                    text-align: center;
                    margin: 15px 0;
                }}
                .toggle a {{
                    color: #007bff;
                    cursor: pointer;
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Deep Agents Login</h1>
                <div id="error" class="error"></div>
                <div id="success" class="success"></div>
                
                <form id="authForm">
                    <input type="email" id="email" placeholder="Email" required>
                    <input type="password" id="password" placeholder="Password" required>
                    <button type="submit" id="submitBtn">Sign In</button>
                </form>
                
                <div class="toggle">
                    <a id="toggleLink" onclick="toggleMode()">Don't have an account? Sign up</a>
                </div>
            </div>
            
            <script>
                const supabaseUrl = '{SUPABASE_URL}';
                const supabaseKey = '{SUPABASE_ANON_KEY}';
                const supabase = window.supabase.createClient(supabaseUrl, supabaseKey);
                
                let isSignUp = false;
                
                function toggleMode() {{
                    isSignUp = !isSignUp;
                    const form = document.getElementById('authForm');
                    const submitBtn = document.getElementById('submitBtn');
                    const toggleLink = document.getElementById('toggleLink');
                    
                    if (isSignUp) {{
                        submitBtn.textContent = 'Sign Up';
                        toggleLink.textContent = 'Already have an account? Sign in';
                    }} else {{
                        submitBtn.textContent = 'Sign In';
                        toggleLink.textContent = 'Don't have an account? Sign up';
                    }}
                }}
                
                document.getElementById('authForm').addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const errorDiv = document.getElementById('error');
                    const successDiv = document.getElementById('success');
                    const submitBtn = document.getElementById('submitBtn');
                    
                    errorDiv.textContent = '';
                    successDiv.textContent = '';
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Please wait...';
                    
                    try {{
                        if (isSignUp) {{
                            const {{ data, error }} = await supabase.auth.signUp({{
                                email: email,
                                password: password,
                                options: {{
                                    emailRedirectTo: '{CALLBACK_URL}'
                                }}
                            }});
                            
                            if (error) {{
                                errorDiv.textContent = error.message;
                                submitBtn.disabled = false;
                                submitBtn.textContent = 'Sign Up';
                                return;
                            }}
                            
                            if (data.session) {{
                                // Auto-signed in
                                window.location.href = '{CALLBACK_URL}?token=' + data.session.access_token;
                            }} else {{
                                successDiv.textContent = 'Account created! Please check your email to confirm.';
                                submitBtn.disabled = false;
                                submitBtn.textContent = 'Sign Up';
                            }}
                        }} else {{
                            const {{ data, error }} = await supabase.auth.signInWithPassword({{
                                email: email,
                                password: password
                            }});
                            
                            if (error) {{
                                errorDiv.textContent = error.message;
                                submitBtn.disabled = false;
                                submitBtn.textContent = 'Sign In';
                                return;
                            }}
                            
                            if (data.session) {{
                                // Redirect with token
                                window.location.href = '{CALLBACK_URL}?token=' + data.session.access_token;
                            }}
                        }}
                    }} catch (err) {{
                        errorDiv.textContent = 'An error occurred: ' + err.message;
                        submitBtn.disabled = false;
                        submitBtn.textContent = isSignUp ? 'Sign Up' : 'Sign In';
                    }}
                }});
            </script>
        </body>
        </html>
        """.format(
            SUPABASE_URL=SUPABASE_URL,
            SUPABASE_ANON_KEY=SUPABASE_ANON_KEY,
            CALLBACK_URL=CALLBACK_URL
        )
        
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress server logs."""
        pass


def start_callback_server():
    """Start a local server to capture the OAuth callback."""
    global server_running
    
    try:
        with socketserver.TCPServer(("", CALLBACK_PORT), AuthCallbackHandler) as httpd:
            print(f"[OK] Callback server started on http://localhost:{CALLBACK_PORT}")
            while server_running:
                httpd.handle_request()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"[ERROR] Port {CALLBACK_PORT} is already in use.")
            print(f"       Please close the application using that port or wait a moment and try again.")
        else:
            print(f"[ERROR] Failed to start server: {e}")
        server_running = False


async def main():
    """Main function."""
    global captured_token, CALLBACK_PORT, CALLBACK_URL
    
    print("=" * 80)
    print("Deep Agents - Interactive Login & Test")
    print("=" * 80)
    print()
    
    # Check configuration
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("[ERROR] SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        print()
        print("Add these to your .env file:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_ANON_KEY=your-anon-key")
        print()
        print("These should match your frontend configuration.")
        sys.exit(1)
    
    print(f"[OK] Supabase URL: {SUPABASE_URL}")
    print(f"[OK] LangGraph URL: {LANGGRAPH_URL}")
    
    # Find available port (in case default is taken)
    try:
        CALLBACK_PORT = find_free_port()
        CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}/callback"
        print(f"[OK] Using callback port: {CALLBACK_PORT}")
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    print()
    
    # Start callback server in background
    server_thread = Thread(target=start_callback_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start and verify it's running
    await asyncio.sleep(1)
    
    # Check if server started successfully
    if not server_running:
        print("[ERROR] Failed to start callback server. Exiting.")
        sys.exit(1)
    
    # Open browser
    login_url = f"http://localhost:{CALLBACK_PORT}/"
    print(f"[*] Opening browser for login...")
    print(f"   URL: {login_url}")
    print()
    print("Please log in using your email and password.")
    print("The browser will automatically close after successful login.")
    print()
    
    webbrowser.open(login_url)
    
    # Wait for token to be captured
    print("[*] Waiting for authentication...")
    max_wait = 300  # 5 minutes max
    waited = 0
    while captured_token is None and waited < max_wait:
        await asyncio.sleep(1)
        waited += 1
        if waited % 10 == 0:
            print(f"   Still waiting... ({waited}s)")
    
    if not captured_token:
        print()
        print("[ERROR] Timeout: No token captured. Please try again.")
        sys.exit(1)
    
    print()
    print("[SUCCESS] Authentication successful! Token captured.")
    print()
    
    # Save token to environment for the example script
    os.environ["AUTH_TOKEN"] = captured_token
    
    # Import and run the example
    print("=" * 80)
    print("Running example_multiple_graphs.py with your token...")
    print("=" * 80)
    print()
    
    try:
        # Import the example module
        sys.path.insert(0, str(Path(__file__).parent))
        from example_multiple_graphs import example_multiple_graphs
        
        # Run with the captured token
        await example_multiple_graphs(captured_token, LANGGRAPH_URL)
        
    except ImportError as e:
        print(f"[ERROR] Error importing example script: {e}")
        print("Make sure example_multiple_graphs.py is in the same directory.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error running example: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("[SUCCESS] All done! Your token is saved in the environment.")
    print("=" * 80)
    print()
    print("To use the token in other scripts, run:")
    print(f"  export AUTH_TOKEN='{captured_token[:20]}...'")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        sys.exit(0)

