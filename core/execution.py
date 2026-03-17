"""
execution.py — The Evolution Chamber

Sandboxed execution environment where LLM-proposed Lean 4 code mutations are
compiled, verified, and measured. Supports both local and Docker-based execution.
"""

import json
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
from dataclasses import dataclass, asdict

from core.metrics import evaluate, FitnessScore

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ExecutionResult:
    success: bool
    fitness: FitnessScore
    duration_seconds: float
    lean_file: str
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _run_local(lean_content: str, workdir: Path) -> tuple[str, str, int]:
    """Compile Lean 4 content locally using Lake."""
    lean_file = workdir / "Mutation.lean"
    lean_file.write_text(lean_content)

    result = subprocess.run(
        ["lake", "env", "lean", str(lean_file)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return result.stdout, result.stderr, result.returncode


def _run_docker(lean_content: str, workdir: Path) -> tuple[str, str, int]:
    """Compile Lean 4 content inside a sandboxed Docker container."""
    lean_file = workdir / "Mutation.lean"
    lean_file.write_text(lean_content)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "--network=none",
            "--memory=4g",
            "--cpus=2",
            "-v", f"{workdir}:/workspace:ro",
            "-w", "/workspace",
            "ghcr.io/leanprover/lean4:latest",
            "lean", "Mutation.lean",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return result.stdout, result.stderr, result.returncode


def execute_mutation(
    lean_content: str,
    lineage: str | None = None,
    use_docker: bool = False,
) -> ExecutionResult:
    """
    Execute a Lean 4 code mutation and return its fitness score.

    Args:
        lean_content: The Lean 4 source code to evaluate.
        lineage: Which lineage this mutation belongs to (for interestingness scoring).
        use_docker: If True, run in a sandboxed Docker container.
    """
    workdir = Path(tempfile.mkdtemp(prefix="oe_mutation_"))
    start_time = time.time()

    try:
        runner = _run_docker if use_docker else _run_local
        stdout, stderr, returncode = runner(lean_content, workdir)

        lean_file = workdir / "Mutation.lean"
        lineage_dirs = []
        if lineage:
            lineage_dirs = [str(PROJECT_ROOT / "lineages" / lineage)]
        else:
            lineage_dirs = [
                str(p) for p in (PROJECT_ROOT / "lineages").iterdir() if p.is_dir()
            ]

        fitness = evaluate(lean_file, lineage_dirs)
        duration = time.time() - start_time

        return ExecutionResult(
            success=fitness.passes_floor,
            fitness=fitness,
            duration_seconds=round(duration, 2),
            lean_file=str(lean_file),
            stdout=stdout,
            stderr=stderr,
        )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return ExecutionResult(
            success=False,
            fitness=FitnessScore(
                verification=0, lemma_depth=0, interestingness=0.0,
                error_message="Execution timed out.",
            ),
            duration_seconds=round(duration, 2),
            lean_file=str(workdir / "Mutation.lean"),
            stderr="Execution timed out after 600 seconds.",
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def log_result(result: ExecutionResult, log_path: Path) -> None:
    """Append an execution result to the contribution log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    if log_path.exists():
        entries = json.loads(log_path.read_text())

    entries.append({
        "timestamp": time.time(),
        "success": result.success,
        "fitness": result.fitness.to_dict(),
        "duration_seconds": result.duration_seconds,
        "lean_file": result.lean_file,
    })

    log_path.write_text(json.dumps(entries, indent=2) + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python execution.py <path-to-lean-file>")
        sys.exit(1)

    lean_path = Path(sys.argv[1])
    content = lean_path.read_text()
    result = execute_mutation(content)
    print(json.dumps(result.to_dict(), indent=2))
