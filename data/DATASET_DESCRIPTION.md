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

6. **Limitations (paper §Limitations).** **Self-selection** (overshare “wins” and interesting threads), **platform imbalance**, **LLM-as-judge** proxies for completeness/topics, and analyses being **illustrative** rather than exhaustive social science.

## How this repository loads the data

See `dataloader.py`. In short:

- **Source:** `tucnguyen/ShareChat` on Hugging Face Datasets.
- **Default split slice:** first `prop` (default **10%**) of `train` for the chosen config.
- **Default config:** `chatgpt` only; other platforms require changing `config_name` (or extending the loader to concatenate configs).
- **Output:** Parquet under `data/dataset.parquet` (or `output_path`).

For cross-platform EDA, either **switch configs** and combine Parquet files with a `platform` column already present, or use the Datasets library to load multiple configs explicitly.

## Related work (Hugging Face Papers search)

The Hugging Face MCP **`paper_search`** tool was queried for neighboring literature. Papers that sit closest to ShareChat’s niche—**real user ↔ LLM logs**, **scale**, and **downstream use** (safety, alignment, analysis)—include:

| Paper (HF Papers link) | Why it is related |
| --- | --- |
| [WildChat: 1M ChatGPT Interaction Logs in the Wild](https://hf.co/papers/2405.01470) | Large “in the wild” ChatGPT logs; ShareChat cites WildChat for toxicity methodology and comparison. |
| [LMSYS-Chat-1M](https://hf.co/papers/2309.11998) | Major real conversation corpus through a **unified** arena/demo interface; contrasts with ShareChat’s **native multi-platform** design. |
| [OpenAssistant Conversations](https://hf.co/papers/2304.07327) | Crowdsourced assistant-style dialogues and alignment-related annotations; different provenance than shared-link harvesting. |
| [WILDCHAT-50M](https://hf.co/papers/2501.18511) | Synthetic / scaled follow-on building on WildChat-style data for post-training work. |
| [UltraChat / scaling instructional conversations](https://hf.co/papers/2305.14233) | Instructional multi-turn data for chat model improvement—complementary to observational “wild” corpora. |

ShareChat itself is indexed on HF Papers as [ShareChat: A Dataset of Chatbot Conversations in the Wild](https://hf.co/papers/2512.17843).

## Citations

BibTeX from the paper / dataset card:

```bibtex
@misc{yan2026sharechatdatasetchatbotconversations,
      title={ShareChat: A Dataset of Chatbot Conversations in the Wild},
      author={Yueru Yan and Tuc Nguyen and Bo Su and Melissa Lieffers and Thai Le},
      year={2026},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2512.17843},
}
```

When publishing subsets derived from the Hugging Face release, follow the dataset card’s **attribution** requirements and respect **platform terms of use**, **non-de-anonymization**, and **safety filtering** guidance stated there and in the paper’s ethical considerations.
