import os
import sys
import secrets
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from dotenv import load_dotenv

# Load existing environment variables
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

PORT = 8000
REDIRECT_URI = f"http://localhost:{PORT}/callback"

# Global state to share data from request handler
oauth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress server logs to keep console clean
        return

    def do_GET(self):
        global oauth_code
        parsed_url = urllib.parse.urlparse(self.path)
        
        if parsed_url.path == "/callback":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            if "code" in query_params:
                oauth_code = query_params["code"][0]
                
                # Send a beautiful premium feedback page to the user
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                
                success_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>LinkedIn Authorization Successful</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            background: radial-gradient(circle at top left, #0e1e38 0%, #050b14 100%);
                            color: #ffffff;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                        }
                        .container {
                            background: rgba(255, 255, 255, 0.05);
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.1);
                            padding: 40px;
                            border-radius: 20px;
                            text-align: center;
                            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                            max-width: 450px;
                        }
                        .icon {
                            font-size: 64px;
                            margin-bottom: 20px;
                            color: #0077b5;
                            animation: pulse 2s infinite ease-in-out;
                        }
                        h1 {
                            font-size: 24px;
                            margin: 0 0 10px 0;
                            font-weight: 600;
                            letter-spacing: -0.5px;
                        }
                        p {
                            color: #a0aec0;
                            font-size: 15px;
                            line-height: 1.6;
                            margin: 0 0 24px 0;
                        }
                        .status {
                            display: inline-block;
                            padding: 8px 16px;
                            background: rgba(72, 187, 120, 0.2);
                            border: 1px solid #48bb78;
                            color: #48bb78;
                            border-radius: 50px;
                            font-weight: 500;
                            font-size: 13px;
                        }
                        @keyframes pulse {
                            0% { transform: scale(1); }
                            50% { transform: scale(1.05); }
                            100% { transform: scale(1); }
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="icon">🔗</div>
                        <h1>Authorization Completed!</h1>
                        <p>You have successfully authenticated with LinkedIn. You can now close this browser tab and return to the terminal.</p>
                        <div class="status">Token Received Successfully</div>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode("utf-8"))
            else:
                error_msg = query_params.get("error_description", ["Unknown error"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family:sans-serif; text-align:center; padding-top:100px;">
                    <h1 style="color:red;">Authorization Failed</h1>
                    <p>{error_msg}</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode("utf-8"))

def write_to_env(updates):
    # Read existing content if it exists
    env_content = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_content[k.strip()] = v.strip()
                    
    # Update with new values
    env_content.update(updates)
    
    # Write back
    with open(ENV_PATH, "w") as f:
        f.write("# LinkedIn API Credentials\n")
        f.write(f"LINKEDIN_CLIENT_ID={env_content.get('LINKEDIN_CLIENT_ID', '')}\n")
        f.write(f"LINKEDIN_CLIENT_SECRET={env_content.get('LINKEDIN_CLIENT_SECRET', '')}\n")
        f.write(f"LINKEDIN_REDIRECT_URI={env_content.get('LINKEDIN_REDIRECT_URI', REDIRECT_URI)}\n\n")
        f.write("# Generated Access Tokens\n")
        f.write(f"LINKEDIN_ACCESS_TOKEN={env_content.get('LINKEDIN_ACCESS_TOKEN', '')}\n")
        f.write(f"LINKEDIN_PERSON_URN={env_content.get('LINKEDIN_PERSON_URN', '')}\n\n")
        f.write("# Optional Configuration\n")
        f.write(f"GEMINI_API_KEY={env_content.get('GEMINI_API_KEY', '')}\n")

def run_oauth_flow():
    # Verify environment values
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    
    if not client_id or not client_secret or client_id == "your_client_id_here" or client_secret == "your_client_secret_here":
        print("\n" + "="*70)
        print("💡 LINKEDIN API SETUP REQUIRED")
        print("="*70)
        print("Please enter your LinkedIn application details.")
        print("Get these from the LinkedIn Developer Portal: https://www.linkedin.com/developers/")
        print("Make sure 'Share on LinkedIn' is enabled and redirect URI is set to:")
        print(f"   {REDIRECT_URI}")
        print("-"*70)
        client_id = input("Enter LinkedIn Client ID: ").strip()
        client_secret = input("Enter LinkedIn Client Secret: ").strip()
        
        if not client_id or not client_secret:
            print("❌ Client ID and Client Secret are required. Aborting.")
            sys.exit(1)
            
        write_to_env({
            "LINKEDIN_CLIENT_ID": client_id,
            "LINKEDIN_CLIENT_SECRET": client_secret
        })
        
    print("\n🚀 Starting local authentication server...")
    server = HTTPServer(("localhost", PORT), OAuthCallbackHandler)
    
    # Generate authorization URL
    state = secrets.token_hex(16)
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "scope": "w_member_social"  # Scope to post text and image shares
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(auth_params)}"
    
    print("\n👉 Please authorize the app by clicking/opening this URL in your browser:")
    print("-" * 80)
    print(auth_url)
    print("-" * 80)
    
    # Open browser automatically
    webbrowser.open(auth_url)
    
    # Wait for the callback request
    print("\nWaiting for redirect callback on port 8000...")
    while oauth_code is None:
        server.handle_request()
        
    print("✅ Authorization code received.")
    
    # Exchange authorization code for access token
    print("\nExchanging code for access token...")
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = {
        "grant_type": "authorization_code",
        "code": oauth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        access_token = token_info.get("access_token")
        
        if not access_token:
            print("❌ Access token was not found in response:", token_info)
            sys.exit(1)
            
        print("✅ Access token retrieved successfully.")
        
        # Retrieve the profile URN using versioned API (/rest/me)
        print("\nFetching profile URN...")
        me_url = "https://api.linkedin.com/rest/me"
        me_headers = {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": "202401",  # Standard versioning header
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        me_response = requests.get(me_url, headers=me_headers)
        me_response.raise_for_status()
        me_info = me_response.json()
        person_id = me_info.get("id")
        
        if not person_id:
            print("❌ Member ID not found in /rest/me response:", me_info)
            sys.exit(1)
            
        person_urn = f"urn:li:person:{person_id}"
        print(f"✅ Authenticated as: {person_urn}")
        
        # Save credentials to .env
        write_to_env({
            "LINKEDIN_ACCESS_TOKEN": access_token,
            "LINKEDIN_PERSON_URN": person_urn,
            "LINKEDIN_CLIENT_ID": client_id,
            "LINKEDIN_CLIENT_SECRET": client_secret
        })
        
        print("\n" + "="*70)
        print("🎉 SUCCESS! CREDENTIALS STORED SECURELY IN .env")
        print("="*70)
        print("Variables set:")
        print(f"  LINKEDIN_ACCESS_TOKEN: [REDACTED {access_token[:6]}...{access_token[-6:]}]")
        print(f"  LINKEDIN_PERSON_URN: {person_urn}")
        print("="*70)
        
    except requests.exceptions.RequestException as e:
        print("\n❌ Error exchanging token or fetching profile URN:")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status: {e.response.status_code}")
            print(f"Details: {e.response.text}")
        else:
            print(e)
        sys.exit(1)

if __name__ == "__main__":
    run_oauth_flow()
