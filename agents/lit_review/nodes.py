import json
import logging
from typing import Any

from agents.lit_review.mcp import get_tools
from agents.lit_review.state import AgentState

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

LLM_MODEL = "gpt-5-nano"
DIVERSIFY_TEMPERATURE = 0.85


class DiversifiedQueries(BaseModel):
    """Exactly five diverse search formulations for literature discovery."""

    queries: list[str] = Field(
        ...,
        description="Five distinct web search queries (different angles, terms, methods).",
    )

    @field_validator("queries")
    @classmethod
    def exactly_five_non_empty(cls, v: list[str]) -> list[str]:
        cleaned = [q.strip() for q in v if q and str(q).strip()]
        if len(cleaned) != 5:
            raise ValueError(f"Expected exactly 5 non-empty queries, got {len(cleaned)}.")
        return cleaned


def collect_query(state: AgentState) -> dict:
    """Ensure `query` is set: use CLI-provided value or prompt interactively."""
    q = (state.get("query") or "").strip()
    if not q:
        q = input("Enter your research query: ").strip()
    if not q:
        raise ValueError("A non-empty research query is required.")
    return {"query": q}


async def diversify_queries(state: AgentState) -> dict:
    """Rewrite the user query into five diverse search strings for broader recall."""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=DIVERSIFY_TEMPERATURE)
    structured = llm.with_structured_output(DiversifiedQueries)
    base = state["query"]
    msg = HumanMessage(
        content=(
            "You help social-science / interdisciplinary researchers find literature. "
            "Given the research question below, output exactly FIVE distinct web search "
            "queries a researcher could run (different synonyms, mechanisms, populations, "
            "methods, or adjacent concepts). Each query should be short (under ~200 chars), "
            "specific, and not a duplicate of the others.\n\n"
            f"Research question:\n{base}"
        )
    )
    raw = await structured.ainvoke([msg])
    if isinstance(raw, DiversifiedQueries):
        diversified = raw
    elif isinstance(raw, dict):
        diversified = DiversifiedQueries.model_validate(raw)
    else:
        raise TypeError(f"Unexpected structured output type: {type(raw)!r}")
    return {"search_queries": diversified.queries, "messages": [msg]}


def _pick_tavily_search_tool(tools: list[Any]) -> Any | None:
    for t in tools:
        name = (getattr(t, "name", None) or "").lower()
        if "tavily" in name and "search" in name:
            return t
    for t in tools:
        name = (getattr(t, "name", None) or "").lower()
        if "search" in name:
            return t
    return tools[0] if tools else None


def _coerce_tavily_args(tool: Any, query: str) -> dict[str, Any]:
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


def _hits_from_tool_result(raw: Any, source_query: str) -> list[dict[str, Any]]:
    body: dict[str, Any] | None
    if raw is None:
        return []
    if isinstance(raw, dict):
        body = raw
    else:
        text = str(raw).strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return []
        body = parsed if isinstance(parsed, dict) else None
    if body is None:
        return []
    results = body.get("results")
    if results is None and isinstance(body.get("content"), list):
        results = body["content"]
    if not isinstance(results, list):
        return []
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

    tool = _pick_tavily_search_tool(tools)
    if tool is None:
        logger.error("No Tavily search tool found among MCP tools.")
        return {"tavily_raw_hits": []}

    args = _coerce_tavily_args(tool, q)
    try:
        raw = await tool.ainvoke(args)
    except Exception as exc:
        logger.warning("Tavily tool failed for query %r: %s", q, exc)
        return {"tavily_raw_hits": []}

    hits = _hits_from_tool_result(raw, source_query=q)
    return {"tavily_raw_hits": hits}


def merge_paper_results(state: AgentState) -> dict:
    """Dedupe Tavily hits from all parallel branches into ``papers``."""
    rows = list(state.get("tavily_raw_hits") or [])
    seen: set[str] = set()
    papers: list[str] = []
    for row in rows:
        url = (row.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        title = (row.get("title") or "").strip() or url
        src = (row.get("source_query") or "").strip()
        suffix = f" (from: {src})" if src else ""
        papers.append(f"{title} | {url}{suffix}")
    return {"papers": papers}


def get_human_feedback(state: AgentState) -> dict:
    n = len(state.get("papers") or [])
    print(f"Human review — {n} unique paper link(s) after merge.")
    return {}

def draft_summary(state: AgentState) -> AgentState:
    print("Draft summary")
    return state
