from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from agents.lit_review.nodes.constants import LLM_MODEL
from agents.lit_review.state import AgentState

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

REPORT_PATH = Path(__file__).resolve().parent.parent.parent / "report.md"

_REPORT_TEMPLATE_INSTRUCTIONS = """\
Write a markdown literature report using EXACTLY this heading hierarchy and order (no other top-level #):

# Paper report

## Executive Summary
(2–4 short paragraphs: restate the question, what the listed sources collectively suggest, and key limitations.)

## Sections
(Under this heading, write 2–5 thematic subsections. Each subsection MUST use heading level ### with a short descriptive title, e.g. ### Methods and measurement. Body paragraphs follow each ### heading. Group themes only from the sources; do not invent studies.)

## Future Directions
(Concrete next steps for search or research implied by gaps in the sources.)

## Conclusion
(1–2 paragraphs closing the report.)

Rules:
- Use only the headings shown (# Paper report, ## Executive Summary, ## Sections, ### …, ## Future Directions, ## Conclusion).
- Stay grounded in the listed titles/URLs; do not cite papers not represented in the list.
- Output ONLY the markdown report body starting with the line `# Paper report`. No preamble, no code fences.
"""


def _strip_markdown_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:markdown)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def _wrap_report(body: str) -> str:
    body = body.strip()
    return f"---\n\n{body}\n\n---\n"


def _write_report(content: str) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(content, encoding="utf-8")


async def draft_summary(state: AgentState) -> dict:
    """Synthesize retrieved links into a structured paper report and write ``report.md``."""
    papers = list(state.get("papers") or [])
    query = (state.get("query") or "").strip()
    feedback_lines = [f for f in (state.get("human_feedback") or []) if str(f).strip()]
    feedback_block = (
        "\n\nHuman reviewer notes (follow unless they conflict with evidence):\n"
        + "\n".join(f"- {line}" for line in feedback_lines)
        if feedback_lines
        else ""
    )

    if not papers:
        body = (
            "# Paper report\n\n"
            "## Executive Summary\n\n"
            f"No web sources were retrieved for the research question: {query!r}. "
            "Verify TAVILY_API_KEY, network access, and Tavily MCP configuration, then re-run the agent.\n\n"
            "## Sections\n\n"
            "### Retrieval status\n\n"
            "No candidate links were available to group into themes.\n\n"
            "## Future Directions\n\n"
            "After fixing retrieval, re-run the pipeline and curate sources in the human review step.\n\n"
            "## Conclusion\n\n"
            "This report could not be grounded in external sources for this run.\n"
        )
        full = _wrap_report(body)
        _write_report(full)
        return {
            "summary": f"No sources retrieved. Wrote placeholder report to {REPORT_PATH}.",
        }

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.2)
    listed = "\n".join(f"- {p}" for p in papers[:50])
    msg = HumanMessage(
        content=(
            _REPORT_TEMPLATE_INSTRUCTIONS
            + f"\n\nResearch question:\n{query}\n\nCandidate sources:\n{listed}"
            + feedback_block
        )
    )
    resp = await llm.ainvoke([msg])
    text = _strip_markdown_fences((getattr(resp, "content", None) or "").strip())
    if not text or not text.lstrip().startswith("#"):
        text = (
            "# Paper report\n\n"
            "## Executive Summary\n\n"
            "Summary generation returned empty or invalid output; please re-run.\n\n"
            "## Sections\n\n"
            "### Source list\n\n"
            + "\n".join(f"- {p}" for p in papers[:50])
            + "\n\n## Future Directions\n\n"
            "Re-run draft_summary after checking model configuration.\n\n"
            "## Conclusion\n\n"
            "Report body was not produced automatically.\n"
        )
    full = _wrap_report(text)
    _write_report(full)

    out: dict[str, Any] = {
        "summary": f"Paper report written to {REPORT_PATH}",
    }
    if isinstance(resp, AIMessage):
        out["messages"] = [resp]
    return out
