from agents.lit_review.state import AgentState


def collect_query(state: AgentState) -> dict:
    """Ensure `query` is set: use CLI-provided value or prompt interactively."""
    q = (state.get("query") or "").strip()
    if not q:
        q = input("Enter your research query: ").strip()
    if not q:
        raise ValueError("A non-empty research query is required.")
    return {"query": q}
