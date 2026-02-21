"""
server.py — StockPulse local dev server
Serves demo.html and proxies Airia API calls to avoid CORS issues.

Usage:
    uv run server.py
    Then open http://localhost:8080/demo.html
"""

import json
import os
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

AIRIA_WEBHOOK_URL = os.environ.get("AIRIA_WEBHOOK_URL", "")
AIRIA_API_KEY     = os.environ.get("AIRIA_API_KEY", "")
PORT = 8080


class ProxyHandler(SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        """Handle CORS preflight for the proxy endpoint."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/agent":
            self._proxy_airia()
        else:
            self.send_error(404)

    def _proxy_airia(self):
        """Forward the browser's request to Airia and return the response."""
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        try:
            req = urllib.request.Request(
                AIRIA_WEBHOOK_URL,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Api-Key":    AIRIA_API_KEY,
                    "User-Agent":   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "Accept":       "application/json, */*",
                    "Origin":       "http://localhost:8080",
                    "Referer":      "http://localhost:8080/",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                status  = resp.status
                payload = resp.read()
        except urllib.error.HTTPError as e:
            status  = e.code
            payload = e.read()
        except Exception as e:
            self.send_response(502)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Api-Key, Authorization")

    def log_message(self, fmt, *args):
        # Suppress noisy GET logs for static files; keep POST logs
        if self.command == "POST":
            print(f"  → {self.path}  {args[1]}")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"StockPulse server running at http://localhost:{PORT}")
    print(f"  Airia proxy: POST /api/agent → {AIRIA_WEBHOOK_URL[:60]}...")
    print(f"  Open: http://localhost:{PORT}/demo.html")
    HTTPServer(("", PORT), ProxyHandler).serve_forever()
