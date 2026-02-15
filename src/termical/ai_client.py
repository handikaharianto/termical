"""OpenAI API client for activity summarization and action item extraction."""
import json
from typing import Any

from openai import OpenAI
from openai import OpenAIError
from rich.console import Console

from termical.config import get_openai_key

console = Console()


class AIClient:
    """OpenAI API client for activity processing."""
    
    def __init__(self, api_key: str | None = None):
        """Initialize the AI client.
        
        Args:
            api_key: OpenAI API key (if None, will try to load from config)
        """
        if api_key is None:
            api_key = get_openai_key()
        
        if not api_key:
            raise ValueError("OpenAI API key not found. Run 'termical setup' first.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def generate_summary(
        self,
        title: str,
        description: str | None = None
    ) -> str | None:
        """Generate a 1-2 sentence prep summary for an activity.

        Args:
            title: Activity title
            description: Activity description/notes
            
        Returns:
            Summary text or None if generation fails
        """
        if not description or description.strip() == "":
            # No description, return a simple statement
            return f"Activity: {title}"
        
        prompt = f"""Generate a concise 1-2 sentence prep summary for this activity.

Activity Title: {title}
Description: {description}

Provide a brief summary that helps someone prepare for this activity. Focus on the key topics, goals, or action items mentioned."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise activity summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except OpenAIError as e:
            console.print(f"[yellow]OpenAI API error (summary): {e}[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]Error generating summary: {e}[/yellow]")
            return None
    
    def extract_action_items(
        self,
        title: str,
        description: str | None = None
    ) -> list[dict[str, Any]]:
        """Extract action items from activity description.

        Args:
            title: Activity title
            description: Activity description/notes
            
        Returns:
            List of action items in format: [{"task": str, "assignee": str, "status": str}]
        """
        if not description or description.strip() == "":
            return []
        
        prompt = f"""Extract action items from this activity.

Activity Title: {title}
Description: {description}

Identify any tasks, action items, or to-dos mentioned. For each action item, extract:
- task: What needs to be done
- assignee: Who is responsible (use "Unassigned" if not specified)
- status: Always set to "pending"

Return the results as a JSON array. If no action items found, return an empty array."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts action items from activity notes. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            
            # Handle different JSON structures
            if isinstance(result, list):
                action_items = result
            elif isinstance(result, dict):
                # Try common keys
                action_items = (
                    result.get("action_items") or
                    result.get("actions") or
                    result.get("tasks") or
                    []
                )
            else:
                action_items = []
            
            # Validate structure
            validated_items = []
            for item in action_items:
                if isinstance(item, dict) and "task" in item:
                    validated_items.append({
                        "task": item.get("task", ""),
                        "assignee": item.get("assignee", "Unassigned"),
                        "status": item.get("status", "pending")
                    })
            
            return validated_items
            
        except OpenAIError as e:
            console.print(f"[yellow]OpenAI API error (actions): {e}[/yellow]")
            return []
        except json.JSONDecodeError as e:
            console.print(f"[yellow]Error parsing action items JSON: {e}[/yellow]")
            return []
        except Exception as e:
            console.print(f"[yellow]Error extracting action items: {e}[/yellow]")
            return []


# Global client instance
_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    """Get the global AI client instance.
    
    Returns:
        AIClient instance
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
