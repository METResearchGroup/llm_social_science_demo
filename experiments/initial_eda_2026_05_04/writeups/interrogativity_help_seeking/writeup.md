# interrogativity_help_seeking

- **Latest batch:** `20260504T214601Z`
- **Dataset:** `data/dataset.parquet`
- **Rows (input / after filters):** 97638 / 48873

## Limitations

ShareChat is built from **publicly shared** conversation links (self-selected threads), and this repo’s default loader slice uses the **`chatgpt`** config only (see `data/dataloader.py`). See `data/DATASET_DESCRIPTION.md` for platform imbalance, PII redaction, and paper limitations.

## Metrics (excerpt)

```json
{
  "rate_ends_with_question_mark": 0.20117447261269003,
  "rate_contains_help_seeking_cue_regex": 0.3052196509320074,
  "rate_either_question_or_cue": 0.3876782681644262,
  "by_language": {
    "English": {
      "rate": 0.5448992058643861,
      "n": 31103.0
    },
    "Japanese": {
      "rate": 0.02413036665622062,
      "n": 9573.0
    },
    "Spanish": {
      "rate": 0.260126582278481,
      "n": 1580.0
    },
    "German": {
      "rate": 0.2081887578070784,
      "n": 1441.0
    },
    "Chinese": {
      "rate": 0.029965156794425088,
      "n": 1435.0
    },
    "French": {
      "rate": 0.25246195165622204,
      "n": 1117.0
    },
    "Portuguese": {
      "rate": 0.346782988004362,
      "n": 917.0
    },
    "Italian": {
      "rate": 0.26032315978456017,
      "n": 557.0
    },
    "Russian": {
      "rate": 0.3080260303687636,
      "n": 461.0
    },
    "Dutch": {
      "rate": 0.3192771084337349,
      "n": 166.0
    },
    "Hebrew": {
      "rate": 0.23846153846153847,
      "n": 130.0
    },
    "Polish": {
      "rate": 0.047619047619047616,
      "n": 42.0
    },
    "Swedish": {
      "rate": 0.05128205128205128,
      "n": 39.0
    },
    "Finnish": {
      "rate": 0.15625,
      "n": 32.0
    },
    "Arabic": {
      "rate": 0.09090909090909091,
      "n": 22.0
    }
  },
  "by_topic": {
    "specific_info": {
      "rate": 0.4488078541374474,
      "n": 15686.0
    },
    "other": {
      "rate": 0.21476040573627142,
      "n": 5718.0
    },
    "unclear": {
      "rate": 0.1311787072243346,
      "n": 4208.0
    },
    "mathematical_calculation": {
      "rate": 0.5156677821721934,
      "n": 3287.0
    },
    "tutoring_or_teaching": {
      "rate": 0.39560779461800183,
      "n": 3233.0
    },
    "computer_programming": {
      "rate": 0.474354174466492,
      "n": 2671.0
    },
    "greetings_and_chitchat": {
      "rate": 0.208594881699662,
      "n": 2071.0
    },
    "relationships_and_personal_reflection": {
      "rate": 0.4767206477732793,
      "n": 1976.0
    },
    "write_fiction": {
      "rate": 0.39568345323741005,
      "n": 1807.0
    },
    "argument_or_summary_generation": {
      "rate": 0.6621346023113528,
      "n": 1471.0
    },
    "edit_or_critique_provided_text": {
      "rate": 0.34034560480841475,
      "n": 1331.0
    },
    "create_an_image": {
      "rate": 0.23892773892773891,
      "n": 858.0
    },
    "data_analysis": {
      "rate": 0.5682926829268292,
      "n": 820.0
    },
    "how_to_advice": {
      "rate": 0.6423135464231354,
      "n": 657.0
    },
    "health_fitness_beauty_or_self_care": {
      "rate": 0.5872193436960277,
      "n": 579.0
    }
  }
}
```

## Figures

![visuals.png](../../results/interrogativity_help_seeking/20260504T214601Z/visuals.png)

## Dataset documentation (reference)

<details><summary>DATASET_DESCRIPTION.md (truncated)</summary>

```text
# ShareChat — dataset description for this repository

This note summarizes what **ShareChat** is, how it was built and licensed, headline results from the paper, how we load it in `dataloader.py`, and how that lines up with the exploratory questions in `experiments/initial_eda_2026_05_04/README.md`. Primary sources: [ShareChat on Hugging Face](https://huggingface.co/datasets/tucnguyen/ShareChat), [ShareChat (HTML) on arXiv](https://arxiv.org/html/2512.17843v2), and the companion PDF identifier [arXiv:2512.17843](https://arxiv.org/abs/2512.17843).

## What the data is

ShareChat is a **turn-level, multi-platform corpus** of real user ↔ assistant chat from **five products**: ChatGPT, Perplexity, Grok, Gemini, and Claude. Rows are **individual messages** (not one row per conversation), with shared fields so analyses can aggregate by conversation using keys such as `url` and `turns_count`.

**Collection context.** Conversations come from **publicly shared links** users created on each platform (not private logs). The authors discover URLs in part via **Internet Archive / Wayback Machine** pattern search, then render share pages with **Selenium**, parse HTML into structured records, and run a **PII pipeline** (Microsoft Presidio, spaCy NER, custom rules) across multiple languages. Collection was conducted under **IRB approval** (paper reports #28569). The Hugging Face hub notes the repository is **gated**: you must log in and accept the **ShareChat Dataset License Agreement** before downloading files.

**Temporal and linguistic scope (paper).** Roughly **April 2023 – October 2025** overall; per-platform windows differ (e.g., Grok from Dec 2024 in the appendix table). **101 languages** at the corpus level; **message-level** language detection (lingua-py in the paper) feeds distributions—English dominates, with Japanese as the second-largest slice in the paper’s Figure 2 narrative.

**Scale (paper Table 1).** About **142,808 conversations**, **660,293 turns**, mean **4.62 turns** per conversation. **ChatGPT** dominates volume (~72% of conversations); **Claude** is a small fraction (~0.7%). Token means are **much longer for assistant than user** turns (paper: ~1,115 vs ~135 mean tokens using the Llama-2 tokenizer), reflecting long answers, code, citations, and tool-like outputs.

**Hub updates.** The [dataset card](https://huggingface.co/datasets/tucnguyen/ShareChat) states that as of **5 Apr 2026** an additional **`topic`** column was added per conversation (topic at message/conversation granularity as documented on the card). The card also notes a policy update (Apr 2026) allowing **derivative subsets** with clear attribution to ShareChat.

## Schema and platform-specific fields

**Core columns (all platforms, per HF card and paper):** `platform`, `url`, `turns_count`, `message_index`, `role`, `plain_text`, `detected_language_final` (and, on the hub, **`topic`** after the 2026 update).

**Extra columns vary by platform** (paper Table 2 and §2): e.g., Perplexity/Grok **sources** and citation-like metadata; Grok/Claude **thinking** traces; Claude **code** / **analysis** / **version**; Gemini **model** and timestamps; ChatGPT **model** and **message_create_time** / **create_time**; Perplexity engagement fields such as **views** / **shares**. **Turn-level timestamps** are emphasized for **ChatGPT** and **Grok** in the paper’s temporal analyses.

On Hugging Face the dataset is organized by **config** (one per platform, e.g. `chatgpt`). Our `DataLoader` in `dataloader.py` defaults to **`HF_DEFAULT_CONFIG = "chatgpt"`** and loads `train[:{pct}%]` into local Parquet.

## Key findings from the paper (selected)

1. **Motivation vs prior corpora.** ShareChat argues prior datasets often **homogenize** interaction through a single demo UI, drop **non-text affordances** (citations, thinking blocks), skew toward **shorter threads**, and suffer **observer bias** when users know they are in a study. ShareChat trades that for **self-selection bias** (users choose what to share).

2. **Depth and languages.** Compared to datasets in Table 1 (e.g., LMSYS-Chat-1M, WildChat, ShareGPT), ShareChat emphasizes **longer threads and longer assistant outputs** and **broader language coverage** in their reported statistics.

3. **Toxicity.** Turn-level toxicity (Detoxify and OpenAI moderation, following WildChat-style thresholds) is **lower overall** than WildChat and broadly competitive or better on several comparisons the paper reports. There is a strong **rank correlation** between user-side and model-side toxicity **within** platforms (interpreted as “mirroring”). **Claude** can rank higher on some toxicity metrics in their breakdowns—read in context of small sample size and detection limits.

4. **Topics.** User messages are classified into **24 fine-grained** categories (Llama-3.1-8B-Instruct), rolled up to **seven** high-level groups. **“Seeking information”** dominates (~39.6% of requests in §3.3); **Other/Unknown** is large (~19%); technical help, writing, practical guidance, and self-expression fill much of the rest; **multimedia** is small (~2.4%). Platforms differ in role (e.g., Perplexity vs Claude specialization).

5. **Representative analyses.** **Completeness:** automated pipeline (Qwen3-8B) labels whether intentions are fully, partially, or not met—**ChatGPT and Claude** skew toward **complete** verdicts more than others in their Figure 5 narrative. **Source grounding:** Grok’s sources are **concentrated on X**; Perplexity draws from a **wider mix** (Wikipedia, Reddit, NIH, etc.) and can attach **very many** sources per thread. **Timestamps:** ChatGPT shows **decreasing** model latency over turn index; Grok shows **increasing** latency; user dwell time relates **weakly** to output length at the individual level despite aggregate trends.

6. **Limitations (paper §Limitations).** **Self-selection** (overshare “wins” and interesting threads), **platform imbalance**, **LLM-as-judge** proxies for completeness/t
```

</details>
