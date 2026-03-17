"""
pruner.py — Stagnant Lineage Detection & Archival

Identifies lineages that have stopped producing meaningful progress
and recommends them for archival (freezing to /archives).
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# A lineage is considered stagnant if it has had no improvement in this many contributions
STAGNATION_THRESHOLD_CONTRIBUTIONS = 10

# Minimum contributions before a lineage can be pruned (don't kill young lineages)
MIN_AGE_CONTRIBUTIONS = 5


def load_lineages() -> dict[str, dict]:
    """Load all active lineage data."""
    lineages_dir = PROJECT_ROOT / "lineages"
    lineages = {}

    if not lineages_dir.exists():
        return lineages

    for lineage_dir in sorted(lineages_dir.iterdir()):
        if not lineage_dir.is_dir():
            continue
        learnings_path = lineage_dir / "lineage_learnings.json"
        if learnings_path.exists():
            lineages[lineage_dir.name] = json.loads(learnings_path.read_text())

    return lineages


def detect_stagnant(lineages: dict[str, dict]) -> list[dict]:
    """Identify lineages that appear to have stagnated."""
    stagnant = []

    for name, data in lineages.items():
        contribution_count = data.get("contribution_count", 0)

        # Too young to evaluate
        if contribution_count < MIN_AGE_CONTRIBUTIONS:
            continue

        total_mutations = data.get("total_mutations", 0)
        total_successes = data.get("total_successes", 0)
        best_depth = data.get("best_lemma_depth", 0)

        # Success rate across all contributions
        success_rate = total_successes / max(total_mutations, 1)

        # Heuristic: if success rate is very low and lemma depth hasn't grown,
        # the lineage is likely stagnant
        is_stagnant = (
            success_rate < 0.05 and contribution_count >= STAGNATION_THRESHOLD_CONTRIBUTIONS
        ) or (
            best_depth == 0 and contribution_count >= STAGNATION_THRESHOLD_CONTRIBUTIONS
        )

        if is_stagnant:
            stagnant.append({
                "lineage": name,
                "contribution_count": contribution_count,
                "total_mutations": total_mutations,
                "success_rate": round(success_rate, 3),
                "best_lemma_depth": best_depth,
                "reason": "low success rate" if success_rate < 0.05 else "no lemma depth progress",
            })

    return stagnant


def archive_lineage(name: str) -> None:
    """Move a lineage from /lineages to /archives."""
    source = PROJECT_ROOT / "lineages" / name
    dest = PROJECT_ROOT / "archives" / name

    if not source.exists():
        print(f"  Lineage '{name}' not found in lineages/")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Add archival metadata before moving
    learnings_path = source / "lineage_learnings.json"
    if learnings_path.exists():
        data = json.loads(learnings_path.read_text())
        data["archived_at"] = datetime.now(timezone.utc).isoformat()
        data["status"] = "frozen"
        learnings_path.write_text(json.dumps(data, indent=2) + "\n")

    shutil.move(str(source), str(dest))
    print(f"  Archived: lineages/{name} -> archives/{name}")


def check_stagnation() -> None:
    """Check for stagnant lineages and report."""
    lineages = load_lineages()

    if not lineages:
        print("No active lineages found.")
        return

    stagnant = detect_stagnant(lineages)

    if not stagnant:
        print("No stagnant lineages detected.")
        return

    print(f"Found {len(stagnant)} stagnant lineage(s):\n")
    for s in stagnant:
        print(f"  {s['lineage']}")
        print(f"    Contributions: {s['contribution_count']}")
        print(f"    Success rate: {s['success_rate']:.1%}")
        print(f"    Best depth: {s['best_lemma_depth']}")
        print(f"    Reason: {s['reason']}")
        print()

    # Save report
    report_path = PROJECT_ROOT / "knowledge" / "pruning_report.json"
    report_path.write_text(json.dumps(stagnant, indent=2) + "\n")
    print(f"Report saved to: {report_path}")
    print("To archive a lineage, run: python -m synthesizer.pruner --archive <name>")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lineage Pruner")
    parser.add_argument("--check", action="store_true", help="Check for stagnant lineages")
    parser.add_argument("--archive", type=str, help="Archive a specific lineage")
    args = parser.parse_args()

    if args.archive:
        archive_lineage(args.archive)
    elif args.check:
        check_stagnation()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
