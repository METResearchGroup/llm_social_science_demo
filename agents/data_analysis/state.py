import operator
from typing import Annotated, Any, NotRequired, TypedDict


class AgentState(TypedDict, total=False):
    """State passed between data-analysis nodes."""

    user_query: str
    analysis_goal: str
    route: str
    dataset_context: dict[str, Any]
    subtasks: list[dict[str, Any]]
    worker_id: NotRequired[int]
    worker_spec: NotRequired[dict[str, Any]]
    worker_outputs: Annotated[list[dict[str, Any]], operator.add]
    merged_results: dict[str, Any]
    narrative: str
    dataframe_path: str
    analysis_result: dict[str, Any]
    report: str
