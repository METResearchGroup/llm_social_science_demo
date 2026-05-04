import json
from typing import Any


def normalize_diversified_queries(candidates: list[str], n: int) -> list[str]:
    """Clean, dedupe, and cap candidate queries to exactly ``n`` when possible."""
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        q = str(raw or "").strip()
        if not q:
            continue
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(q)
    return cleaned[:n]


def parse_fallback_queries(raw_text: str) -> list[str]:
    text = (raw_text or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return list(parsed.get("queries") or [])
        if isinstance(parsed, list):
            return list(parsed)
    except json.JSONDecodeError:
        pass
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip()]


def coerce_structured_queries(raw: Any) -> list[str]:
    if isinstance(raw, dict):
        return list(raw.get("queries") or [])
    queries = getattr(raw, "queries", None)
    if isinstance(queries, list):
        return list(queries)
    return []
