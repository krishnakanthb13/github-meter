import os
import sys
import re
import json
import time
import logging
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from dotenv import load_dotenv

# Ensure we can import fetch_contributions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fetch_contributions import fetch_contributions

PORT = 8090
YEAR_REGEX = re.compile(r'^\d{4}$')
MIN_YEAR = 2015

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

# Load .env once at startup
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

_profile_url = os.getenv("GITHUB_PROFILE", "https://github.com/krishnakanthb13")
_username = _profile_url.rstrip('/').split('/')[-1] if '/' in _profile_url else _profile_url

# Rate limiting: serialize contribution fetches
_fetch_lock = threading.Lock()

# Account info cache
_account_cache = {
    "data": None,
    "ts": 0,
    "etag": None,
    "last_modified": None,
    "last_fail_ts": 0
}
_account_lock = threading.Lock()
_ACCOUNT_CACHE_TTL = 3600  # 1 hour
_RETRY_COOLDOWN = 300      # 5 minutes


def _fetch_account_info():
    now = time.time()
    
    # If cache is fresh, return it
    if _account_cache["data"] and (now - _account_cache["ts"]) < _ACCOUNT_CACHE_TTL:
        return _account_cache["data"]

    # Cooldown to serve stale cache during persistent outages
    if _account_cache["data"] and (now - _account_cache["last_fail_ts"]) < _RETRY_COOLDOWN:
        return _account_cache["data"]

    with _account_lock:
        # Double-check after acquiring lock
        if _account_cache["data"] and (now - _account_cache["ts"]) < _ACCOUNT_CACHE_TTL:
            return _account_cache["data"]
        if _account_cache["data"] and (now - _account_cache["last_fail_ts"]) < _RETRY_COOLDOWN:
            return _account_cache["data"]

        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "github-meter"
            }
            if _account_cache["etag"]:
                headers["If-None-Match"] = _account_cache["etag"]
            if _account_cache["last_modified"]:
                headers["If-Modified-Since"] = _account_cache["last_modified"]

            req = Request(
                f"https://api.github.com/users/{_username}",
                headers=headers
            )
            try:
                with urlopen(req, timeout=10) as resp:
                    etag = resp.getheader("ETag")
                    last_mod = resp.getheader("Last-Modified")
                    
                    data = json.loads(resp.read().decode())
                    info = {
                        "created_at": data.get("created_at"),
                    }
                    _account_cache["data"] = info
                    _account_cache["ts"] = now
                    _account_cache["etag"] = etag
                    _account_cache["last_modified"] = last_mod
                    return info
            except HTTPError as e:
                # Catch HTTP 304 Not Modified
                if e.code == 304:
                    log.info("GitHub account info not modified (304). Renewing cache lifetime.")
                    _account_cache["ts"] = now
                    return _account_cache["data"]
                raise e
        except Exception as e:
            log.warning("Failed to fetch account info: %s", e)
            _account_cache["last_fail_ts"] = now
            return _account_cache["data"]


class GithubMeterHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8090')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
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
            self.send_header('Cache-Control', 'max-age=300')
            self.end_headers()

            response = {
                "profile_url": _profile_url,
                "username": _username
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif path == '/api/account':
            info = _fetch_account_info()
            if info:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'max-age=3600')
                self.end_headers()
                self.wfile.write(json.dumps(info).encode('utf-8'))
            else:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Could not fetch account info"}).encode('utf-8'))

        elif path == '/api/fetch':
            year = query_params.get('year', [None])[0]
            now = time.localtime().tm_year

            # Validate year parameter
            if not year or not YEAR_REGEX.match(year) or int(year) < MIN_YEAR or int(year) > now:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                msg = {"status": "error", "message": f"Invalid year. Must be {MIN_YEAR}–{now}."}
                self.wfile.write(json.dumps(msg).encode('utf-8'))
                return

            if not _fetch_lock.acquire(blocking=False):
                self.send_response(429)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                msg = {"status": "error", "message": "A fetch is already in progress."}
                self.wfile.write(json.dumps(msg).encode('utf-8'))
                return

            try:
                log.info("Fetching contribution HTML for year: %s", year)
                fetch_contributions(year)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                log.error("Error during fetch: %s", e)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            finally:
                _fetch_lock.release()
        else:
            super().do_GET()

    def log_message(self, format, *args):
        log.info(format % args)


def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    server_address = ('localhost', PORT)
    try:
        httpd = ThreadingHTTPServer(server_address, GithubMeterHandler)
        log.info("Running on http://localhost:%d", PORT)
        httpd.serve_forever()
    except Exception as e:
        log.error("Failed to start server: %s", e)
        sys.exit(1)


if __name__ == '__main__':
    run_server()
