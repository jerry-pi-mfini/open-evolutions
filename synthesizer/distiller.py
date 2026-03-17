"""
distiller.py — Tiered Knowledge Distillation

Processes contribution data and updates the appropriate level of the
knowledge hierarchy:
  Level 1: Raw logs (contribution_log.json) — already provided by contributor
  Level 2: Lineage wisdom (lineage_learnings.json) — updated here
  Level 3: Master knowledge (learnings.json) — updated by knowledge_manager.py
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def distill_contribution(distilled: dict, lineage: str) -> None:
    """Update lineage-level knowledge from a contribution's distilled data."""
    lineage_dir = PROJECT_ROOT / "lineages" / lineage
    lineage_dir.mkdir(parents=True, exist_ok=True)

    learnings_path = lineage_dir / "lineage_learnings.json"

    # Load existing lineage learnings or initialize
    if learnings_path.exists():
        learnings = json.loads(learnings_path.read_text())
    else:
        learnings = {
            "lineage": lineage,
            "description": "",
            "known_imports": [],
            "heuristics": [],
            "dead_ends": [],
            "contribution_count": 0,
            "total_mutations": 0,
            "total_successes": 0,
        }

    # Update counters
    learnings["contribution_count"] = learnings.get("contribution_count", 0) + 1
    learnings["total_mutations"] = (
        learnings.get("total_mutations", 0) + distilled.get("total_mutations", 0)
    )
    learnings["total_successes"] = (
        learnings.get("total_successes", 0) + distilled.get("successful_compilations", 0)
    )

    # Merge negative constraints as dead ends
    for nc in distilled.get("negative_constraints", []):
        pattern = nc.get("pattern", "")
        if pattern and pattern not in learnings["dead_ends"]:
            learnings["dead_ends"].append(pattern)

    # Track best results
    best_depth = distilled.get("best_lemma_depth", 0)
    prev_best = learnings.get("best_lemma_depth", 0)
    if best_depth > prev_best:
        learnings["best_lemma_depth"] = best_depth

    best_novelty = distilled.get("best_interestingness", 0.0)
    prev_novelty = learnings.get("best_interestingness", 0.0)
    if best_novelty > prev_novelty:
        learnings["best_interestingness"] = best_novelty

    learnings_path.write_text(json.dumps(learnings, indent=2) + "\n")
    print(f"  Updated {learnings_path}")
    print(f"  Lineage totals: {learnings['total_mutations']} mutations, "
          f"{learnings['total_successes']} successes across "
          f"{learnings['contribution_count']} contributions")
