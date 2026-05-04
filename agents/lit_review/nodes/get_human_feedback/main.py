from agents.lit_review.state import AgentState


def get_human_feedback(state: AgentState) -> dict:
    """Optional interactive checkpoint to prune links and capture human notes."""
    papers = list(state.get("papers") or [])
    n = len(papers)
    print(f"Human review — {n} unique paper link(s) after merge.")

    if not papers:
        return {"human_feedback": []}

    print("\nCandidate sources:")
    for idx, paper in enumerate(papers, start=1):
        print(f"{idx}. {paper}")

    print(
        "\nEnter indices to remove (comma-separated), or press Enter to keep all "
        "(example: 2,5,7)."
    )
    raw_remove = input("Remove indices: ").strip()

    to_remove: set[int] = set()
    if raw_remove:
        for token in raw_remove.split(","):
            token = token.strip()
            if not token:
                continue
            if not token.isdigit():
                print(f"Ignoring invalid index token: {token!r}")
                continue
            idx = int(token)
            if idx < 1 or idx > n:
                print(f"Ignoring out-of-range index: {idx}")
                continue
            to_remove.add(idx - 1)

    filtered_papers = [p for i, p in enumerate(papers) if i not in to_remove]
    print(f"Keeping {len(filtered_papers)} of {n} sources.")

    note = input(
        "Optional guidance for summary (themes to emphasize, exclusions, etc.). "
        "Press Enter to skip:\n> "
    ).strip()

    feedback: list[str] = []
    if to_remove:
        removed_count = len(to_remove)
        feedback.append(f"Removed {removed_count} source(s) during human review.")
    if note:
        feedback.append(note)

    return {"papers": filtered_papers, "human_feedback": feedback}
