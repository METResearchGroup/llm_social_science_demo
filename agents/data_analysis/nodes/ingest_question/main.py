from agents.data_analysis.state import AgentState


def ingest_question(state: AgentState) -> dict[str, str]:
    """Normalize user query into a canonical analysis goal string."""
    query = (state.get("user_query") or "").strip()
    goal = query or "analyze first message versus later messages"
    return {"analysis_goal": goal}
