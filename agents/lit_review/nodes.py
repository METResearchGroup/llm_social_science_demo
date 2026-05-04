from agents.lit_review.state import AgentState

def get_papers(state: AgentState) -> AgentState:
    print("Getting papers")
    return state

def get_human_feedback(state: AgentState) -> AgentState:
    print("Human review")
    return state

def draft_summary(state: AgentState) -> AgentState:
    print("Draft summary")
    return state
