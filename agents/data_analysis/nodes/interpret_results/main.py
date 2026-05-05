from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.data_analysis.nodes.constants import LLM_MODEL
from agents.data_analysis.state import AgentState


class Interpretation(BaseModel):
    """Structured narrative interpretation for merged analysis outputs."""

    key_findings: list[str] = Field(..., description="Short list of key findings grounded in results.")
    caveats: list[str] = Field(..., description="Potential data/measurement caveats.")
    short_interpretation: str = Field(..., description="One short paragraph summary.")


def interpret_results(state: AgentState) -> dict[str, str]:
    """Use LLM to interpret merged analysis outputs into narrative text."""
    goal = state.get("analysis_goal", "")
    merged = state.get("merged_results", {})
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1)
    structured = llm.with_structured_output(Interpretation)

    msg = HumanMessage(
        content=(
            "You are interpreting results from a social science data analysis.\n"
            "Return ONLY structured output.\n"
            "Use only evidence in merged_results; do not invent numbers.\n\n"
            f"User goal:\n{goal}\n\n"
            f"Merged results:\n{merged}\n"
        )
    )
    interpretation = structured.invoke([msg])
    narrative = "\n".join(
        [
            "Key findings:",
            *[f"- {item}" for item in interpretation.key_findings],
            "",
            "Caveats:",
            *[f"- {item}" for item in interpretation.caveats],
            "",
            interpretation.short_interpretation,
        ]
    )
    return {"narrative": narrative}
