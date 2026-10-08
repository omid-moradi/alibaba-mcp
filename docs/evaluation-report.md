# Alibaba MCP — tool-selection & quality evaluation report

Generated: 2026-10-08 (by `scripts/evaluate.py`, in-memory MCP transport, mock provider — real measured values only).

| # | Query | Expected tool | Discoverable | Args contract | Invocation | Structured output | Error handling | Latency (ms) |
|---|-------|---------------|--------------|---------------|------------|------------------|----------------|--------------|
| 1 | Find flights from Tehran to Mashhad tomorrow | `search_flights` | PASS | PASS | PASS | PASS | PASS | 132.9 |
| 2 | Find a hotel in Mashhad for three nights | `search_hotels` | PASS | PASS | PASS | PASS | PASS | 17.3 |
| 3 | Compare the cheapest and fastest travel options | `compare_travel_options` | PASS | PASS | PASS | PASS | PASS | 22.2 |
| 4 | What are the cancellation rules? | `search_travel_policies` | PASS | PASS | PASS | PASS | PASS | 3.8 |

## Latency summary (end-to-end MCP tool calls)

- samples: 4
- mean: 44.1 ms
- median: 19.7 ms
- min: 3.8 ms / max: 132.9 ms

## Notes & limitations

- Discoverability is a lexical proxy for LLM tool selection: it checks
  that query intent keywords occur in the tool descriptions that
  `tools/list` exposes to the model. It does not measure an actual
  LLM's selection accuracy; run `examples/langgraph_agent.py` with a
  real model for end-to-end agent evaluation.
- Latency is measured over the in-memory transport with the mock
  provider; it reflects MCP protocol + validation overhead, not
  network or upstream API time.
- All data is mock; live Alibaba.ir access is not available
  (see docs/live-integration-notes.md).
