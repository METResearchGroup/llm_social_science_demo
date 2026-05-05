from __future__ import annotations

from typing import Any

from agents.data_analysis.state import AgentState


def merge_results(state: AgentState) -> dict[str, dict[str, Any]]:
    """Merge parallel worker outputs into a stable object."""
    outputs = state.get("worker_outputs") or []
    merged = {
        "num_workers": len(outputs),
        "workers": sorted(outputs, key=lambda x: x.get("worker_id", -1)),
    }
    return {"merged_results": merged}
