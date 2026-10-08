"""LangGraph agent over Alibaba MCP.

A ReAct agent whose ONLY tools are the ones it discovers from the Alibaba
MCP server at runtime (real MCP protocol — no direct imports of server
code). The LLM decides which tools to call.

Setup:
    uv sync --group agent              # installs langgraph/langchain
    # plus the provider package for your model, e.g.:
    uv pip install langchain-openai    # or langchain-google-genai, langchain-anthropic

Configuration (choose one):
    set ALIBABA_AGENT_MODEL=openai:gpt-4o-mini
    set ALIBABA_AGENT_MODEL=google-genai:gemini-2.0-flash
    set ALIBABA_AGENT_MODEL=anthropic:claude-sonnet-4-5
plus the matching API key environment variable (OPENAI_API_KEY, etc.).

Usage:
    uv run python examples/langgraph_agent.py
    uv run python examples/langgraph_agent.py "Find the cheapest flight from Tehran to Mashhad"
"""

from __future__ import annotations

import asyncio
import os
import sys

from mcp import Client, StdioServerParameters


async def main() -> int:
    question = " ".join(sys.argv[1:]) or (
        "Find the cheapest flight from Tehran to Mashhad tomorrow."
    )
    model_spec = os.environ.get("ALIBABA_AGENT_MODEL", "openai:gpt-4o-mini")

    # Import only after the agent extras are known to be installed.
    try:
        from langchain.chat_models import init_chat_model
        from langgraph.prebuilt import create_react_agent
    except ImportError:  # pragma: no cover - environment guard
        print("LangChain/LangGraph not installed. Run: uv sync --group agent")
        return 1

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client"))
    from mcp_langchain_bridge import as_langchain_tools

    server = StdioServerParameters(command=sys.executable, args=["-m", "alibaba_mcp"])
    async with Client(server) as mcp_client:
        tools = await as_langchain_tools(mcp_client)
        print(f"Discovered {len(tools)} MCP tools: {[t.name for t in tools]}")

        llm = init_chat_model(model_spec)
        agent = create_react_agent(llm, tools)
        print(f"\nUser: {question}\n")
        final_state = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"recursion_limit": 25},
        )
        for message in final_state["messages"]:
            role = getattr(message, "type", "unknown")
            content = getattr(message, "content", "")
            if role == "ai" and content:
                print(f"Agent: {content}")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
