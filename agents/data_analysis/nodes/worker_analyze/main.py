from __future__ import annotations

from typing import Any

from data.dataloader import DataLoader

from agents.data_analysis.state import AgentState


def _normalize_index(df):
    df["message_index"] = df["message_index"].astype("string").str.extract(r"(-?\d+)", expand=False)
    df["message_index"] = df["message_index"].fillna("-1").astype(int)
    index_shift = 1 if int(df["message_index"].min()) >= 1 else 0
    df["normalized_message_index"] = df["message_index"] - index_shift
    df["is_first_turn"] = df["normalized_message_index"] == 0
    return df


def _compare_boolean_rate(df, target_column: str) -> dict[str, Any]:
    if target_column not in df.columns:
        return {"error": f"Column '{target_column}' not found."}
    values = df[target_column]
    if values.dtype != bool:
        lowered = values.fillna("").astype(str).str.lower()
        if lowered.isin({"true", "false"}).mean() > 0.95:
            values = lowered.eq("true")
        else:
            return {"error": f"Column '{target_column}' is not boolean-like."}

    first = values[df["is_first_turn"]]
    rest = values[~df["is_first_turn"]]
    return {
        "first_turn_rate": round(float(first.mean()) if len(first) else 0.0, 4),
        "non_first_turn_rate": round(float(rest.mean()) if len(rest) else 0.0, 4),
        "delta": round(
            (float(first.mean()) if len(first) else 0.0) - (float(rest.mean()) if len(rest) else 0.0),
            4,
        ),
    }


def _compare_numeric_mean(df, target_column: str) -> dict[str, Any]:
    if target_column not in df.columns:
        return {"error": f"Column '{target_column}' not found."}
    numeric = (
        df[target_column]
        if str(df[target_column].dtype).startswith(("int", "float"))
        else df[target_column].astype("string").str.extract(r"(-?\d+\.?\d*)", expand=False)
    )
    numeric = numeric.astype(float)
    first = numeric[df["is_first_turn"]]
    rest = numeric[~df["is_first_turn"]]
    return {
        "first_turn_mean": round(float(first.mean()) if len(first) else 0.0, 4),
        "non_first_turn_mean": round(float(rest.mean()) if len(rest) else 0.0, 4),
        "delta": round(
            (float(first.mean()) if len(first) else 0.0) - (float(rest.mean()) if len(rest) else 0.0),
            4,
        ),
    }


def _top_categories(df, target_column: str, group_column: str) -> dict[str, Any]:
    if target_column not in df.columns:
        return {"error": f"Column '{target_column}' not found."}
    groups = [group_column] if group_column and group_column in df.columns else []
    key_cols = groups + [target_column]
    counts = (
        df[key_cols]
        .fillna("unknown")
        .astype(str)
        .value_counts()
        .head(10)
        .rename("count")
        .reset_index()
        .to_dict(orient="records")
    )
    return {"top_combinations": counts}


def worker_analyze(state: AgentState) -> dict[str, list[dict[str, Any]]]:
    """Execute a single planned subtask on local parquet data."""
    loader = DataLoader()
    df = loader.load_data_from_local().copy()
    df["plain_text"] = df["plain_text"].fillna("").astype(str)
    df["text_length"] = df["plain_text"].str.len()
    df["has_question_mark"] = df["plain_text"].str.contains(r"\?")
    df["has_why"] = df["plain_text"].str.contains(r"\bwhy\b", case=False, regex=True)
    df = _normalize_index(df)

    worker_id = int(state.get("worker_id", -1))
    task = state.get("worker_spec") or {}
    operation = str(task.get("operation", ""))
    target_column = str(task.get("target_column", ""))
    group_column = str(task.get("group_column", ""))

    if operation == "compare_boolean_rate":
        result = _compare_boolean_rate(df, target_column)
    elif operation == "compare_numeric_mean":
        result = _compare_numeric_mean(df, target_column)
    elif operation == "top_categories":
        result = _top_categories(df, target_column, group_column)
    else:
        result = {"error": f"Unsupported operation '{operation}'."}

    output = {
        "worker_id": worker_id,
        "task": task,
        "result": result,
    }
    return {"worker_outputs": [output]}
