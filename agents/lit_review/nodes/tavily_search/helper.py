import json
import re
from typing import Any


def pick_tavily_search_tool(tools: list[Any]) -> Any | None:
    for t in tools:
        name = (getattr(t, "name", None) or "").lower()
        if name == "tavily_search":
            return t
    for t in tools:
        name = (getattr(t, "name", None) or "").lower()
        if "tavily" in name and "search" in name:
            return t
    for t in tools:
        name = (getattr(t, "name", None) or "").lower()
        if "search" in name:
            return t
    return tools[0] if tools else None


def coerce_tavily_args(tool: Any, query: str) -> dict[str, Any]:
    schema = getattr(tool, "args_schema", None)
    if schema is not None:
        fields = getattr(schema, "model_fields", None)
        if isinstance(fields, dict) and fields:
            keys = set(fields.keys())
            if "query" in keys:
                return {"query": query}
            if "q" in keys:
                return {"q": query}
    return {"query": query}


def hits_from_results_dicts(results: list[Any], source_query: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("link")
        if not url:
            continue
        hits.append(
            {
                "url": str(url).strip(),
                "title": str(item.get("title") or "").strip(),
                "snippet": str(item.get("content") or item.get("snippet") or "")[:800],
                "source_query": source_query,
            }
        )
    return hits


def hits_from_tavily_mcp_text(blob: str, source_query: str) -> list[dict[str, Any]]:
    """Parse Tavily MCP ``tavily_search`` prose block (Title / URL / Content)."""
    t = blob.replace("\r\n", "\n")
    hits: list[dict[str, Any]] = []
    for m in re.finditer(r"Title:\s*(.+?)\s*\nURL:\s*(https?://\S+)", t):
        title, url = m.group(1).strip(), m.group(2).strip()
        rest = t[m.end() :]
        next_title = re.search(r"\nTitle:\s", rest)
        block = rest[: next_title.start()] if next_title else rest
        cm = re.search(r"Content:\s*(.*)", block, flags=re.DOTALL)
        snippet = cm.group(1).strip()[:800] if cm else ""
        hits.append(
            {
                "url": url,
                "title": title or url,
                "snippet": snippet,
                "source_query": source_query,
            }
        )
    return hits


def hits_from_tool_result(raw: Any, source_query: str) -> list[dict[str, Any]]:
    if raw is None:
        return []

    if isinstance(raw, dict):
        body = raw
        results = body.get("results")
        if results is None and isinstance(body.get("content"), list):
            results = body["content"]
        if isinstance(results, list) and results and isinstance(results[0], dict):
            return hits_from_results_dicts(results, source_query)
        return []

    if isinstance(raw, list):
        parts: list[str] = []
        for item in raw:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                parts.append(str(item["text"]))
        blob = "\n".join(parts) if parts else ""
        if blob.strip():
            return hits_from_tavily_mcp_text(blob, source_query)
        return []

    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        if s.startswith("{"):
            try:
                parsed = json.loads(s)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(parsed, dict):
                    return hits_from_tool_result(parsed, source_query)
        return hits_from_tavily_mcp_text(s, source_query)

    return hits_from_tool_result(str(raw).strip(), source_query)
