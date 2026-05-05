from data.dataloader import DataLoader

from agents.data_analysis.state import AgentState


def load_dataset_context(_: AgentState) -> dict[str, str]:
    """Load local parquet through DataLoader.load_data_from_local."""
    loader = DataLoader()
    _ = loader.load_data_from_local()
    return {"dataframe_path": str(loader.output_path)}
