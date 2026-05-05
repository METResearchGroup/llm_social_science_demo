import re
from typing import Any

from data.dataloader import DataLoader

from agents.data_analysis.state import AgentState


def analyze_first_vs_rest(_: AgentState) -> dict[str, dict[str, Any]]:
    """Compute deterministic v1 metrics for first-turn vs later turns."""
    loader = DataLoader()
    df = loader.load_data_from_local()

    working_df = df.copy()
    working_df["message_index"] = (
        working_df["message_index"].astype("string").str.extract(r"(-?\d+)", expand=False)
    )
    working_df["message_index"] = working_df["message_index"].fillna("-1").astype(int)
    working_df["plain_text"] = working_df["plain_text"].fillna("").astype(str)

    # Contract requires first-turn derivation from message_index == 0.
    # ShareChat slices may be 1-indexed, so normalize to keep the same predicate.
    index_shift = 1 if int(working_df["message_index"].min()) >= 1 else 0
    working_df["normalized_message_index"] = working_df["message_index"] - index_shift
    working_df["is_first_turn"] = working_df["normalized_message_index"] == 0
    working_df["text_length"] = working_df["plain_text"].str.len()
    working_df["has_question_mark"] = working_df["plain_text"].str.contains(r"\?")
    working_df["has_why"] = working_df["plain_text"].str.contains(r"\bwhy\b", flags=re.IGNORECASE)

    first = working_df[working_df["is_first_turn"]]
    rest = working_df[~working_df["is_first_turn"]]

    def _rate(series: Any) -> float:
        return float(series.mean()) if len(series) else 0.0

    result: dict[str, Any] = {
        "counts": {
            "first_turn_rows": int(len(first)),
            "non_first_turn_rows": int(len(rest)),
        },
        "average_text_length": {
            "first_turn": round(float(first["text_length"].mean()) if len(first) else 0.0, 2),
            "non_first_turn": round(float(rest["text_length"].mean()) if len(rest) else 0.0, 2),
        },
        "question_rate": {
            "first_turn": round(_rate(first["has_question_mark"]), 4),
            "non_first_turn": round(_rate(rest["has_question_mark"]), 4),
        },
        "lexical_cue_rate_why": {
            "first_turn": round(_rate(first["has_why"]), 4),
            "non_first_turn": round(_rate(rest["has_why"]), 4),
        },
    }

    first_len = result["average_text_length"]["first_turn"]
    rest_len = result["average_text_length"]["non_first_turn"]
    first_q = result["question_rate"]["first_turn"]
    rest_q = result["question_rate"]["non_first_turn"]
    interpretation = (
        "First-turn messages are generally longer than later turns."
        if first_len > rest_len
        else "Later turns are generally longer than first-turn messages."
    )
    interpretation += (
        " First turns are more likely to contain questions."
        if first_q > rest_q
        else " Later turns are more likely to contain questions."
    )
    result["interpretation"] = interpretation

    return {"analysis_result": result}
