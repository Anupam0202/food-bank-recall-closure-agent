#!/usr/bin/env python3
"""Offline fallback for deterministic UI and health QA only; production remains FastAPI."""
from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

ROUTES = {
    "/": "/preview/dashboard.html",
    "/inventory": "/preview/inventory.html",
    "/partner/tasks": "/preview/partner-tasks.html",
    "/readiness": "/preview/readiness.html",
    "/styles.css": "/preview/styles.css",
    "/app.js": "/preview/app.js",
}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            body = json.dumps(
                {
                    "status": "ok",
                    "ai_mode": "MOCK_GEMINI",
                    "repository": "IN_MEMORY",
                    "media": "LOCAL_MEDIA",
                    "server": "offline-preview",
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.path = ROUTES.get(self.path, self.path)
        return super().do_GET()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"Offline preview listening on http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
