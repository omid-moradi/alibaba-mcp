"""Root shim for MCP tooling.

``uv run mcp dev server.py`` and ``uv run mcp run server.py`` look for a
module-level server object named ``mcp`` (or ``server``/``app``) in this
file; importing the package-level instance keeps a single source of truth.
"""

from alibaba_mcp.server import mcp

__all__ = ["mcp"]
