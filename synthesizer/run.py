"""
run.py — Grand Synthesizer Entry Point

Orchestrates the post-merge synthesis pipeline:
1. Classify the contribution (lineage detection, novelty check)
2. Distill learnings into the lineage knowledge base
3. Update the master knowledge base
4. Update the human-readable evolution journal
"""

import argparse
import json
from pathlib import Path

from synthesizer.distiller import distill_contribution
from synthesizer.novelty import classify_contribution, NoveltyResult
from synthesizer.knowledge_manager import update_master_learnings, update_evolution_journal

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run(pr_number: str, lineage: str, author: str) -> None:
    """Execute the full synthesis pipeline for a merged PR."""
    print(f"Grand Synthesizer: processing PR #{pr_number} by {author}")
    print(f"  Lineage: {lineage}")

    # Load the contribution's distilled data
    distilled_path = PROJECT_ROOT / "contribution_distilled.json"
    if not distilled_path.exists():
        print("WARNING: No contribution_distilled.json found. Skipping synthesis.")
        return

    distilled = json.loads(distilled_path.read_text())

    # 1. Classify novelty
    print("\n[1/4] Classifying contribution...")
    novelty = classify_contribution(distilled, lineage)
    print(f"  Novelty score: {novelty.score:.3f}")
    print(f"  Classification: {novelty.classification}")
    if novelty.should_spawn_lineage:
        print(f"  ** New lineage recommended: {novelty.suggested_lineage_name}")

    # 2. Distill into lineage knowledge
    print("\n[2/4] Distilling into lineage knowledge...")
    distill_contribution(distilled, lineage)

    # 3. Update master knowledge base
    print("\n[3/4] Updating master knowledge base...")
    update_master_learnings(distilled, novelty)

    # 4. Update evolution journal
    print("\n[4/4] Updating evolution journal...")
    update_evolution_journal(
        pr_number=pr_number,
        author=author,
        lineage=lineage,
        distilled=distilled,
        novelty=novelty,
    )

    print("\nSynthesis complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Grand Synthesizer")
    parser.add_argument("--pr", required=True, help="PR number")
    parser.add_argument("--lineage", required=True, help="Lineage name")
    parser.add_argument("--author", required=True, help="PR author")
    args = parser.parse_args()

    run(pr_number=args.pr, lineage=args.lineage, author=args.author)


if __name__ == "__main__":
    main()
