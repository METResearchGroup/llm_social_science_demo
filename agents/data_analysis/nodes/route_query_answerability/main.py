from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.data_analysis.nodes.constants import LLM_MODEL
from agents.data_analysis.state import AgentState

DATASET_DESCRIPTION_PATH = Path(__file__).resolve().parents[4] / "data" / "DATASET_DESCRIPTION.md"
DATASET_DESCRIPTION = DATASET_DESCRIPTION_PATH.read_text(encoding="utf-8")


class AnswerabilityResult(BaseModel):
    """Structured answerability output for deterministic graph routing."""

    answerable: bool = Field(
        ...,
        description=(
            "True only when the user's question can be answered using fields and derivations "
            "explicitly described in the dataset context."
        ),
    )


def route_query_answerability(state: AgentState) -> str:
    """Route query to answerable vs unanswerable branch via LLM structured output."""
    query = state.get("analysis_goal", "")
    msg = HumanMessage(
        content=(
            "You are deciding whether a user query is answerable using only the dataset context.\n"
            "Return ONLY the structured boolean output.\n\n"
            "Decision rule:\n"
            "- answerable=true only if the query can be answered with this dataset's columns or "
            "obvious deterministic derivations from them.\n"
            "- answerable=false for requests needing external world knowledge, future events, "
            "or data not present in the dataset context.\n\n"
            f"Dataset context:\n{DATASET_DESCRIPTION}\n\n"
            f"User query:\n{query}\n"
        )
    )
    try:
        llm = ChatOpenAI(model=LLM_MODEL, temperature=0.0)
        structured = llm.with_structured_output(AnswerabilityResult)
        result = structured.invoke([msg])
    except Exception as exc:
        raise RuntimeError(
            "LLM answerability routing failed. Set OPENAI_API_KEY to run the data analysis "
            "router, then retry."
        ) from exc
    return "answerable" if result.answerable else "unanswerable"
