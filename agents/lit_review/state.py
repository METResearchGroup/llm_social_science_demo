from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State passed between nodes."""
    messages: Annotated[list, add_messages]
    query: str
    papers: list[str]
    human_feedback: list[str]
    summary: str
