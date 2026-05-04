from agents.lit_review.state import AgentState


def get_human_feedback(state: AgentState) -> dict:
    n = len(state.get("papers") or [])
    print(f"Human review — {n} unique paper link(s) after merge.")
    return {}
