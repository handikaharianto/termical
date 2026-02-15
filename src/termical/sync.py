"""Data synchronization engine for fetching and processing activities."""
from datetime import datetime, timedelta
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from termical.calendar_client import get_calendar_client
from termical.ai_client import get_ai_client
from termical.database import get_database
from termical.models import Activity

console = Console()


class SyncEngine:
    """Orchestrates calendar fetching and AI processing."""
    
    def __init__(self):
        """Initialize sync engine."""
        self.calendar_client = get_calendar_client()
        self.ai_client = get_ai_client()
        self.db = get_database()
    
    def sync_today(self, force_refresh: bool = False) -> list[Activity]:
        """Sync today's activities from Google Calendar.
        
        Args:
            force_refresh: Force refresh even if data is recent
            
        Returns:
            List of Activity objects for today
        """
        # Check if we need to refresh
        if not force_refresh and self._is_data_fresh():
            # Return cached data
            return self._get_today_activities_from_db()
        
        # Authenticate with Google Calendar
        console.print("[dim]Connecting to Google Calendar...[/dim]")
        if not self.calendar_client.authenticate():
            console.print("[yellow]Using cached data (if available)[/yellow]")
            return self._get_today_activities_from_db()
        
        # Fetch events
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                description="Fetching today's activities...",
                total=None
            )
            
            raw_events = self.calendar_client.get_today_events()
            
            if not raw_events:
                console.print("[dim]No activities found for today[/dim]")
                return []
            
            progress.update(
                task,
                description=f"Processing {len(raw_events)} activities..."
            )
            
            # Process each event
            activities = []
            for raw_event in raw_events:
                event = self.calendar_client.parse_event(raw_event)
                
                # Generate AI summary and extract action items
                ai_summary = self.ai_client.generate_summary(
                    event["title"],
                    event.get("description")
                )
                
                action_items = self.ai_client.extract_action_items(
                    event["title"],
                    event.get("description")
                )
                
                # Prepare activity data
                activity_data = {
                    "event_id": event["event_id"],
                    "title": event["title"],
                    "start_time": event["start_time"],
                    "end_time": event["end_time"],
                    "description": event.get("description"),
                    "attendees": event.get("attendees", []),
                    "ai_summary": ai_summary,
                    "action_items": action_items,
                    "last_synced": datetime.utcnow(),
                }
                
                # Upsert to database
                self._upsert_activity(activity_data)
                activities.append(activity_data)
            
            progress.update(task, description="✓ Sync complete!")
        
        console.print(f"[green]Synced {len(activities)} activities[/green]")
        
        # Return fresh data from database
        return self._get_today_activities_from_db()
    
    def _is_data_fresh(self, max_age_minutes: int = 30) -> bool:
        """Check if cached data is fresh enough.
        
        Args:
            max_age_minutes: Maximum age of data to consider fresh
            
        Returns:
            True if data is fresh, False otherwise
        """
        session = self.db.get_session()
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Check if any activity for today was synced recently
            stmt = (
                select(Activity)
                .where(Activity.start_time >= today_start)
                .where(Activity.start_time < today_start + timedelta(days=1))
                .order_by(Activity.last_synced.desc())
                .limit(1)
            )
            
            result = session.execute(stmt).first()
            
            if result is None:
                return False
            
            activity = result[0]
            age = now - activity.last_synced
            
            return age.total_seconds() < (max_age_minutes * 60)
            
        finally:
            session.close()
    
    def _get_today_activities_from_db(self) -> list[Activity]:
        """Get today's activities from database.

        Returns:
            List of Activity objects
        """
        session = self.db.get_session()
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            stmt = (
                select(Activity)
                .where(Activity.start_time >= today_start)
                .where(Activity.start_time < today_end)
                .order_by(Activity.start_time)
            )
            
            result = session.execute(stmt).scalars().all()
            return list(result)
            
        finally:
            session.close()
    
    def _upsert_activity(self, activity_data: dict[str, Any]) -> None:
        """Insert or update an activity in the database.

        Args:
            activity_data: Dictionary of activity data
        """
        session = self.db.get_session()
        try:
            stmt = insert(Activity).values(**activity_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["event_id"],
                set_={
                    "title": stmt.excluded.title,
                    "start_time": stmt.excluded.start_time,
                    "end_time": stmt.excluded.end_time,
                    "description": stmt.excluded.description,
                    "attendees": stmt.excluded.attendees,
                    "ai_summary": stmt.excluded.ai_summary,
                    "action_items": stmt.excluded.action_items,
                    "last_synced": stmt.excluded.last_synced,
                }
            )
            
            session.execute(stmt)
            session.commit()
            
        except Exception as e:
            session.rollback()
            console.print(f"[yellow]Warning: Failed to save activity: {e}[/yellow]")
        finally:
            session.close()


def get_sync_engine() -> SyncEngine:
    """Get a sync engine instance.
    
    Returns:
        SyncEngine instance
    """
    return SyncEngine()
