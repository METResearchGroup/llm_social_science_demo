# Language Mix

- Run ID: `20260505T210023Z`
- Dataset: `/Users/mark/Documents/work/llm_social_science_demo_worktree/data/dataset.parquet`
- Filtered rows: `48903` of `97638`

## Metrics

```json
{
  "english_rate": 0.6360141504611169,
  "top_languages": {
    "English": 31103,
    "Japanese": 9576,
    "Spanish": 1581,
    "German": 1441,
    "Chinese": 1435,
    "French": 1119,
    "Portuguese": 917,
    "Italian": 557,
    "Russian": 463,
    "Dutch": 169
  }
}
```

## Figures

- `experiments/initial_eda_2026_05_04/results/language_mix/20260505T210023Z/top_languages.png`
- `experiments/initial_eda_2026_05_04/results/language_mix/20260505T210023Z/english_share.png`

## Caveats

- Exploratory analysis over the local slice (typically 10% ChatGPT config by default).
- Topic-specific summaries require `topic` to exist in the dataset.
