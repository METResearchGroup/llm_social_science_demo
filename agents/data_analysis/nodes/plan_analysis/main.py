from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator

from agents.data_analysis.nodes.constants import LLM_MODEL
from agents.data_analysis.state import AgentState

MAX_SUBTASKS = 3


class PlannedSubtask(BaseModel):
    """A bounded analysis task that can run independently."""

    name: str = Field(..., description="Short task name.")
    operation: str = Field(
        ...,
        description="One of: compare_boolean_rate, compare_numeric_mean, top_categories.",
    )
    target_column: str = Field(..., description="Primary dataset column for this operation.")
    group_column: str = Field(
        "",
        description="Optional grouping column used by top_categories; empty otherwise.",
    )
    filter_description: str = Field(
        "",
        description="Optional human-readable filter intent. Leave empty if no filter.",
    )
    rationale: str = Field(..., description="Why this task helps answer the user query.")

    @field_validator("operation")
    @classmethod
    def enforce_known_operation(cls, v: str) -> str:
        allowed = {"compare_boolean_rate", "compare_numeric_mean", "top_categories"}
        if v not in allowed:
            raise ValueError(f"Unsupported operation '{v}'. Allowed: {sorted(allowed)}")
        return v


class AnalysisPlan(BaseModel):
    """Structured output for LLM task planning."""

    subtasks: list[PlannedSubtask] = Field(
        ...,
        description=f"1 to {MAX_SUBTASKS} subtasks for answering the query.",
    )

    @field_validator("subtasks")
    @classmethod
    def bounded_subtasks(cls, v: list[PlannedSubtask]) -> list[PlannedSubtask]:
        if not (1 <= len(v) <= MAX_SUBTASKS):
            raise ValueError(f"Expected 1..{MAX_SUBTASKS} subtasks, got {len(v)}")
        return v


def plan_analysis(state: AgentState) -> dict[str, list[dict]]:
    """Create a bounded, structured analysis plan from query + dataset context."""
    goal = state.get("analysis_goal", "")
    dataset_context = state.get("dataset_context", {})

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.0)
    structured = llm.with_structured_output(AnalysisPlan)
    msg = HumanMessage(
        content=(
            "You are planning a data analysis over a pandas DataFrame.\n"
            "Return ONLY the structured output.\n\n"
            "Constraints:\n"
            "- Plan between 1 and 3 subtasks.\n"
            "- Use only these operations: compare_boolean_rate, compare_numeric_mean, top_categories.\n"
            "- target_column and group_column must be valid columns from the dataset context.\n"
            "- Prefer robust tasks that can run on noisy real-world data.\n\n"
            f"Dataset context:\n{dataset_context}\n\n"
            f"User query:\n{goal}\n"
        )
    )
    planned = structured.invoke([msg])
    return {"subtasks": [task.model_dump() for task in planned.subtasks]}
