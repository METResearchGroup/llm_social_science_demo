"""MCP server layer."""

from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from lib.env_vars_loader import EnvVarsLoader

env_vars = EnvVarsLoader.load_env_vars()

MCP_CONFIG = {
    "tavily": {
        "command": "npx",
        "args": ["-y", "tavily-mcp@latest"],
        "env": {
            "TAVILY_API_KEY": env_vars["TAVILY_API_KEY"],
        }
    }
}

_mcp_client = None

async def get_tools() -> list[Any]:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MultiServerMCPClient(MCP_CONFIG)
    return await _mcp_client.get_tools()
