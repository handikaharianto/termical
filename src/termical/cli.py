"""CLI entry point for termical."""
import typer
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from termical import __version__

app = typer.Typer(
    name="termical",
    help="Termical - Where your schedule meets your terminal",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        rprint(f"[bold]termical[/bold] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Termical - Where your schedule meets your terminal."""
    pass


@app.command()
def setup() -> None:
    """Interactive setup wizard for first-time configuration."""
    from termical.commands.setup import run_setup
    run_setup()


@app.command()
def today(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show AI-generated summaries for each activity"
    )
) -> None:
    """Display today's activities in a formatted table."""
    from termical.commands.today import show_today
    show_today(verbose=verbose)


if __name__ == "__main__":
    app()
