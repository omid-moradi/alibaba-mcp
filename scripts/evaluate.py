"""Tool-selection & quality evaluation suite for Alibaba MCP.

Runs a deterministic, dependency-free evaluation of the server's agent
fitness WITHOUT requiring an LLM API key:

1. discoverability  — do the query's intent keywords appear in the tool
   descriptions exposed by tools/list? (what an LLM sees when choosing)
2. argument contract — do the documented parameters exist in the tool schema?
3. invocation       — call the expected tool with canonical arguments and
   validate the structured output shape.
4. error handling   — call with invalid arguments; the result must be a
   model-readable error, not a crash.
5. latency          — measured end-to-end tool call latency (in-memory
   transport, mock provider).

Writes docs/evaluation-report.md with the REAL measured numbers.

Usage:
    uv run python scripts/evaluate.py
"""

from __future__ import annotations

import statistics
import time
from datetime import date, timedelta
from pathlib import Path

from mcp import Client

from alibaba_mcp.config import ProviderMode, Settings
from alibaba_mcp.server import create_server

TOMORROW = (date.today() + timedelta(days=1)).isoformat()

CASES = [
    {
        "query": "Find flights from Tehran to Mashhad tomorrow",
        "intent_terms": ["flights"],
        "tool": "search_flights",
        "args": {"origin": "THR", "destination": "MHD", "departure_date": TOMORROW},
        "bad_args": {"origin": "XXX", "destination": "MHD", "departure_date": TOMORROW},
        "error_expect": "Unknown airport code",
        "output_shape": ["count", "flights", "is_mock_data"],
    },
    {
        "query": "Find a hotel in Mashhad for three nights",
        "intent_terms": ["hotel"],
        "tool": "search_hotels",
        "args": {
            "city_id": "MHD",
            "check_in": TOMORROW,
            "check_out": (date.today() + timedelta(days=4)).isoformat(),
        },
        "bad_args": {
            "city_id": "XXX",
            "check_in": TOMORROW,
            "check_out": (date.today() + timedelta(days=3)).isoformat(),
        },
        "error_expect": "No hotel inventory",
        "output_shape": ["count", "hotels", "is_mock_data"],
    },
    {
        "query": "Compare the cheapest and fastest travel options",
        "intent_terms": ["cheapest", "fastest"],
        "tool": "compare_travel_options",
        "args": {"origin": "THR", "destination": "MHD", "departure_date": TOMORROW},
        "bad_args": {"origin": "THR", "destination": "MHD", "departure_date": "2020-01-01"},
        "error_expect": "in the past",
        "output_shape": ["cheapest", "fastest", "options"],
    },
    {
        "query": "What are the cancellation rules?",
        "intent_terms": ["cancellation"],
        "tool": "search_travel_policies",
        "args": {"query": "cancellation rules"},
        "bad_args": None,
        "error_expect": None,
        "output_shape": ["result"],
    },
]


def render_report(results: list[dict[str, object]], latencies_ms: list[float]) -> str:
    def ok(flag: object) -> str:
        return "PASS" if flag else "FAIL"

    lines = [
        "# Alibaba MCP — tool-selection & quality evaluation report",
        "",
        f"Generated: {date.today().isoformat()} (by `scripts/evaluate.py`, "
        "in-memory MCP transport, mock provider — real measured values only).",
        "",
        "| # | Query | Expected tool | Discoverable | Args contract | "
        "Invocation | Structured output | Error handling | Latency (ms) |",
        "|---|-------|---------------|--------------|---------------|"
        "------------|------------------|----------------|--------------|",
    ]
    for r in results:
        lines.append(
            f"| {r['i']} | {r['query']} | `{r['tool']}` | "
            f"{ok(r['discoverable'])} | {ok(r['args_contract'])} | "
            f"{ok(r['invocation'])} | {ok(r['output_shape'])} | "
            f"{ok(r['error_handling'])} | {r['latency_ms']:.1f} |"
        )
    lines += [
        "",
        "## Latency summary (end-to-end MCP tool calls)",
        "",
        f"- samples: {len(latencies_ms)}",
        f"- mean: {statistics.mean(latencies_ms):.1f} ms",
        f"- median: {statistics.median(latencies_ms):.1f} ms",
        f"- min: {min(latencies_ms):.1f} ms / max: {max(latencies_ms):.1f} ms",
        "",
    ]
    return "\n".join(lines)


async def main() -> None:
    settings = Settings(
        provider=ProviderMode.MOCK,
        rate_limit_max_calls=0,
    )
    server = create_server(settings)
    results: list[dict[str, object]] = []
    latencies_ms: list[float] = []

    async with Client(server, raise_exceptions=True) as client:
        tools_page = await client.list_tools()
        tools = {t.name: t for t in tools_page.tools}

        for i, case in enumerate(CASES, start=1):
            tool = tools[case["tool"]]
            description = tool.description or ""
            schema = tool.input_schema or {}

            # 1. discoverability: intent terms visible in description
            discoverable = all(term.lower() in description.lower() for term in case["intent_terms"])
            # 2. argument contract: all args exist as schema properties
            properties = schema.get("properties", {})
            args_contract = all(a in properties for a in case["args"])

            # 3. invocation + latency + 4. output shape
            start = time.perf_counter()
            result = await client.call_tool(case["tool"], case["args"])
            latency_ms = (time.perf_counter() - start) * 1000
            latencies_ms.append(latency_ms)
            invocation = not result.is_error
            data = result.structured_content or {}
            output_shape = all(key in data for key in case["output_shape"])

            # 4. error handling
            error_handling = True
            if case["bad_args"] is not None:
                bad = await client.call_tool(case["tool"], case["bad_args"])
                error_handling = bool(bad.is_error)
                if case["error_expect"]:
                    error_handling = error_handling and (
                        case["error_expect"] in bad.content[0].text
                    )

            results.append(
                {
                    "i": i,
                    "query": case["query"],
                    "tool": case["tool"],
                    "discoverable": discoverable,
                    "args_contract": args_contract,
                    "invocation": invocation,
                    "output_shape": output_shape,
                    "error_handling": error_handling,
                    "latency_ms": latency_ms,
                }
            )

    report = render_report(results, latencies_ms)
    report += (
        "\n## Notes & limitations\n\n"
        "- Discoverability is a lexical proxy for LLM tool selection: it checks\n"
        "  that query intent keywords occur in the tool descriptions that\n"
        "  `tools/list` exposes to the model. It does not measure an actual\n"
        "  LLM's selection accuracy; run `examples/langgraph_agent.py` with a\n"
        "  real model for end-to-end agent evaluation.\n"
        "- Latency is measured over the in-memory transport with the mock\n"
        "  provider; it reflects MCP protocol + validation overhead, not\n"
        "  network or upstream API time.\n"
        "- All data is mock; live Alibaba.ir access is not available\n"
        "  (see docs/live-integration-notes.md).\n"
    )
    out_path = Path("docs") / "evaluation-report.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Report written to {out_path}")
    failed = [
        r
        for r in results
        if not all(
            r[k]
            for k in (
                "discoverable",
                "args_contract",
                "invocation",
                "output_shape",
                "error_handling",
            )
        )
    ]
    print(f"{len(results) - len(failed)}/{len(results)} cases passed all checks")
    for r in failed:
        print("  FAILED:", r["query"])
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
