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
    parts.append("Your goal is to build toward a formal proof of the Narrowing Lemma for the")
    parts.append("Riemann Zeta function: that no zeros exist within distance ε of the lines")
    parts.append("Re(s)=0 and Re(s)=1 in the critical strip.")
    parts.append("")
    parts.append("## Instructions")
    parts.append("")
    parts.append("Below is a SCAFFOLD that already compiles. You MUST output it exactly as-is,")
    parts.append("then ADD new theorems after the `-- ADD THEOREMS BELOW` marker.")
    parts.append("")
    parts.append("Your added theorems should build toward the Narrowing Lemma.")
    parts.append("")
    parts.append("CRITICAL: Use `sorry` for ANY proof that is not trivially one-line.")
    parts.append("Your job is to lay out the PROOF ARCHITECTURE — the chain of theorem")
    parts.append("statements from foundations to the Narrowing Lemma. Proving them comes later.")
    parts.append("A file with 8 theorem statements using sorry is MUCH more valuable than")
    parts.append("a file that tries to prove one hard theorem and fails to compile.")
    parts.append("")
    parts.append("Only prove a step WITHOUT sorry if it is genuinely simple, like:")
    parts.append("  `constructor <;> linarith [h.1, h.2]` or `exact h.1` or `simp`")
    parts.append("If a tactic doesn't immediately work, replace the ENTIRE proof body with sorry.")
    parts.append("")
    parts.append("Key rules for your added code:")
    parts.append("- Apply functions: `riemannZeta s` not `riemannZeta`")
    parts.append("- Use `noncomputable` for defs involving `Complex.exp`, `Complex.log`, etc.")
    parts.append("- `Complex.pi` doesn't exist — use `↑Real.pi`; for norm use `‖s‖`")
    parts.append("- Do NOT add new imports. The scaffold imports are sufficient.")
    parts.append("")
    parts.append("## Quick Reference: Complex Number Operations")
    parts.append("- Absolute value / modulus: `‖z‖` (norm notation), NOT `Complex.abs z`")
    parts.append("- Conjugate: `starRingEnd ℂ z`, NOT `Complex.conj z`")
    parts.append("- Pi: `↑Real.pi` or `(Real.pi : ℝ)`, NOT `Complex.pi`")
    parts.append("- Real/imaginary parts: `z.re`, `z.im`")
    parts.append("")
    parts.append("## Scaffold (output this EXACTLY, then add theorems at the bottom)")
    parts.append("")
    parts.append("```lean4")
    parts.append("import Mathlib.Data.Complex.Basic")
    parts.append("import Mathlib.Data.Real.Basic")
    parts.append("import Mathlib.Analysis.SpecialFunctions.Complex.Log")
    parts.append("import Mathlib.Tactic")
    parts.append("")
    parts.append("-- Core definitions")
    parts.append("def CriticalStrip (s : ℂ) : Prop := 0 < s.re ∧ s.re < 1")
    parts.append("def EpsilonInterior (s : ℂ) (ε : ℝ) : Prop := ε < s.re ∧ s.re < 1 - ε")
    parts.append("")
    parts.append("-- Zeta and Xi (placeholders)")
    parts.append("noncomputable def riemannZeta : ℂ → ℂ := sorry")
    parts.append("noncomputable def xi (s : ℂ) : ℂ :=")
    parts.append("  s * (s - 1) * Complex.exp (-s / 2 * Complex.log s) * riemannZeta s")
    parts.append("")
    parts.append("-- Definitions that depend on riemannZeta (MUST come after it)")
    parts.append("def ZeroFreeRegion (P : ℂ → Prop) : Prop := ∀ s, P s → riemannZeta s ≠ 0")
    parts.append("")
    parts.append("-- Known results as axioms")
    parts.append("axiom zeta_nonzero_re_one (t : ℝ) (ht : t ≠ 0) :")
    parts.append("    riemannZeta (1 + t * Complex.I) ≠ 0")
    parts.append("axiom xi_symmetry (s : ℂ) : xi s = xi (1 - s)")
    parts.append("axiom zeta_meromorphic (s : ℂ) (hs : s ≠ 1) : Differentiable ℂ riemannZeta")
    parts.append("")
    parts.append("-- Foundation (proved)")
    parts.append("theorem eps_interior_in_strip (s : ℂ) (ε : ℝ) (hε : ε > 0)")
    parts.append("    (h : EpsilonInterior s ε) : CriticalStrip s := by")
    parts.append("  constructor <;> linarith [h.1, h.2]")
    parts.append("")
    parts.append("-- ADD THEOREMS BELOW --")
    parts.append("```")
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
        parts.append("Study these errors carefully and do NOT repeat the same mistakes:")
        parts.append("")
        for i, r in enumerate(previous_results[-5:]):  # last 5 results
            status = "COMPILED" if r["success"] else "FAILED"
            error = r.get("error", "OK")
            parts.append(f"### Attempt {i + 1}: {status}")
            if error and error != "OK":
                # Show enough error context to learn from
                parts.append(f"```")
                parts.append(error[:500])
                parts.append(f"```")
            parts.append("")

    parts.append(f"## Cycle {cycle}")
    parts.append("Propose a Lean 4 file that advances the proof tree toward the Narrowing Lemma.")
    parts.append("If previous attempts failed, fix the specific errors shown above.")
    parts.append("If previous attempts succeeded with basic lemmas, build deeper — define the")
    parts.append("Xi function, prove symmetry properties, establish zero-free region structure.")
    parts.append("Use `sorry` freely for steps you can't complete, so you can lay out the full")
    parts.append("proof architecture.")
    parts.append("")
    parts.append("Output ONLY the Lean 4 code, enclosed in ```lean4 ... ``` markers.")

    return "\n".join(parts)


import re as _re

# Known bad identifiers → suggested replacements
KNOWN_BAD_IDENTIFIERS = {
    "Complex.abs": "‖·‖ (norm) or Complex.normSq",
    "Complex.pi": "↑Real.pi or (Real.pi : ℝ)",
    "Complex.conj": "starRingEnd ℂ · or conj",
    "Complex.gamma": "sorry (no Gamma in cached Mathlib)",
    "Real.abs": "|·| or abs",
    "min_pos": "lt_min or min_le_left/min_le_right",
    "min_pos_iff": "lt_min_iff",
}


def lint_lean_code(code: str) -> tuple[str, list[str]]:
    """Auto-fix known bad patterns in Lean 4 code. Returns (fixed_code, warnings)."""
    warnings = []

    # Check for known bad identifiers
    for bad_id, suggestion in KNOWN_BAD_IDENTIFIERS.items():
        if bad_id in code:
            warnings.append(f"Found `{bad_id}` — use {suggestion} instead")

    # Auto-fix: Complex.abs x → ‖x‖
    code = _re.sub(r'Complex\.abs\s+\(([^)]+)\)', r'‖\1‖', code)
    code = _re.sub(r'Complex\.abs\s+(\w+)', r'‖\1‖', code)

    # Auto-fix: Complex.pi → ↑Real.pi
    code = code.replace('Complex.pi', '↑Real.pi')

    # Auto-fix: Complex.conj x → starRingEnd ℂ x
    code = _re.sub(r'Complex\.conj\s+(\w+)', r'starRingEnd ℂ \1', code)

    return code, warnings


def _extract_code_block(text: str) -> str | None:
    """Extract Lean 4 code from a markdown code block."""
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
        newline = text.index("\n", start)
        start = newline + 1
        end = text.index("```", start)
        return text[start:end].strip()
    return text.strip()


def _get_client():
    """Get an Anthropic client, or None if unavailable."""
    try:
        import anthropic
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] `anthropic` package not installed. "
            "Run `pip install anthropic`."
        )
        return None

    try:
        client = anthropic.Anthropic()
        return client
    except Exception:
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY not set or invalid. "
            "Export your API key: `export ANTHROPIC_API_KEY=sk-...`"
        )
        return None


def call_agent(prompt: str, client=None) -> str | None:
    """Call the LLM agent to propose a mutation. Returns Lean 4 code or None."""
    if client is None:
        client = _get_client()
    if client is None:
        return None

    import anthropic

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError:
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY not set or invalid."
        )
        return None

    text = response.content[0].text
    return _extract_code_block(text)


def call_agent_fix(client, original_code: str, error_message: str) -> str | None:
    """Ask the agent to fix compilation errors. Returns fixed code or None."""
    prompt = (
        "The following Lean 4 code failed to compile. Fix the errors and return "
        "the COMPLETE corrected file. If a proof is too hard, replace it with `sorry`.\n\n"
        "## Compilation Error\n```\n"
        f"{error_message[:800]}\n"
        "```\n\n"
        "## Code to Fix\n```lean4\n"
        f"{original_code}\n"
        "```\n\n"
        "Output ONLY the corrected Lean 4 code in ```lean4 ... ``` markers."
    )

    import anthropic

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        return None

    text = response.content[0].text
    return _extract_code_block(text)


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

    client = _get_client()
    if client is None:
        return

    max_retries = 3  # retry attempts per cycle on failure

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
            lean_code = call_agent(prompt, client=client)

        if lean_code is None:
            console.print("[yellow]Agent returned no code. Skipping cycle.[/yellow]")
            continue

        # 2b. Lint pass: auto-fix known bad patterns
        lean_code, lint_warnings = lint_lean_code(lean_code)
        for w in lint_warnings:
            console.print(f"[dim]Lint: {w}[/dim]")

        console.print(f"[dim]Received {len(lean_code)} chars of Lean 4 code.[/dim]")

        # 3. Execute mutation
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Compiling mutation...", total=None)
            exec_result = execute_mutation(lean_code, lineage=lineage, use_docker=use_docker)

        # 3b. Retry loop: if compilation failed, ask agent to fix
        for retry in range(1, max_retries + 1):
            if exec_result.success:
                break
            error_msg = exec_result.fitness.error_message
            # Only retry on fixable errors (not timeouts or missing files)
            if not error_msg or "timed out" in error_msg.lower():
                break

            console.print(f"[dim]Compilation failed. Retry {retry}/{max_retries}...[/dim]")
            with Progress(
                SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description=f"Agent fixing errors (retry {retry})...", total=None)
                fixed_code = call_agent_fix(client, lean_code, error_msg)

            if not fixed_code or fixed_code == lean_code:
                console.print("[dim]Agent returned same code. Stopping retries.[/dim]")
                break

            fixed_code, fix_warnings = lint_lean_code(fixed_code)
            for w in fix_warnings:
                console.print(f"[dim]Lint (retry {retry}): {w}[/dim]")

            with Progress(
                SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description=f"Recompiling fix {retry}...", total=None)
                exec_result = execute_mutation(
                    fixed_code, lineage=lineage, use_docker=use_docker,
                )
            lean_code = fixed_code

            if exec_result.success:
                console.print(f"[green]Retry {retry} succeeded![/green]")
            else:
                console.print(f"[dim]Retry {retry} failed.[/dim]")

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
