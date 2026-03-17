"""
status.py — Local Environment Status

Displays the current state of the contributor's local Open Evolutions setup:
knowledge base version, active lineages, contribution log summary.
"""

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def show_status() -> None:
    """Display the current state of the local evolution environment."""
    console.print(Panel("[bold]Open Evolutions — Status[/bold]"))

    # Knowledge base
    learnings_path = PROJECT_ROOT / "knowledge" / "learnings.json"
    if learnings_path.exists():
        data = json.loads(learnings_path.read_text())
        console.print(f"Knowledge base version: [bold]{data.get('version', 'unknown')}[/bold]")
        console.print(f"  Negative constraints: {len(data.get('negative_constraints', []))}")
        console.print(f"  Positive heuristics: {len(data.get('positive_heuristics', []))}")
        console.print(f"  Unexplored frontiers: {len(data.get('unexplored_frontiers', []))}")
    else:
        console.print("[yellow]No knowledge base found. Run `oe-cli init` first.[/yellow]")

    # Lineages
    lineages_dir = PROJECT_ROOT / "lineages"
    if lineages_dir.exists():
        console.print()
        table = Table(title="Active Lineages")
        table.add_column("Name", style="bold")
        table.add_column("Description")
        table.add_column("Heuristics")
        table.add_column("Dead Ends")

        for lineage_dir in sorted(lineages_dir.iterdir()):
            if not lineage_dir.is_dir():
                continue
            learnings_file = lineage_dir / "lineage_learnings.json"
            if learnings_file.exists():
                data = json.loads(learnings_file.read_text())
                table.add_row(
                    data.get("lineage", lineage_dir.name),
                    data.get("description", "—")[:60],
                    str(len(data.get("heuristics", []))),
                    str(len(data.get("dead_ends", []))),
                )
            else:
                table.add_row(lineage_dir.name, "—", "0", "0")

        console.print(table)

    # Contribution log
    log_path = PROJECT_ROOT / "contribution_log.json"
    if log_path.exists():
        entries = json.loads(log_path.read_text())
        total = len(entries)
        successes = sum(1 for e in entries if e.get("success"))
        console.print(f"\nContribution log: {total} mutations ({successes} compiled)")
    else:
        console.print("\n[dim]No contribution log yet. Run `oe-cli start` to begin evolving.[/dim]")
