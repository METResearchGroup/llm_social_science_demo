# thread_length_vs_user_properties

- **Latest batch:** `20260504T214601Z`
- **Dataset:** `data/dataset.parquet`
- **Rows (input / after filters):** 97638 / 48873

## Limitations

ShareChat is built from **publicly shared** conversation links (self-selected threads), and this repo’s default loader slice uses the **`chatgpt`** config only (see `data/dataloader.py`). See `data/DATASET_DESCRIPTION.md` for platform imbalance, PII redaction, and paper limitations.

## Metrics (excerpt)

```json
{
  "aggregation_note": "Per-message (user rows): Spearman between turns_count (conversation) and user plain_text length.",
  "spearman_turns_count_vs_user_msg_len": {
    "rho": -0.06575515873805689,
    "pvalue": 5.669715480467026e-48
  },
  "summary_by_turn_bin": {
    "1-2": {
      "mean": 704.7571952595937,
      "median": 80.0,
      "count": 7088
    },
    "3-5": {
      "mean": 370.62699899149976,
      "median": 65.0,
      "count": 6941
    },
    "6+": {
      "mean": 267.55111353461143,
      "median": 67.0,
      "count": 34844
    }
  },
  "language_share_top8_by_bin": {
    "1-2": {
      "English": 0.6272573363431151,
      "Japanese": 0.22418171557562078,
      "Spanish": 0.033718961625282165,
      "German": 0.022714446952595935,
      "French": 0.02116252821670429,
      "Portuguese": 0.018340857787810385,
      "Chinese": 0.01664785553047404,
      "Russian": 0.013261851015801355
    },
    "6+": {
      "English": 0.639335323154632,
      "Japanese": 0.1872632303983469,
      "Chinese": 0.03412352198369877,
      "Spanish": 0.032516358627023303,
      "German": 0.03174147629434049,
      "French": 0.0239352542762025,
      "Portuguese": 0.018625875330042476,
      "Italian": 0.010790953966249569
    },
    "3-5": {
      "English": 0.6310329923642126,
      "Japanese": 0.210200259328627,
      "Spanish": 0.029966863564327907,
      "German": 0.025068433943235845,
      "Portuguese": 0.019881861403256016,
      "French": 0.019161504106036596,
      "Chinese": 0.018441146808817175,
      "Italian": 0.01555971761993949
    }
  },
  "topic_share_top8_by_bin": {
    "1-2": {
      "specific_info": 0.4741817155756208,
      "other": 0.07011851015801354,
      "computer_programming": 0.06348758465011287,
      "mathematical_calculation": 0.059678329571106095,
      "tutoring_or_teaching": 0.05431715575620767,
      "write_fiction": 0.03809255079006772,
      "argument_or_summary_generation": 0.03682279909706546,
      "unclear": 0.025112866817155757
    },
    "6+": {
      "specific_info": 0.27772356790265185,
      "other": 0.129778441051544,
      "unclear": 0.1029445528641947,
      "mathematical_calculation": 0.06928022041097463,
      "tutoring_or_teaching": 0.06899322695442543,
      "computer_programming": 0.05452875674434623,
      "greetings_and_chitchat": 0.04950637125473539,
      "relationships_and_personal_reflection": 0.04830099873722879
    },
    "3-5": {
      "specific_info": 0.38150122460740526,
      "other": 0.10070595015127504,
      "mathematical_calculation": 0.06483215674974788,
      "tutoring_or_teaching": 0.06396772799308457,
      "unclear": 0.06382365653364068,
      "computer_programming": 0.04624693848148682,
      "argument_or_summary_generation": 0.03774672237429765,
      "greetings_and_chitchat": 0.03529750756375162
    }
  }
}
```

## Figures

![visuals.png](../../results/thread_length_vs_user_properties/20260504T214601Z/visuals.png)

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
