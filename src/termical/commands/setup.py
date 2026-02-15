"""Setup command for initial configuration."""
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from termical.config import (
    get_config,
    set_openai_key,
    CREDENTIALS_FILE,
    CONFIG_DIR,
)
from termical.database import init_database

console = Console()


def run_setup() -> None:
    """Run the interactive setup wizard."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Welcome to Termical Setup[/bold cyan]\n\n"
            "This wizard will help you configure:\n"
            "  • PostgreSQL database connection\n"
            "  • OpenAI API key\n"
            "  • Google Calendar OAuth credentials",
            title="Setup Wizard",
            border_style="cyan",
        )
    )
    console.print()
    
    config = get_config()
    
    # Step 1: Database Configuration
    console.print("[bold]Step 1/3: Database Configuration[/bold]")
    console.print("Configure your PostgreSQL connection (default: Docker Compose settings)\n")
    
    db_host = questionary.text(
        "Database host:",
        default="localhost"
    ).ask()
    
    db_port = questionary.text(
        "Database port:",
        default="5432"
    ).ask()
    
    db_name = questionary.text(
        "Database name:",
        default="termical"
    ).ask()
    
    db_user = questionary.text(
        "Database user:",
        default="termical_user"
    ).ask()
    
    db_password = questionary.password(
        "Database password:"
    ).ask()
    
    # Save database config
    config.set("database.host", db_host)
    config.set("database.port", int(db_port))
    config.set("database.name", db_name)
    config.set("database.user", db_user)
    config.set("database.password", db_password)
    
    # Test database connection
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Testing database connection...", total=None)
        
        try:
            db_url = config.get_database_url()
            db = init_database(db_url)
            
            if not db.verify_connection():
                console.print("[bold red]✗[/bold red] Database connection failed!")
                console.print("\n[yellow]Tips:[/yellow]")
                console.print("  • Make sure PostgreSQL is running (try: docker-compose up -d)")
                console.print("  • Check your credentials")
                console.print("  • Verify the database exists")
                return
            
            # Create tables
            db.create_tables()
            console.print("[bold green]✓[/bold green] Database connection successful!")
            console.print("[bold green]✓[/bold green] Database tables created!")
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Error: {e}")
            return
    
    console.print()
    
    # Step 2: OpenAI API Key
    console.print("[bold]Step 2/3: OpenAI Configuration[/bold]")
    console.print("Enter your OpenAI API key (will be stored securely in system keyring)\n")
    
    openai_key = questionary.password(
        "OpenAI API Key:",
        validate=lambda text: len(text) > 0 or "API key cannot be empty"
    ).ask()
    
    if openai_key:
        set_openai_key(openai_key)
        console.print("[bold green]✓[/bold green] OpenAI API key stored securely!")
    
    console.print()
    
    # Step 3: Google Calendar OAuth
    console.print("[bold]Step 3/3: Google Calendar Setup[/bold]")
    console.print(
        "To use Google Calendar integration, you need to:\n"
        "  1. Create a project in Google Cloud Console\n"
        "  2. Enable the Google Calendar API\n"
        "  3. Create OAuth 2.0 credentials (Desktop app)\n"
        "  4. Download credentials.json\n"
    )
    
    if not CREDENTIALS_FILE.exists():
        console.print(
            f"\n[yellow]Please place your credentials.json file in:[/yellow]\n"
            f"  {CREDENTIALS_FILE}\n"
        )
        
        setup_now = questionary.confirm(
            "Have you placed the credentials.json file?",
            default=False
        ).ask()
        
        if not setup_now:
            console.print(
                "\n[yellow]You can add credentials.json later and re-run setup.[/yellow]"
            )
    else:
        console.print("[bold green]✓[/bold green] credentials.json found!")
    
    # Save configuration
    config.save()
    console.print()
    
    # Summary
    console.print(
        Panel.fit(
            "[bold green]Setup Complete![/bold green]\n\n"
            f"Configuration saved to: {config.config_file}\n\n"
            "Next steps:\n"
            "  • Run [bold]termical today[/bold] to see today's activities\n"
            "  • Use [bold]--verbose[/bold] flag to see AI summaries",
            title="Success",
            border_style="green",
        )
    )
    console.print()
