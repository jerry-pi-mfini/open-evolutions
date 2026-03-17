"""
oe-cli — Open Evolutions Command-Line Interface

The primary tool for contributors to interact with the Open Evolutions platform.
Handles environment setup, agent-driven evolution loops, and PR submission.
"""

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="oe-cli",
    help="Open Evolutions — Distributed Research Engine CLI",
    no_args_is_help=True,
)
console = Console()


@app.command()
def init(
    challenge: str = typer.Option("RZCS", help="Challenge identifier to initialize."),
) -> None:
    """Initialize a local fork for an Open Evolutions challenge.

    Checks dependencies (Lean 4, Docker), sets up the Lake project, and
    initializes the knowledge base.
    """
    from core.prepare import prepare

    console.print(Panel(f"Initializing Open Evolutions for challenge: [bold]{challenge}[/bold]"))
    success = prepare()
    if success:
        console.print("\n[bold green]Ready to evolve![/bold green] Run `oe-cli start` to begin.")
    else:
        console.print(
            "\n[bold yellow]Setup completed with warnings.[/bold yellow] "
            "Some features may be limited."
        )


@app.command()
def start(
    challenge: str = typer.Option("RZCS", help="Challenge identifier."),
    lineage: str = typer.Option(
        None, help="Specific lineage to focus on. If omitted, the agent chooses."
    ),
    cycles: int = typer.Option(10, help="Number of mutation cycles to run."),
    cycle_minutes: int = typer.Option(5, help="Maximum minutes per mutation cycle."),
    docker: bool = typer.Option(False, help="Run mutations in Docker sandbox."),
) -> None:
    """Start the autonomous evolution loop.

    The agent ingests the master knowledge base and lineage wisdom, then
    runs Karpathy-style experiment cycles proposing and testing Lean 4 mutations.
    """
    from oe_cli.evolve import run_evolution_loop

    console.print(Panel(
        f"[bold]Starting evolution loop[/bold]\n"
        f"Challenge: {challenge}\n"
        f"Lineage: {lineage or 'agent-selected'}\n"
        f"Cycles: {cycles} x {cycle_minutes}min"
    ))

    run_evolution_loop(
        challenge=challenge,
        lineage=lineage,
        num_cycles=cycles,
        cycle_minutes=cycle_minutes,
        use_docker=docker,
    )


@app.command()
def submit(
    lineage: str = typer.Option(..., help="Lineage this submission belongs to."),
    message: str = typer.Option(None, help="Optional description of this contribution."),
) -> None:
    """Package the current work into a PR-ready submission.

    Synthesizes contribution logs, validates fitness scores, and prepares
    a branch with all required artifacts.
    """
    from oe_cli.submit import prepare_submission

    console.print(Panel("[bold]Preparing submission[/bold]"))
    prepare_submission(lineage=lineage, message=message)


@app.command()
def status() -> None:
    """Show the current state of the local evolution environment."""
    from oe_cli.status import show_status

    show_status()


if __name__ == "__main__":
    app()
