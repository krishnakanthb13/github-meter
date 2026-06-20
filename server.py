import os
import sys
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Ensure we can import fetch_contributions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fetch_contributions import fetch_contributions

PORT = 8090

class GithubMeterHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == '/api/config':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Force reload .env
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            load_dotenv(env_path, override=True)
            
            profile_url = os.getenv("GITHUB_PROFILE", "https://github.com/krishnakanthb13")
            # Extract username
            username = profile_url.rstrip('/').split('/')[-1] if '/' in profile_url else profile_url
            
            response = {
                "profile_url": profile_url,
                "username": username
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        elif path == '/api/fetch':
            year = query_params.get('year', [None])[0]
            try:
                print(f"[SERVER] Triggering headless browser fetch for year: {year}")
                fetch_contributions(year)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                print(f"[SERVER] Error during fetch: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        else:
            # Serve the static files
            super().do_GET()

def run_server():
    # Set CWD to server directory so files are served correctly
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    server_address = ('localhost', PORT)
    try:
        httpd = HTTPServer(server_address, GithubMeterHandler)
        print(f"[SERVER] Running on http://localhost:{PORT}")
        httpd.serve_forever()
    except Exception as e:
        print(f"[SERVER] Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server()
