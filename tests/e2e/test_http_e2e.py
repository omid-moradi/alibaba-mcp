"""End-to-end test: MCP client over Streamable HTTP to a real server process."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from contextlib import closing
from datetime import date, timedelta

from mcp import Client


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.2)
    raise TimeoutError(f"server did not start listening on port {port}")


async def test_streamable_http_end_to_end() -> None:
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "alibaba_mcp",
            "--transport",
            "streamable-http",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port(port)
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        url = f"http://127.0.0.1:{port}/mcp"
        async with Client(url) as client:
            assert client.server_info is not None
            assert client.server_info.name == "Alibaba MCP"

            result = await client.call_tool(
                "compare_travel_options",
                {"origin": "THR", "destination": "MHD", "departure_date": tomorrow},
            )
            assert not result.is_error
            data = result.structured_content
            assert data is not None and data["cheapest"] is not None
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
