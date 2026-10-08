"""MCP -> LangChain tool bridge (SDK v2 client).

Converts tools discovered from an MCP server (via the official Python SDK
v2 ``Client``) into LangChain tools usable by LangGraph agents.

Why not ``langchain-mcp-adapters``? At the time of writing it still targets
the v1 SDK session API, while this project is built on SDK v2
(``mcp.Client``). The bridge below is ~70 lines, has no version conflicts,
and demonstrates exactly what an adapter must do: translate MCP tool
schemas into JSON-schema tools and forward calls over the MCP protocol.

Requires the optional ``agent`` dependency group (langchain-core).
"""

from __future__ import annotations

from typing import Any

from mcp import Client


def _describe_tool_result(result: Any) -> str:
    """Render an MCP CallToolResult for an LLM."""
    if result.is_error:
        blocks = [getattr(b, "text", str(b)) for b in result.content]
        return "TOOL ERROR: " + " ".join(blocks)
    structured = result.structured_content
    if structured is not None:
        import json

        # unwrap the {"result": ...} envelope used for list/scalar outputs
        if isinstance(structured, dict) and set(structured) == {"result"}:
            structured = structured["result"]
        return json.dumps(structured, ensure_ascii=False, default=str)
    return " ".join(getattr(b, "text", str(b)) for b in result.content)


async def as_langchain_tools(client: Client) -> list[Any]:
    """Return LangChain tools mirroring the remote MCP server's tool list."""
    from langchain_core.tools import StructuredTool

    page = await client.list_tools()
    tools: list[Any] = []
    for tool in page.tools:
        description = tool.description or tool.name
        # Attach server instructions + annotation hints so the LLM can
        # behave well (e.g. ask before destructive sandbox bookings).
        if tool.annotations and tool.annotations.destructive_hint:
            description += (
                "\n\nNOTE: this tool modifies sandbox state. Confirm with the "
                "user before calling it."
            )
        tools.append(
            StructuredTool.from_function(
                coroutine=lambda _tool_name=tool.name, **kwargs: _call(client, _tool_name, kwargs),
                name=tool.name,
                description=description,
                args_schema=_json_schema_to_pydantic(tool.name, tool.input_schema),
            )
        )
    return tools


async def _call(client: Client, name: str, arguments: dict[str, Any]) -> str:
    result = await client.call_tool(name, arguments)
    return _describe_tool_result(result)


def _json_schema_to_pydantic(name: str, schema: dict[str, Any]) -> Any:
    """Build a lightweight args model from the tool's JSON input schema."""
    from pydantic import create_model

    properties: dict[str, Any] = {}
    for field_name, spec in (schema.get("properties") or {}).items():
        field_type: Any = spec.get("type", "string")
        ann = {
            "string": (str, ...),
            "integer": (int, ...),
            "number": (float, ...),
            "boolean": (bool, ...),
        }.get(field_type, (str, ...))
        default = spec.get("default")
        if default is not None:
            properties[field_name] = (ann[0], default)
        elif field_name in (schema.get("required") or []):
            properties[field_name] = ann
        else:
            properties[field_name] = (ann[0] | None, None)
    return create_model(f"{name}Args", **properties)
