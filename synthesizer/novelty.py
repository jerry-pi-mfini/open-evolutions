"""
novelty.py — Novelty Detection & Lineage Classification

Determines whether a contribution:
  - Is a straightforward improvement within its lineage ("Superior")
  - Introduces a significantly novel approach ("Predictive Surprise")
  - Should spawn a new lineage branch
"""

import json
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Threshold above which a contribution is considered "significantly novel"
NOVELTY_THRESHOLD = 0.4

# Minimum interestingness to recommend spawning a new lineage
SPAWN_THRESHOLD = 0.7


@dataclass
class NoveltyResult:
    score: float  # 0.0 to 1.0
    classification: str  # "superior", "novel", "incremental"
    should_spawn_lineage: bool
    suggested_lineage_name: str | None
    reasoning: str


def _load_all_lineage_imports() -> dict[str, set[str]]:
    """Load known imports from all existing lineages."""
    lineages_dir = PROJECT_ROOT / "lineages"
    result = {}

    if not lineages_dir.exists():
        return result

    for lineage_dir in lineages_dir.iterdir():
        if not lineage_dir.is_dir():
            continue
        learnings_path = lineage_dir / "lineage_learnings.json"
        if learnings_path.exists():
            data = json.loads(learnings_path.read_text())
            result[lineage_dir.name] = set(data.get("known_imports", []))

    return result


def classify_contribution(distilled: dict, claimed_lineage: str) -> NoveltyResult:
    """
    Classify a contribution based on its novelty relative to existing lineages.

    Uses interestingness score from the distilled data and compares against
    the existing lineage landscape to determine classification.
    """
    interestingness = distilled.get("best_interestingness", 0.0)
    lemma_depth = distilled.get("best_lemma_depth", 0)
    success_rate = (
        distilled.get("successful_compilations", 0) / max(distilled.get("total_mutations", 1), 1)
    )

    # Load existing lineage data for comparison
    all_imports = _load_all_lineage_imports()
    claimed_imports = all_imports.get(claimed_lineage, set())

    # Compute composite novelty score
    # Weight: interestingness (50%), depth improvement potential (30%), new approach (20%)
    lineage_path = PROJECT_ROOT / "lineages" / claimed_lineage / "lineage_learnings.json"
    prev_best_depth = 0
    if lineage_path.exists():
        prev_data = json.loads(lineage_path.read_text())
        prev_best_depth = prev_data.get("best_lemma_depth", 0)

    depth_improvement = max(0, lemma_depth - prev_best_depth) / max(lemma_depth, 1)

    novelty_score = (
        interestingness * 0.5
        + depth_improvement * 0.3
        + (0.2 if success_rate > 0.3 else 0.0)
    )
    novelty_score = min(novelty_score, 1.0)

    # Classify
    if novelty_score >= SPAWN_THRESHOLD:
        classification = "novel"
        should_spawn = True
        # Generate a lineage name suggestion based on the approach
        suggested_name = f"{claimed_lineage}-variant-{int(novelty_score * 100)}"
        reasoning = (
            f"High novelty score ({novelty_score:.3f}) indicates a significantly "
            f"different approach. Recommend spawning a new lineage."
        )
    elif novelty_score >= NOVELTY_THRESHOLD:
        classification = "novel"
        should_spawn = False
        suggested_name = None
        reasoning = (
            f"Moderate novelty ({novelty_score:.3f}) — introduces new ideas within "
            f"the existing lineage framework."
        )
    elif lemma_depth > prev_best_depth:
        classification = "superior"
        should_spawn = False
        suggested_name = None
        reasoning = (
            f"Advances lemma depth from {prev_best_depth} to {lemma_depth} within "
            f"lineage '{claimed_lineage}'."
        )
    else:
        classification = "incremental"
        should_spawn = False
        suggested_name = None
        reasoning = (
            f"Incremental contribution to lineage '{claimed_lineage}'. "
            f"Novelty score: {novelty_score:.3f}."
        )

    return NoveltyResult(
        score=novelty_score,
        classification=classification,
        should_spawn_lineage=should_spawn,
        suggested_lineage_name=suggested_name,
        reasoning=reasoning,
    )
