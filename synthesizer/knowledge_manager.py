"""
knowledge_manager.py — Master Knowledge Base Management

Handles updates to the top-level knowledge artifacts:
  - knowledge/learnings.json (machine-readable "Brain")
  - knowledge/evolution.md (human-readable "Journal")

Applies epistemic labeling: Positive Heuristic, Negative Constraint,
or Unexplored Frontier.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from synthesizer.novelty import NoveltyResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _next_id(prefix: str, existing: list[dict]) -> str:
    """Generate the next sequential ID for a knowledge entry."""
    max_num = 0
    for entry in existing:
        eid = entry.get("id", "")
        if eid.startswith(prefix):
            try:
                num = int(eid.split("-")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                pass
    return f"{prefix}{max_num + 1:03d}"


def update_master_learnings(distilled: dict, novelty: NoveltyResult) -> None:
    """Update the master learnings.json with findings from a contribution."""
    learnings_path = PROJECT_ROOT / "knowledge" / "learnings.json"

    if learnings_path.exists():
        learnings = json.loads(learnings_path.read_text())
    else:
        learnings = {
            "version": "0.1.0",
            "challenge": "RZCS",
            "global_truths": [],
            "negative_constraints": [],
            "positive_heuristics": [],
            "unexplored_frontiers": [],
        }

    # Add negative constraints from the contribution
    for nc in distilled.get("negative_constraints", []):
        pattern = nc.get("pattern", "")
        # Deduplicate
        existing_patterns = {
            c.get("finding", "") for c in learnings["negative_constraints"]
        }
        if pattern and pattern not in existing_patterns:
            new_id = _next_id("nc-", learnings["negative_constraints"])
            learnings["negative_constraints"].append({
                "id": new_id,
                "finding": pattern,
                "source": f"contribution (lineage: {distilled.get('lineage', 'unknown')})",
                "confidence": "medium",
            })

    # If the contribution is novel, record it as a positive heuristic
    if novelty.classification in ("novel", "superior") and distilled.get("best_lemma_depth", 0) > 0:
        new_id = _next_id("ph-", learnings["positive_heuristics"])
        learnings["positive_heuristics"].append({
            "id": new_id,
            "finding": novelty.reasoning,
            "confidence": "medium" if novelty.classification == "novel" else "high",
        })

    # If a new lineage is spawned, add it to unexplored frontiers
    if novelty.should_spawn_lineage and novelty.suggested_lineage_name:
        new_id = _next_id("uf-", learnings["unexplored_frontiers"])
        learnings["unexplored_frontiers"].append({
            "id": new_id,
            "description": f"New lineage: {novelty.suggested_lineage_name}",
            "rationale": novelty.reasoning,
        })

    learnings_path.write_text(json.dumps(learnings, indent=2) + "\n")
    print(f"  Updated {learnings_path}")


def update_evolution_journal(
    pr_number: str,
    author: str,
    lineage: str,
    distilled: dict,
    novelty: NoveltyResult,
) -> None:
    """Append a milestone entry to the evolution journal."""
    journal_path = PROJECT_ROOT / "knowledge" / "evolution.md"

    if not journal_path.exists():
        journal_path.write_text("# Evolution Journal\n\n---\n\n")

    content = journal_path.read_text()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build the journal entry
    entry_parts = [
        f"\n### PR #{pr_number} — {timestamp}",
        f"**Author:** {author}  ",
        f"**Lineage:** {lineage}  ",
        f"**Classification:** {novelty.classification}  ",
        f"**Novelty Score:** {novelty.score:.3f}  ",
        "",
        f"**Results:** {distilled.get('successful_compilations', 0)}/{distilled.get('total_mutations', 0)} "
        f"mutations compiled  ",
        f"**Best Lemma Depth:** {distilled.get('best_lemma_depth', 0)}  ",
        f"**Best Interestingness:** {distilled.get('best_interestingness', 0.0):.3f}  ",
        "",
        f"> {novelty.reasoning}",
        "",
        "---",
    ]
    entry = "\n".join(entry_parts)

    # Insert before the final "---" or append at end
    if content.rstrip().endswith("---"):
        content = content.rstrip()[:-3] + entry + "\n"
    else:
        content += "\n" + entry + "\n"

    journal_path.write_text(content)
    print(f"  Updated {journal_path}")
