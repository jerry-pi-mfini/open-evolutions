"""
evolve.py — The Autonomous Evolution Loop

Implements the Karpathy-style experiment cycle where an LLM agent:
1. Reads the knowledge base (master learnings + lineage wisdom)
2. Proposes a Lean 4 code mutation
3. Executes it in the sandbox
4. Records results to the contribution log
5. Synthesizes learnings from the session
"""

import json
import time
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from core.execution import execute_mutation, log_result

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_knowledge(challenge: str, lineage: str | None) -> dict:
    """Load the master knowledge base and optionally lineage-specific wisdom."""
    knowledge = {}

    # Master learnings
    master_path = PROJECT_ROOT / "knowledge" / "learnings.json"
    if master_path.exists():
        knowledge["master"] = json.loads(master_path.read_text())

    # Task definition
    task_path = PROJECT_ROOT / "core" / "task_definition.md"
    if task_path.exists():
        knowledge["task"] = task_path.read_text()

    # Lineage-specific wisdom
    if lineage:
        lineage_path = PROJECT_ROOT / "lineages" / lineage / "lineage_learnings.json"
        if lineage_path.exists():
            knowledge["lineage"] = json.loads(lineage_path.read_text())

    return knowledge


def build_agent_prompt(knowledge: dict, cycle: int, previous_results: list) -> str:
    """Construct the prompt for the LLM agent based on accumulated knowledge."""
    parts = []

    parts.append("You are an AI research agent working on the Open Evolutions project.")
    parts.append("Your task is to propose a Lean 4 code mutation that advances the proof.")
    parts.append("")

    if "task" in knowledge:
        parts.append("## Task Definition")
        parts.append(knowledge["task"])
        parts.append("")

    if "master" in knowledge:
        master = knowledge["master"]
        if master.get("negative_constraints"):
            parts.append("## Known Dead Ends (DO NOT repeat these)")
            for nc in master["negative_constraints"]:
                parts.append(f"- {nc['finding']}")
            parts.append("")

        if master.get("positive_heuristics"):
            parts.append("## Positive Heuristics (use these)")
            for ph in master["positive_heuristics"]:
                parts.append(f"- {ph['finding']}")
            parts.append("")

    if "lineage" in knowledge:
        lineage = knowledge["lineage"]
        parts.append(f"## Lineage: {lineage['lineage']}")
        parts.append(f"Description: {lineage['description']}")
        if lineage.get("heuristics"):
            parts.append("Lineage heuristics:")
            for h in lineage["heuristics"]:
                parts.append(f"  - {h}")
        if lineage.get("dead_ends"):
            parts.append("Lineage dead ends:")
            for d in lineage["dead_ends"]:
                parts.append(f"  - {d}")
        parts.append("")

    if previous_results:
        parts.append("## Previous Attempts This Session")
        for i, r in enumerate(previous_results[-5:]):  # last 5 results
            status = "COMPILED" if r["success"] else "FAILED"
            parts.append(f"  Attempt {i + 1}: {status} — {r.get('error', 'OK')}")
        parts.append("")

    parts.append(f"## Cycle {cycle}")
    parts.append("Propose a Lean 4 code block that advances the proof.")
    parts.append("Output ONLY the Lean 4 code, enclosed in ```lean4 ... ``` markers.")

    return "\n".join(parts)


def call_agent(prompt: str) -> str | None:
    """Call the LLM agent to propose a mutation. Returns Lean 4 code or None."""
    try:
        import anthropic
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] `anthropic` package not installed. "
            "Run `pip install anthropic`."
        )
        return None

    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError:
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY not set or invalid. "
            "Export your API key: `export ANTHROPIC_API_KEY=sk-...`"
        )
        return None

    text = response.content[0].text

    # Extract Lean 4 code block
    if "```lean4" in text:
        start = text.index("```lean4") + len("```lean4")
        end = text.index("```", start)
        return text[start:end].strip()
    elif "```lean" in text:
        start = text.index("```lean") + len("```lean")
        end = text.index("```", start)
        return text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        # Skip optional language tag on the same line
        newline = text.index("\n", start)
        start = newline + 1
        end = text.index("```", start)
        return text[start:end].strip()

    return text.strip()


def synthesize_session(results: list, log_path: Path) -> None:
    """Produce a summary of the session's findings."""
    total = len(results)
    successes = sum(1 for r in results if r["success"])

    summary = {
        "session_summary": {
            "total_mutations": total,
            "successful_compilations": successes,
            "success_rate": round(successes / total, 3) if total > 0 else 0.0,
        },
        "key_findings": [],
    }

    # Extract notable results
    for r in results:
        if r["success"] and r["fitness"]["lemma_depth"] > 0:
            summary["key_findings"].append({
                "type": "positive",
                "lemma_depth": r["fitness"]["lemma_depth"],
                "interestingness": r["fitness"]["interestingness"],
            })

    synthesis_path = log_path.parent / "session_synthesis.json"
    synthesis_path.write_text(json.dumps(summary, indent=2) + "\n")
    console.print(f"Session synthesis saved to: {synthesis_path}")


def run_evolution_loop(
    challenge: str,
    lineage: str | None,
    num_cycles: int,
    cycle_minutes: int,
    use_docker: bool,
) -> None:
    """Main evolution loop: propose mutations, execute, record, learn."""
    knowledge = load_knowledge(challenge, lineage)

    if not knowledge.get("task"):
        console.print("[bold red]Error:[/bold red] No task_definition.md found in core/.")
        return

    log_path = PROJECT_ROOT / "contribution_log.json"
    results: list[dict] = []

    console.print(f"[dim]Loaded knowledge base with {len(knowledge)} components.[/dim]")
    console.print(f"[dim]Running {num_cycles} cycles, max {cycle_minutes} min each.[/dim]\n")

    for cycle in range(1, num_cycles + 1):
        cycle_start = time.time()
        console.rule(f"[bold]Cycle {cycle}/{num_cycles}[/bold]")

        # 1. Build prompt from accumulated knowledge
        prompt = build_agent_prompt(knowledge, cycle, results)

        # 2. Call LLM agent
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Agent is thinking...", total=None)
            lean_code = call_agent(prompt)

        if lean_code is None:
            console.print("[yellow]Agent returned no code. Skipping cycle.[/yellow]")
            continue

        console.print(f"[dim]Received {len(lean_code)} chars of Lean 4 code.[/dim]")

        # 3. Execute mutation
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Compiling mutation...", total=None)
            exec_result = execute_mutation(lean_code, lineage=lineage, use_docker=use_docker)

        # 4. Record result
        log_result(exec_result, log_path)
        result_dict = {
            "cycle": cycle,
            "success": exec_result.success,
            "fitness": exec_result.fitness.to_dict(),
            "duration": exec_result.duration_seconds,
            "error": exec_result.fitness.error_message,
        }
        results.append(result_dict)

        # 5. Display result
        table = Table(title=f"Cycle {cycle} Result")
        table.add_column("Metric", style="bold")
        table.add_column("Value")
        table.add_row("Verification", "[green]PASS[/green]" if exec_result.success else "[red]FAIL[/red]")
        table.add_row("Lemma Depth", str(exec_result.fitness.lemma_depth))
        table.add_row("Interestingness", str(exec_result.fitness.interestingness))
        table.add_row("Duration", f"{exec_result.duration_seconds}s")
        if exec_result.fitness.error_message:
            table.add_row("Error", exec_result.fitness.error_message[:200])
        console.print(table)

        # Check cycle time limit
        elapsed = time.time() - cycle_start
        if elapsed > cycle_minutes * 60:
            console.print(f"[yellow]Cycle exceeded {cycle_minutes}min limit.[/yellow]")

    # Post-loop synthesis
    console.rule("[bold]Session Complete[/bold]")
    if results:
        synthesize_session(results, log_path)

    total = len(results)
    successes = sum(1 for r in results if r["success"])
    console.print(f"Completed {total} cycles: {successes} compiled, {total - successes} failed.")
    console.print("Run `oe-cli submit` to package your results for PR submission.")
