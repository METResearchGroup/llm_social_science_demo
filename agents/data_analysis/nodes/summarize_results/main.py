from typing import Any

from agents.data_analysis.state import AgentState


def summarize_results(state: AgentState) -> dict[str, str]:
    """Format final report text for the answerable path."""
    goal = state.get("analysis_goal", "")
    result: dict[str, Any] = state.get("analysis_result", {})
    report = "\n".join(
        [
            "# Data Analysis Agent Report",
            "",
            f"Goal: {goal}",
            "",
            "## First-vs-rest trend metrics",
            str(result),
            "",
            "## Interpretation",
            str(result.get("interpretation", "")),
        ]
    )
    print(report)
    return {"report": report}
