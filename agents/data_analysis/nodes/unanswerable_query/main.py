from agents.data_analysis.state import AgentState


def unanswerable_query(_: AgentState) -> dict[str, str]:
    """Emit exact contract string for unanswerable questions."""
    message = "this query can't be answered by the data"
    print(message)
    return {"report": message}
