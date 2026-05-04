from typing import Any

from agents.lit_review.nodes.constants import LLM_MODEL
from agents.lit_review.state import AgentState

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI


async def draft_summary(state: AgentState) -> dict:
    """Synthesize retrieved links into a short literature-review style summary."""
    papers = state.get("papers") or []
    query = (state.get("query") or "").strip()
    if not papers:
        summary = (
            f"No sources were retrieved for: {query!r}. "
            "Check TAVILY_API_KEY, network access, and Tavily MCP (stdio) configuration."
        )
        return {"summary": summary}

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.2)
    listed = "\n".join(f"- {p}" for p in papers[:50])
    msg = HumanMessage(
        content=(
            "You are assisting with a literature review. Given the research question "
            "and the candidate sources (titles and URLs from web search), write a concise "
            "2-4 paragraph summary that: (1) restates the question, (2) groups themes or "
            "methods reflected in the sources, (3) notes gaps or tensions, and (4) suggests "
            "how a researcher could narrow or extend the search. Do not invent studies "
            "not implied by the listed titles; stay grounded in what is shown.\n\n"
            f"Research question:\n{query}\n\nCandidate sources:\n{listed}"
        )
    )
    resp = await llm.ainvoke([msg])
    text = (getattr(resp, "content", None) or "").strip()
    if not text:
        text = "Summary generation returned empty output."
    out: dict[str, Any] = {"summary": text}
    if isinstance(resp, AIMessage):
        out["messages"] = [resp]
    return out
