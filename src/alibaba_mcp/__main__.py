"""Command-line entry point: ``python -m alibaba_mcp`` / ``alibaba-mcp``.

Supports:
* stdio (default) — for Claude Desktop, Cursor, VS Code and other local hosts
* streamable-http — for remote/networked deployment
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="alibaba-mcp",
        description=(
            "Alibaba MCP — unofficial MCP server for Alibaba.ir-style travel "
            "discovery (portfolio project, not affiliated with Alibaba.ir)."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="stdio for local hosts (default); streamable-http to serve on a port.",
    )
    parser.add_argument("--host", default=None, help="HTTP bind host (default: 127.0.0.1).")
    parser.add_argument(
        "--port", type=int, default=None, help="HTTP bind port (default: 8000)."
    )
    args = parser.parse_args()

    from alibaba_mcp.config import Settings
    from alibaba_mcp.server import create_server

    settings = Settings()
    server = create_server(settings)

    if args.transport == "streamable-http":
        server.run(
            transport="streamable-http",
            host=args.host or settings.mcp_host,
            port=args.port or settings.mcp_port,
            streamable_http_path=settings.mcp_path,
        )
    else:
        server.run()


if __name__ == "__main__":
    main()
