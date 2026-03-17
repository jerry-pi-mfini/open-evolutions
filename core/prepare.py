"""
prepare.py — Environment Setup

Standardizes data, dependencies, and hardware checks across all distributed forks.
Ensures contributors have a consistent Lean 4 + Mathlib environment before running
the evolution loop.
"""

import subprocess
import shutil
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEAN_TOOLCHAIN_FILE = PROJECT_ROOT / "lean-toolchain"
LAKEFILE = PROJECT_ROOT / "lakefile.lean"


def check_command(cmd: str) -> bool:
    """Check if a command-line tool is available."""
    return shutil.which(cmd) is not None


def check_lean_toolchain() -> bool:
    """Verify that Lean 4 and Lake are installed and accessible."""
    if not check_command("lean"):
        print("ERROR: `lean` not found. Install via https://leanprover.github.io/lean4/doc/setup.html")
        return False
    if not check_command("lake"):
        print("ERROR: `lake` not found. It should be bundled with Lean 4.")
        return False

    result = subprocess.run(["lean", "--version"], capture_output=True, text=True)
    print(f"Lean version: {result.stdout.strip()}")
    return True


def check_docker() -> bool:
    """Verify Docker is available for sandboxed execution."""
    if not check_command("docker"):
        print("WARNING: Docker not found. Sandboxed execution will not be available.")
        print("  Install from https://docs.docker.com/get-docker/")
        return False
    print("Docker: available")
    return True


def init_lake_project() -> bool:
    """Initialize or update the Lake project and fetch Mathlib."""
    if not LAKEFILE.exists():
        print("Initializing Lake project...")
        result = subprocess.run(
            ["lake", "init", "OpenEvolutions"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"ERROR: Lake init failed:\n{result.stderr}")
            return False

    print("Fetching dependencies (this may take a while for Mathlib)...")
    result = subprocess.run(
        ["lake", "update"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if result.returncode != 0:
        print(f"ERROR: Lake update failed:\n{result.stderr}")
        return False

    print("Dependencies fetched successfully.")
    return True


def init_knowledge_base() -> None:
    """Ensure the knowledge base files exist with initial structure."""
    knowledge_dir = PROJECT_ROOT / "knowledge"
    knowledge_dir.mkdir(exist_ok=True)

    learnings = knowledge_dir / "learnings.json"
    if not learnings.exists():
        initial = {
            "version": "0.1.0",
            "global_truths": [],
            "negative_constraints": [],
            "positive_heuristics": [],
            "unexplored_frontiers": [],
        }
        learnings.write_text(json.dumps(initial, indent=2) + "\n")
        print("Initialized knowledge/learnings.json")

    evolution = knowledge_dir / "evolution.md"
    if not evolution.exists():
        evolution.write_text(
            "# Evolution Journal\n\n"
            "This document tracks the human-readable narrative of the project's progress.\n\n"
            "---\n\n"
            "*No milestones recorded yet.*\n"
        )
        print("Initialized knowledge/evolution.md")


def init_lineage(name: str, description: str) -> None:
    """Ensure a lineage directory has its learnings file."""
    lineage_dir = PROJECT_ROOT / "lineages" / name
    lineage_dir.mkdir(parents=True, exist_ok=True)

    learnings = lineage_dir / "lineage_learnings.json"
    if not learnings.exists():
        initial = {
            "lineage": name,
            "description": description,
            "known_imports": [],
            "heuristics": [],
            "dead_ends": [],
        }
        learnings.write_text(json.dumps(initial, indent=2) + "\n")
        print(f"Initialized lineage: {name}")


def prepare() -> bool:
    """Run all preparation steps. Returns True if environment is ready."""
    print("=" * 60)
    print("Open Evolutions — Environment Preparation")
    print("=" * 60)

    checks = []

    print("\n[1/4] Checking Lean 4 toolchain...")
    checks.append(check_lean_toolchain())

    print("\n[2/4] Checking Docker...")
    checks.append(check_docker())

    print("\n[3/4] Initializing knowledge base...")
    init_knowledge_base()
    init_lineage("analytic-continuation", "Functional equation and traditional complex analysis")
    init_lineage("computational-bounds", "Zero-free regions through interval arithmetic")
    init_lineage("operator-theory", "Zeros as eigenvalues of operators")

    print("\n[4/4] Setting up Lake project...")
    lean_ok = check_lean_toolchain()
    if lean_ok:
        checks.append(init_lake_project())
    else:
        print("Skipping Lake setup (Lean not installed).")
        checks.append(False)

    print("\n" + "=" * 60)
    if all(checks):
        print("Environment is READY. Run `oe-cli start` to begin evolving.")
    else:
        print("Environment has WARNINGS. Some features may not work.")
        print("You can still proceed with available tools.")
    print("=" * 60)

    return all(checks)


if __name__ == "__main__":
    success = prepare()
    sys.exit(0 if success else 1)
