"""MCP server layer."""

import logging
import os
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from lib.env_vars_loader import EnvVarsLoader

logger = logging.getLogger(__name__)

_mcp_client: MultiServerMCPClient | None = None


def _mcp_connections() -> dict[str, dict[str, Any]]:
    EnvVarsLoader.load_env_vars()
    key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not key:
        logger.warning("TAVILY_API_KEY is not set; Tavily MCP search will likely fail.")
    return {
        "tavily": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "tavily-mcp@latest"],
            "env": {"TAVILY_API_KEY": key},
        }
    }


async def get_tools() -> list[Any]:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MultiServerMCPClient(_mcp_connections())
    return await _mcp_client.get_tools()
