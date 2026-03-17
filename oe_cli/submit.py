"""
submit.py — PR Submission Preparation

Packages the contributor's work (code mutations, contribution logs, distilled
learnings) into a Git branch ready for pull request submission.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

from rich.console import Console

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_git(*args: str) -> tuple[str, int]:
    """Run a git command and return (output, returncode)."""
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return (result.stdout + result.stderr).strip(), result.returncode


def validate_submission(lineage: str) -> list[str]:
    """Check that the submission meets minimum requirements."""
    issues = []

    # Check contribution log exists
    log_path = PROJECT_ROOT / "contribution_log.json"
    if not log_path.exists():
        issues.append("No contribution_log.json found. Run `oe-cli start` first.")
        return issues

    entries = json.loads(log_path.read_text())
    if not entries:
        issues.append("contribution_log.json is empty. No mutations were recorded.")
        return issues

    # Check at least one successful compilation
    successes = [e for e in entries if e.get("success")]
    if not successes:
        issues.append("No successful compilations found. A submission must have at least one passing mutation.")

    # Check lineage exists
    lineage_dir = PROJECT_ROOT / "lineages" / lineage
    if not lineage_dir.exists():
        issues.append(f"Lineage '{lineage}' not found in lineages/ directory.")

    return issues


def distill_learnings(lineage: str) -> dict:
    """Synthesize contribution logs into distilled learnings for the PR."""
    log_path = PROJECT_ROOT / "contribution_log.json"
    entries = json.loads(log_path.read_text())

    successes = [e for e in entries if e.get("success")]
    failures = [e for e in entries if not e.get("success")]

    # Extract patterns from failures (negative constraints)
    negative_constraints = []
    error_counts: dict[str, int] = {}
    for f in failures:
        error = f.get("fitness", {}).get("error_message", "unknown")
        # Truncate long errors to a signature
        signature = error[:100]
        error_counts[signature] = error_counts.get(signature, 0) + 1

    for error, count in error_counts.items():
        if count >= 2:  # Only report repeated errors
            negative_constraints.append({
                "pattern": error,
                "occurrences": count,
            })

    # Best results
    best_depth = max(
        (e.get("fitness", {}).get("lemma_depth", 0) for e in successes), default=0
    )
    best_novelty = max(
        (e.get("fitness", {}).get("interestingness", 0.0) for e in successes), default=0.0
    )

    return {
        "lineage": lineage,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_mutations": len(entries),
        "successful_compilations": len(successes),
        "best_lemma_depth": best_depth,
        "best_interestingness": best_novelty,
        "negative_constraints": negative_constraints,
    }


def prepare_submission(lineage: str, message: str | None = None) -> None:
    """Create a submission branch with all required artifacts."""
    # Validate
    issues = validate_submission(lineage)
    if issues:
        console.print("[bold red]Submission validation failed:[/bold red]")
        for issue in issues:
            console.print(f"  - {issue}")
        return

    # Distill learnings
    console.print("Distilling session learnings...")
    distilled = distill_learnings(lineage)
    distilled_path = PROJECT_ROOT / "contribution_distilled.json"
    distilled_path.write_text(json.dumps(distilled, indent=2) + "\n")

    # Create branch
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch_name = f"submission/{lineage}/{timestamp}"

    console.print(f"Creating branch: [bold]{branch_name}[/bold]")
    output, rc = _run_git("checkout", "-b", branch_name)
    if rc != 0:
        console.print(f"[bold red]Git error:[/bold red] {output}")
        return

    # Stage files
    files_to_add = [
        "contribution_log.json",
        "contribution_distilled.json",
    ]

    # Add session synthesis if it exists
    synthesis = PROJECT_ROOT / "session_synthesis.json"
    if synthesis.exists():
        files_to_add.append("session_synthesis.json")

    for f in files_to_add:
        _run_git("add", f)

    # Also stage any new/modified Lean files in the lineage directory
    _run_git("add", f"lineages/{lineage}/")

    # Commit
    commit_msg = message or f"submission: {lineage} — {distilled['successful_compilations']}/{distilled['total_mutations']} mutations compiled"
    output, rc = _run_git("commit", "-m", commit_msg)
    if rc != 0:
        console.print(f"[bold red]Commit failed:[/bold red] {output}")
        return

    console.print(f"\n[bold green]Submission ready![/bold green]")
    console.print(f"Branch: {branch_name}")
    console.print(f"Compiled: {distilled['successful_compilations']}/{distilled['total_mutations']}")
    console.print(f"Best lemma depth: {distilled['best_lemma_depth']}")
    console.print(f"Best interestingness: {distilled['best_interestingness']}")
    console.print(f"\nPush with: [bold]git push origin {branch_name}[/bold]")
    console.print("Then open a Pull Request on GitHub.")
