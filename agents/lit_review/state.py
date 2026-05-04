import operator
from typing import Annotated, Any, NotRequired, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State passed between nodes.

    ``worker_query`` / ``worker_id`` are supplied per branch via ``Send`` and are
    optional on the full-graph input.
    """

    messages: Annotated[list, add_messages]
    query: str
    search_queries: list[str]
    worker_query: NotRequired[str]
    worker_id: NotRequired[int]
    tavily_raw_hits: Annotated[list[dict[str, Any]], operator.add]
    papers: list[str]
    human_feedback: list[str]
    summary: str
