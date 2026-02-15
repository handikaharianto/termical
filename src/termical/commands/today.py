"""Today command - display today's activities."""
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from termical.sync import get_sync_engine
from termical.config import get_config
from termical.database import init_database

console = Console()


def show_today(verbose: bool = False) -> None:
    """Display today's activities in a formatted table.

    Args:
        verbose: If True, show AI summaries for each activity
    """
    # Check if configured
    config = get_config()
    
    if not config.is_configured():
        console.print(
            "[bold red]Error:[/bold red] Application not configured.\n"
            "Please run [bold]termical setup[/bold] first."
        )
        return
    
    # Initialize database connection
    try:
        db_url = config.get_database_url()
        init_database(db_url)
    except Exception as e:
        console.print(f"[bold red]Database error:[/bold red] {e}")
        console.print("Please run [bold]termical setup[/bold] to reconfigure.")
        return
    
    # Sync activities
    try:
        sync_engine = get_sync_engine()
        activities = sync_engine.sync_today()
    except Exception as e:
        console.print(f"[bold red]Error syncing activities:[/bold red] {e}")
        return
    
    # Display results
    if not activities:
        console.print()
        console.print(
            Panel.fit(
                "[yellow]No activities scheduled for today[/yellow]\n\n"
                "Enjoy your free time! 🎉",
                title="Today's Activities",
                border_style="yellow"
            )
        )
        console.print()
        return
    
    # Create table
    table = Table(
        title=f"Today's Activities ({len(activities)} total)",
        show_header=True,
        header_style="bold cyan",
        title_style="bold",
    )
    
    table.add_column("Time", style="cyan", no_wrap=True, width=11)
    table.add_column("Title", style="white")
    table.add_column("Duration", justify="right", style="magenta", width=8)
    table.add_column("Attendees", justify="right", style="green", width=9)

    # Add rows
    for activity in activities:
        # Format time (convert from UTC to local)
        start_time_utc = activity.start_time.replace(tzinfo=timezone.utc)
        start_local = start_time_utc.astimezone()
        time_str = start_local.strftime("%I:%M %p")
        
        # Calculate duration
        duration_seconds = (activity.end_time - activity.start_time).total_seconds()
        duration_minutes = int(duration_seconds / 60)
        
        if duration_minutes < 60:
            duration_str = f"{duration_minutes}m"
        else:
            hours = duration_minutes // 60
            mins = duration_minutes % 60
            duration_str = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
        
        # Attendee count
        attendee_count = len(activity.attendees) if activity.attendees else 0
        
        # Add row
        table.add_row(
            time_str,
            activity.title,
            duration_str,
            str(attendee_count)
        )
        
        # Add summary row if verbose
        if verbose and activity.ai_summary:
            table.add_row(
                "",
                f"[dim italic]{activity.ai_summary}[/dim italic]",
                "",
                ""
            )
    
    console.print()
    console.print(table)
    console.print()
    
    # Show tip if not verbose
    if not verbose:
        console.print(
            "[dim]💡 Tip: Use [bold]--verbose[/bold] flag to see AI-generated summaries[/dim]"
        )
        console.print()
