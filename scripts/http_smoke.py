#!/usr/bin/env python3
"""Start the real FastAPI app briefly and verify health and semantic HTML identity."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_MARKER = 'data-app-id="food-bank-recall-closure-agent"'
DASHBOARD_HEADING = "Turn a recall notice into verified internal action."


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch(url: str, timeout_seconds: float = 30.0) -> tuple[int, str, str]:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:  # noqa: S310 - loopback smoke endpoint
                return response.status, response.read().decode("utf-8", errors="replace"), response.headers.get_content_type()
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def main() -> None:
    port = free_port()
    env = os.environ.copy()
    env.update({"APP_ENV": "development", "AI_MODE": "mock", "USE_FIRESTORE": "false", "USE_CLOUD_STORAGE": "false", "PORT": str(port)})
    command = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"]
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    failure: BaseException | None = None
    server_output = ""
    try:
        health_status, health_body, health_type = fetch(f"http://127.0.0.1:{port}/healthz")
        if health_status != 200 or health_type != "application/json" or json.loads(health_body).get("status") != "ok":
            raise RuntimeError(f"Health endpoint failed: {health_status} {health_type} {health_body[:500]}")

        dashboard_status, dashboard_body, dashboard_type = fetch(f"http://127.0.0.1:{port}/")
        if dashboard_status != 200 or dashboard_type != "text/html":
            raise RuntimeError(f"Dashboard endpoint failed: {dashboard_status} {dashboard_type}")
        missing = [marker for marker in (APP_MARKER, DASHBOARD_HEADING) if marker not in dashboard_body]
        if missing:
            raise RuntimeError(f"Dashboard semantic contract failed; missing {missing!r}; body sample={dashboard_body[:300]!r}")

        readiness_status, readiness_body, readiness_type = fetch(f"http://127.0.0.1:{port}/api/readiness")
        readiness = json.loads(readiness_body)
        if readiness_status != 200 or readiness_type != "application/json" or "cloud_deployment" not in readiness:
            raise RuntimeError("Readiness endpoint failed its redacted JSON contract")

        print(json.dumps({"status": "PASS", "healthz": health_status, "dashboard": dashboard_status, "readiness": readiness_status, "app_marker": "PASS", "mode": "MOCK_GEMINI"}, indent=2))
    except BaseException as exc:
        failure = exc
    finally:
        process.terminate()
        try:
            server_output, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            server_output, _ = process.communicate(timeout=5)

    if failure is not None:
        if server_output.strip():
            print("--- server output ---", file=sys.stderr)
            print(server_output[-8000:], file=sys.stderr)
        raise failure


if __name__ == "__main__":
    main()
