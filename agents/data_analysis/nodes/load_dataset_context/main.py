from data.dataloader import DataLoader

from agents.data_analysis.state import AgentState


def load_dataset_context(_: AgentState) -> dict:
    """Load local parquet and emit compact schema/context metadata."""
    loader = DataLoader()
    df = loader.load_data_from_local()
    context = {
        "num_rows": int(len(df)),
        "columns": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "null_fraction": {k: round(float(df[k].isna().mean()), 4) for k in df.columns},
        "sample_values": {
            k: [str(v) for v in df[k].dropna().astype(str).head(3).tolist()] for k in df.columns
        },
        "suggested_derived_features": [
            "text_length (len(plain_text))",
            "has_question_mark ('?' in plain_text)",
            "has_why (regex \\bwhy\\b in plain_text)",
            "is_first_turn (normalized message_index == 0)",
        ],
    }
    return {"dataframe_path": str(loader.output_path), "dataset_context": context}
