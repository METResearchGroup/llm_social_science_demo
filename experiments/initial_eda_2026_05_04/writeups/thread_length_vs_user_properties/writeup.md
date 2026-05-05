# Thread Length Vs User Properties

- Run ID: `20260505T210023Z`
- Dataset: `/Users/mark/Documents/work/llm_social_science_demo_worktree/data/dataset.parquet`
- Filtered rows: `48903` of `97638`

## Metrics

```json
{
  "bin_summary": {
    "count": {
      "1-2": 7093,
      "3-5": 6948,
      "6+": 34862
    },
    "mean": {
      "1-2": 704.260397575074,
      "3-5": 370.2535981577432,
      "6+": 267.41297114336527
    },
    "median": {
      "1-2": 80.0,
      "3-5": 65.0,
      "6+": 67.0
    }
  },
  "spearman_correlation": {
    "rho": -0.06564467553018512,
    "p_value": 7.598893232988222e-48
  }
}
```

## Figures

- `experiments/initial_eda_2026_05_04/results/thread_length_vs_user_properties/20260505T210023Z/mean_length_by_turn_bin.png`

## Caveats

- Exploratory analysis over the local slice (typically 10% ChatGPT config by default).
- Topic-specific summaries require `topic` to exist in the dataset.
