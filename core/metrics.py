"""
metrics.py — The Fitness Evaluator

Evaluates Lean 4 proof submissions on three axes:
  V (Verification): Does the code compile without errors?
  D (Lemma Depth):  How many foundational axioms/lemmas does it build upon?
  I (Interestingness): Does it introduce novel approaches not yet in the lineage tree?

Returns a dictionary of numerical scores for the CI pipeline and synthesizer bot.
"""

import json
import subprocess
import re
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class FitnessScore:
    verification: int  # 0 or 1
    lemma_depth: int  # count of dependencies
    interestingness: float  # 0.0 to 1.0
    error_message: str = ""

    @property
    def passes_floor(self) -> bool:
        """A submission must at minimum compile."""
        return self.verification == 1

    def to_dict(self) -> dict:
        return asdict(self)


def check_verification(lean_file: Path) -> tuple[bool, str]:
    """Run `lake build` and check if the Lean 4 file compiles without errors."""
    try:
        result = subprocess.run(
            ["lake", "build"],
            cwd=lean_file.parent,
            capture_output=True,
            text=True,
            timeout=600,
        )
        success = result.returncode == 0
        error = result.stderr if not success else ""
        return success, error
    except FileNotFoundError:
        return False, "Lean 4 / Lake toolchain not found. Run `prepare.py` first."
    except subprocess.TimeoutExpired:
        return False, "Build timed out after 600 seconds."


def check_no_sorry(lean_file: Path) -> tuple[bool, list[str]]:
    """Ensure no `sorry` placeholders remain in the submission."""
    content = lean_file.read_text()
    sorry_matches = [
        f"line {i + 1}" for i, line in enumerate(content.splitlines()) if "sorry" in line
    ]
    return len(sorry_matches) == 0, sorry_matches


def count_lemma_depth(lean_file: Path) -> int:
    """
    Count how many project lemmas and Mathlib theorems this file depends on.
    Heuristic: count `import` statements and `theorem`/`lemma` references.
    """
    content = lean_file.read_text()
    imports = len(re.findall(r"^import\s+", content, re.MULTILINE))
    references = len(re.findall(r"(?:theorem|lemma)\s+\w+", content))
    return imports + references


def compute_interestingness(
    lean_file: Path, existing_lineages: list[str]
) -> float:
    """
    Score novelty based on which Mathlib modules are used.
    If the submission imports modules not seen in any existing lineage, it scores higher.
    """
    content = lean_file.read_text()
    imports = set(re.findall(r"^import\s+(.+)$", content, re.MULTILINE))

    known_imports: set[str] = set()
    for lineage_dir in existing_lineages:
        lineage_path = Path(lineage_dir)
        if lineage_path.exists():
            learnings_file = lineage_path / "lineage_learnings.json"
            if learnings_file.exists():
                data = json.loads(learnings_file.read_text())
                known_imports.update(data.get("known_imports", []))

    if not imports:
        return 0.0

    novel = imports - known_imports
    return len(novel) / len(imports)


def evaluate(lean_file: Path, lineage_dirs: list[str] | None = None) -> FitnessScore:
    """Full evaluation pipeline for a Lean 4 submission."""
    lean_path = Path(lean_file)

    if not lean_path.exists():
        return FitnessScore(
            verification=0, lemma_depth=0, interestingness=0.0,
            error_message=f"File not found: {lean_path}",
        )

    # Check for sorry
    sorry_clean, sorry_locations = check_no_sorry(lean_path)
    if not sorry_clean:
        return FitnessScore(
            verification=0, lemma_depth=0, interestingness=0.0,
            error_message=f"Contains `sorry` at: {', '.join(sorry_locations)}",
        )

    # Check compilation
    compiles, error = check_verification(lean_path)

    # Compute metrics
    depth = count_lemma_depth(lean_path) if compiles else 0
    novelty = (
        compute_interestingness(lean_path, lineage_dirs or []) if compiles else 0.0
    )

    return FitnessScore(
        verification=1 if compiles else 0,
        lemma_depth=depth,
        interestingness=round(novelty, 3),
        error_message=error,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python metrics.py <path-to-lean-file>")
        sys.exit(1)

    target = Path(sys.argv[1])
    lineages = [
        "lineages/analytic-continuation",
        "lineages/computational-bounds",
        "lineages/operator-theory",
    ]
    score = evaluate(target, lineages)
    print(json.dumps(score.to_dict(), indent=2))
