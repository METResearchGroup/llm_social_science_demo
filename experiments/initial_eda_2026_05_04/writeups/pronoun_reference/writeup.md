# Pronoun Reference

- Run ID: `20260505T210023Z`
- Dataset: `/Users/mark/Documents/work/llm_social_science_demo_worktree/data/dataset.parquet`
- Filtered rows: `48903` of `97638`

## Metrics

```json
{
  "counts": {
    "self": 34041,
    "bot_you": 26652,
    "other_they": 12075
  },
  "per_message_any": {
    "self_reference_rate": 0.2089237879066724,
    "bot_reference_rate": 0.1888841175388013,
    "other_reference_rate": 0.07545549352800442
  }
}
```

## Figures

- `experiments/initial_eda_2026_05_04/results/pronoun_reference/20260505T210023Z/pronoun_counts.png`

## Caveats

- Exploratory analysis over the local slice (typically 10% ChatGPT config by default).
- Topic-specific summaries require `topic` to exist in the dataset.
