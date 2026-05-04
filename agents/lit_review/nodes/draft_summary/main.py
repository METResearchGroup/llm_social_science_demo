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
(2-4 short paragraphs: restate the question, what the listed sources collectively suggest, and key limitations.)

## Sections
(Under this heading, write 2-5 thematic subsections. Each subsection MUST use heading level ### with a short descriptive title, e.g. ### Methods and measurement. Body paragraphs follow each ### heading. Group themes only from the sources; do not invent studies.)

## Future Directions
(Concrete next steps for search or research implied by gaps in the sources.)

## Conclusion
(1-2 paragraphs closing the report.)

Rules:
- Use only the headings shown (# Paper report, ## Executive Summary, ## Sections, ### …, ## Future Directions, ## Conclusion).
- Stay grounded in the listed titles/URLs; do not cite papers not represented in the list.
- Output ONLY the markdown report body starting with the line `# Paper report` as the first non-empty line. No preamble, no code fences.
- Do not start or end the document with horizontal rules (lines that are only ---, ***, or ___); those break many Markdown previews.
"""


def _strip_markdown_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:markdown)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


_HRULE_LINE = re.compile(r"^ {0,3}(?:-{3,}|_{3,}|\*{3,})\s*$")


def _strip_leading_trailing_hrules_and_blank(text: str) -> str:
    """Remove outer blank lines and standalone thematic-break lines (avoids YAML/HR ambiguity)."""
    lines = text.replace("\r\n", "\n").split("\n")
    while lines and (not lines[0].strip() or _HRULE_LINE.match(lines[0])):
        lines.pop(0)
    while lines and (not lines[-1].strip() or _HRULE_LINE.match(lines[-1])):
        lines.pop()
    return "\n".join(lines).strip()


def _first_non_empty_line(text: str) -> str:
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.strip():
            return line.strip()
    return ""


def _markdown_report_issues(text: str) -> list[str]:
    """Structural checks so ``report.md`` renders predictably in common Markdown viewers."""
    issues: list[str] = []
    if not text.strip():
        issues.append("Document is empty.")
        return issues
    first = _first_non_empty_line(text)
    if _HRULE_LINE.match(first):
        issues.append(
            "The first non-empty line is a horizontal rule (---/___/***), which many renderers treat as YAML front matter or mis-parse."
        )
    if not first.startswith("#"):
        issues.append("The first non-empty line must be a heading starting with '#'.")
    elif not re.match(r"^#\s+Paper report\s*$", first):
        issues.append("The top-level heading must be exactly `# Paper report` (first heading in the file).")
    if "\x00" in text:
        issues.append("Document contains null bytes.")
    return issues


async def _repair_markdown_report(llm: ChatOpenAI, broken: str, issues: list[str]) -> str:
    bullet = "\n".join(f"- {i}" for i in issues)
    msg = HumanMessage(
        content=(
            "You fix Markdown so it renders correctly in GitHub-style preview.\n\n"
            "Validation failures:\n"
            f"{bullet}\n\n"
            "Return ONLY the corrected Markdown. Requirements:\n"
            "- First non-empty line must be exactly: # Paper report\n"
            "- Do not use YAML front matter. Do not begin or end the file with a horizontal-rule-only line.\n"
            "- Preserve factual content; keep the same heading outline (# / ## / ###) as much as possible.\n"
            "- No surrounding code fences.\n\n"
            "Document to fix:\n"
            f"{broken}"
        )
    )
    resp = await llm.ainvoke([msg])
    return _strip_markdown_fences((getattr(resp, "content", None) or "").strip())


async def _ensure_renderer_safe_markdown(llm: ChatOpenAI, raw: str) -> str:
    """Normalize, validate, and optionally LLM-repair until checks pass or repair is exhausted."""
    text = _strip_leading_trailing_hrules_and_blank(
        _strip_markdown_fences(raw.lstrip("\ufeff").strip())
    )
    issues = _markdown_report_issues(text)
    if not issues:
        return text
    repaired = await _repair_markdown_report(llm, text, issues)
    text = _strip_leading_trailing_hrules_and_blank(_strip_markdown_fences(repaired.strip()))
    issues2 = _markdown_report_issues(text)
    if issues2:
        repaired2 = await _repair_markdown_report(llm, text, issues2)
        text = _strip_leading_trailing_hrules_and_blank(_strip_markdown_fences(repaired2.strip()))
    return text


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
        body = await _ensure_renderer_safe_markdown(
            ChatOpenAI(model=LLM_MODEL, temperature=0.0), body
        )
        _write_report(body if body.endswith("\n") else body + "\n")
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
    text = _strip_leading_trailing_hrules_and_blank(
        _strip_markdown_fences(
            (getattr(resp, "content", None) or "").lstrip("\ufeff").strip()
        )
    )
    if not text:
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
    text = await _ensure_renderer_safe_markdown(llm, text)
    if _markdown_report_issues(text):
        text = (
            "# Paper report\n\n"
            "## Executive Summary\n\n"
            "The model output could not be normalized into renderer-safe Markdown after automatic repair. "
            "See the candidate sources in **Sections** below.\n\n"
            "## Sections\n\n"
            "### Source list\n\n"
            + "\n".join(f"- {p}" for p in papers[:50])
            + "\n\n## Future Directions\n\n"
            "Re-run the agent or adjust the draft_summary repair prompt.\n\n"
            "## Conclusion\n\n"
            "Automatic report generation did not yield a valid Markdown outline.\n"
        )
    out_body = text if text.endswith("\n") else text + "\n"
    _write_report(out_body)

    out: dict[str, Any] = {
        "summary": f"Paper report written to {REPORT_PATH}",
    }
    if isinstance(resp, AIMessage):
        out["messages"] = [resp]
    return out
