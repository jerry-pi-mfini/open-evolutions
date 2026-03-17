"""
hybridizer.py — Cross-Lineage Convergence Detection

Detects when two lineages are evolving toward similar approaches and
issues "Hybridization Challenges" to the community to merge them.
"""

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# If two lineages share more than this fraction of imports, flag for hybridization
OVERLAP_THRESHOLD = 0.6

# Minimum number of contributions before a lineage is eligible for comparison
MIN_CONTRIBUTIONS = 3


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


def compute_overlap(imports_a: set[str], imports_b: set[str]) -> float:
    """Compute Jaccard similarity between two sets of imports."""
    if not imports_a and not imports_b:
        return 0.0
    intersection = imports_a & imports_b
    union = imports_a | imports_b
    return len(intersection) / len(union)


def compute_dead_end_overlap(dead_ends_a: list[str], dead_ends_b: list[str]) -> float:
    """Compute overlap in discovered dead ends between lineages."""
    set_a = set(dead_ends_a)
    set_b = set(dead_ends_b)
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def find_hybridization_candidates(lineages: dict[str, dict]) -> list[dict]:
    """Find pairs of lineages that may benefit from hybridization."""
    candidates = []
    names = list(lineages.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a_name, b_name = names[i], names[j]
            a_data, b_data = lineages[a_name], lineages[b_name]

            # Skip lineages with too few contributions
            if (a_data.get("contribution_count", 0) < MIN_CONTRIBUTIONS or
                    b_data.get("contribution_count", 0) < MIN_CONTRIBUTIONS):
                continue

            a_imports = set(a_data.get("known_imports", []))
            b_imports = set(b_data.get("known_imports", []))

            import_overlap = compute_overlap(a_imports, b_imports)
            dead_end_overlap = compute_dead_end_overlap(
                a_data.get("dead_ends", []),
                b_data.get("dead_ends", []),
            )

            # Composite convergence score
            convergence = import_overlap * 0.6 + dead_end_overlap * 0.4

            if convergence >= OVERLAP_THRESHOLD:
                candidates.append({
                    "lineage_a": a_name,
                    "lineage_b": b_name,
                    "import_overlap": round(import_overlap, 3),
                    "dead_end_overlap": round(dead_end_overlap, 3),
                    "convergence_score": round(convergence, 3),
                })

    return candidates


def check_hybridization() -> None:
    """Check for hybridization opportunities and report."""
    lineages = load_lineages()

    if len(lineages) < 2:
        print("Not enough active lineages for hybridization analysis.")
        return

    candidates = find_hybridization_candidates(lineages)

    if not candidates:
        print("No hybridization candidates detected.")
        return

    print(f"Found {len(candidates)} hybridization candidate(s):\n")
    for c in candidates:
        print(f"  {c['lineage_a']} <-> {c['lineage_b']}")
        print(f"    Convergence: {c['convergence_score']:.3f}")
        print(f"    Import overlap: {c['import_overlap']:.3f}")
        print(f"    Dead end overlap: {c['dead_end_overlap']:.3f}")
        print()

    # Save report for the CI workflow to pick up
    report_path = PROJECT_ROOT / "knowledge" / "hybridization_report.json"
    report_path.write_text(json.dumps(candidates, indent=2) + "\n")
    print(f"Report saved to: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybridization Detector")
    parser.add_argument("--check", action="store_true", help="Run hybridization check")
    args = parser.parse_args()

    if args.check:
        check_hybridization()


if __name__ == "__main__":
    main()
