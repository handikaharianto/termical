"""Google Calendar API client."""
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rich.console import Console

from termical.config import TOKEN_FILE, CREDENTIALS_FILE

# Google Calendar API scope (read-only)
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

console = Console()


class CalendarClient:
    """Google Calendar API client with OAuth 2.0 authentication."""
    
    def __init__(self):
        """Initialize the calendar client."""
        self.creds: Credentials | None = None
        self.service = None
    
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        # Check if we have saved credentials
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, "rb") as token:
                self.creds = pickle.load(token)
        
        # If credentials are invalid or don't exist, get new ones
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Refresh expired credentials
                try:
                    self.creds.refresh(Request())
                    console.print("[dim]Access token refreshed[/dim]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Token refresh failed: {e}[/yellow]")
                    self.creds = None
            
            # If still no valid credentials, run OAuth flow
            if not self.creds or not self.creds.valid:
                if not CREDENTIALS_FILE.exists():
                    console.print(
                        f"[bold red]Error:[/bold red] credentials.json not found at {CREDENTIALS_FILE}\n"
                        "Please run [bold]termical setup[/bold] first."
                    )
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(CREDENTIALS_FILE), SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                    console.print("[green]✓[/green] Google Calendar authenticated!")
                except Exception as e:
                    console.print(f"[bold red]Error during OAuth flow:[/bold red] {e}")
                    return False
            
            # Save credentials for next time
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(self.creds, token)
        
        # Build the service
        try:
            self.service = build("calendar", "v3", credentials=self.creds)
            return True
        except Exception as e:
            console.print(f"[bold red]Error building Calendar service:[/bold red] {e}")
            return False
    
    def fetch_events(
        self,
        start_date: datetime,
        end_date: datetime,
        max_results: int = 100
    ) -> list[dict[str, Any]]:
        """Fetch calendar events for a date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (exclusive)
            max_results: Maximum number of events to fetch
            
        Returns:
            List of event dictionaries
            
        Raises:
            RuntimeError: If not authenticated or API call fails
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            # Convert to RFC3339 format
            time_min = start_date.isoformat() + "Z"
            time_max = end_date.isoformat() + "Z"
            
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,  # Expand recurring events
                    orderBy="startTime",
                )
                .execute()
            )
            
            events = events_result.get("items", [])
            return events
            
        except HttpError as e:
            if e.resp.status == 401:
                console.print("[bold red]Authentication error.[/bold red] Please run setup again.")
            elif e.resp.status == 403:
                console.print("[bold red]Permission denied.[/bold red] Check API is enabled.")
            elif e.resp.status == 429:
                console.print("[yellow]Rate limit exceeded.[/yellow] Please try again later.")
            else:
                console.print(f"[bold red]HTTP Error:[/bold red] {e}")
            return []
        except Exception as e:
            console.print(f"[bold red]Error fetching events:[/bold red] {e}")
            return []
    
    def get_today_events(self) -> list[dict[str, Any]]:
        """Fetch today's calendar events.
        
        Returns:
            List of today's event dictionaries
        """
        now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = now + timedelta(days=1)
        
        return self.fetch_events(now, tomorrow)
    
    def parse_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Parse a Google Calendar event into a normalized format.
        
        Args:
            event: Raw event dictionary from Google Calendar API
            
        Returns:
            Normalized event dictionary with standardized fields
        """
        # Parse start and end times
        start = event.get("start", {})
        end = event.get("end", {})
        
        # Handle all-day events vs timed events
        start_time = start.get("dateTime", start.get("date"))
        end_time = end.get("dateTime", end.get("date"))
        
        # Parse datetime strings
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        else:
            start_dt = datetime.utcnow()
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        else:
            end_dt = start_dt + timedelta(hours=1)
        
        # Parse attendees
        attendees = []
        for attendee in event.get("attendees", []):
            attendees.append({
                "email": attendee.get("email"),
                "name": attendee.get("displayName", attendee.get("email")),
                "status": attendee.get("responseStatus", "needsAction"),
            })
        
        return {
            "event_id": event.get("id"),
            "title": event.get("summary", "(No title)"),
            "description": event.get("description"),
            "start_time": start_dt,
            "end_time": end_dt,
            "attendees": attendees,
            "location": event.get("location"),
            "link": event.get("htmlLink"),
        }


# Global client instance
_calendar_client: CalendarClient | None = None


def get_calendar_client() -> CalendarClient:
    """Get the global calendar client instance.
    
    Returns:
        CalendarClient instance
    """
    global _calendar_client
    if _calendar_client is None:
        _calendar_client = CalendarClient()
    return _calendar_client
