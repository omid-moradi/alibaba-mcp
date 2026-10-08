"""Container healthcheck: send a real MCP initialize over Streamable HTTP.

Exits 0 when the server answers an MCP initialize request; exits 1
otherwise. No secrets are involved.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

HOST = os.environ.get("ALIBABA_MCP_HOST", "127.0.0.1")
PORT = os.environ.get("ALIBABA_MCP_PORT", "8000")
PATH = os.environ.get("ALIBABA_MCP_PATH", "/mcp")

url = f"http://{HOST}:{PORT}{PATH}"
payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2026-07-28",
        "capabilities": {},
        "clientInfo": {"name": "healthcheck", "version": "0.0.0"},
    },
}).encode()

def _extract_json_rpc(raw: bytes) -> dict[str, object]:
    """Parse a JSON or SSE-encoded JSON-RPC response body."""
    text = raw.decode(errors="replace")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    for line in stripped.splitlines():
        if line.startswith("data:"):
            payload = line.removeprefix("data:").strip()
            if payload.startswith("{"):
                return json.loads(payload)
    raise ValueError(f"no JSON-RPC payload found in response")


request = urllib.request.Request(
    url,
    data=payload,
    headers={
        "Content-Type": "application/json",
        # Required by the Streamable HTTP transport.
        "Accept": "application/json, text/event-stream",
    },
)
try:
    with urllib.request.urlopen(request, timeout=5) as response:
        body = _extract_json_rpc(response.read())
    if "result" in body:
        print("healthy: server answered MCP initialize")
        sys.exit(0)
    print(f"unhealthy: unexpected response: {body}")
    sys.exit(1)
except urllib.error.HTTPError as exc:
    if exc.code in (401, 403):
        # auth is enabled: the server is up and rejecting anonymous access
        print("healthy: server up (auth required)")
        sys.exit(0)
    print(f"unhealthy: HTTP {exc.code}")
    sys.exit(1)
except Exception as exc:  # noqa: BLE001 - healthcheck must never crash
    print(f"unhealthy: {exc}")
    sys.exit(1)
