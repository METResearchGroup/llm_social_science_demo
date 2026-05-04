import logging

from agents.lit_review.nodes.constants import (
    DIVERSIFY_TEMPERATURE,
    LLM_MODEL,
    NUM_DIVERSIFIED_QUERIES,
)
from agents.lit_review.nodes.diversify_queries.helper import (
    coerce_structured_queries,
    normalize_diversified_queries,
    parse_fallback_queries,
)
from agents.lit_review.state import AgentState

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class DiversifiedQueries(BaseModel):
    """Diverse search formulations for literature discovery."""

    queries: list[str] = Field(
        ...,
        description=(
            f"{NUM_DIVERSIFIED_QUERIES} distinct web search queries "
            "(different angles, terms, methods)."
        ),
    )

    @field_validator("queries")
    @classmethod
    def exactly_n_non_empty(cls, v: list[str]) -> list[str]:
        cleaned = [q.strip() for q in v if q and str(q).strip()]
        n = NUM_DIVERSIFIED_QUERIES
        if len(cleaned) != n:
            raise ValueError(f"Expected exactly {n} non-empty queries, got {len(cleaned)}.")
        return cleaned


async def diversify_queries(state: AgentState) -> dict:
    """Rewrite the user query into diverse search strings for broader recall."""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=DIVERSIFY_TEMPERATURE)
    structured = llm.with_structured_output(DiversifiedQueries)
    base = state["query"]
    n = NUM_DIVERSIFIED_QUERIES
    msg = HumanMessage(
        content=(
            "You help social-science / interdisciplinary researchers find literature. "
            f"Given the research question below, output exactly {n} distinct web search "
            "queries a researcher could run (different synonyms, mechanisms, populations, "
            "methods, or adjacent concepts). Each query should be short (under ~200 chars), "
            "specific, and not a duplicate of the others.\n\n"
            f"Research question:\n{base}"
        )
    )
    try:
        raw = await structured.ainvoke([msg])
        queries = coerce_structured_queries(raw)
    except Exception as exc:
        logger.warning("Structured diversify output failed; using fallback parsing: %s", exc)
        fallback = await llm.ainvoke(
            [
                HumanMessage(
                    content=(
                        f"Generate exactly {n} distinct web search queries for this research question.\n"
                        "Return ONLY a JSON object with key 'queries' and a list of strings.\n\n"
                        f"Research question:\n{base}"
                    )
                )
            ]
        )
        queries = parse_fallback_queries(str(getattr(fallback, "content", None) or ""))

    normalized = normalize_diversified_queries(queries, n)
    if len(normalized) != n:
        raise ValueError(
            f"Expected {n} diversified queries, got {len(normalized)} after normalization."
        )
    return {"search_queries": normalized, "messages": [msg]}
