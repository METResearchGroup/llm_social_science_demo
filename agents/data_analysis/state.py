from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """State passed between data-analysis nodes."""

    user_query: str
    analysis_goal: str
    route: str
    dataframe_path: str
    analysis_result: dict[str, Any]
    report: str
