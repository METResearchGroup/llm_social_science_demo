from agents.lit_review.state import AgentState


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
