import logging

from agents.lit_review.mcp import get_tools
from agents.lit_review.nodes.tavily_search.helper import (
    coerce_tavily_args,
    hits_from_tool_result,
    pick_tavily_search_tool,
)
from agents.lit_review.state import AgentState

logger = logging.getLogger(__name__)


async def tavily_search(state: AgentState) -> dict:
    """Single Tavily search for ``worker_query`` (invoked in parallel via ``Send``)."""
    q = (state.get("worker_query") or "").strip()
    if not q:
        logger.warning("tavily_search missing worker_query; skipping.")
        return {"tavily_raw_hits": []}

    try:
        tools = await get_tools()
    except Exception as exc:
        logger.exception("Failed to load MCP tools: %s", exc)
        return {"tavily_raw_hits": []}

    tool = pick_tavily_search_tool(tools)
    if tool is None:
        logger.error("No Tavily search tool found among MCP tools.")
        return {"tavily_raw_hits": []}

    args = coerce_tavily_args(tool, q)
    try:
        raw = await tool.ainvoke(args)
    except Exception as exc:
        logger.warning("Tavily tool failed for query %r: %s", q, exc)
        return {"tavily_raw_hits": []}

    hits = hits_from_tool_result(raw, source_query=q)
    return {"tavily_raw_hits": hits}
