from __future__ import annotations

from typing import Any

from agents.data_analysis.state import AgentState


def finalize_report(state: AgentState) -> dict[str, str]:
    """Compose and print final report text."""
    goal = state.get("analysis_goal", "")
    merged: dict[str, Any] = state.get("merged_results", {})
    narrative = state.get("narrative", "")
    report = "\n".join(
        [
            "# Data Analysis Agent Report",
            "",
            f"Goal: {goal}",
            "",
            "## Structured Results",
            str(merged),
            "",
            "## Interpretation",
            narrative,
        ]
    )
    print(report)
    return {"report": report}
