"""
BrahmaAI Calendar Tool
Mock calendar scheduling for demo/development.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from backend.tools.registry import BaseTool

logger = logging.getLogger(__name__)


class CalendarTool(BaseTool):
    name = "calendar_tool"
    description = "Schedule, list, and manage calendar events (mock API)"
    args = {
        "action": "str: 'create', 'list', or 'delete'",
        "title": "str: Event title (for create)",
        "date": "str: Event date in YYYY-MM-DD format",
        "time": "str: Event time in HH:MM format",
        "duration_minutes": "int: Duration in minutes (default: 60)",
        "description": "str: Event description (optional)",
    }

    _events: list[dict[str, Any]] = []

    async def execute(
        self,
        action: str = "list",
        title: str = "",
        date: str = "",
        time: str = "09:00",
        duration_minutes: int = 60,
        description: str = "",
        event_id: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        logger.info(f"[CalendarTool] Action: {action}")

        if action == "create":
            return self._create_event(title, date, time, duration_minutes, description)
        elif action == "list":
            return self._list_events()
        elif action == "delete":
            return self._delete_event(event_id)
        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
                "output": f"Unknown action: {action}. Use 'create', 'list', or 'delete'.",
            }

    def _create_event(
        self,
        title: str,
        date: str,
        time_str: str,
        duration: int,
        description: str,
    ) -> dict[str, Any]:
        if not title:
            return {"status": "error", "error": "Event title is required", "output": "Title required."}

        event = {
            "id": str(uuid.uuid4()),
            "title": title,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "time": time_str,
            "duration_minutes": duration,
            "description": description,
            "created_at": time.time(),
        }
        self._events.append(event)

        return {
            "status": "success",
            "event_id": event["id"],
            "output": (
                f"📅 Event created!\n"
                f"Title: {title}\n"
                f"Date: {event['date']} at {event['time']}\n"
                f"Duration: {duration} minutes\n"
                f"(Note: Mock calendar — integrate Google Calendar API for production)"
            ),
            "event": event,
        }

    def _list_events(self) -> dict[str, Any]:
        if not self._events:
            return {
                "status": "success",
                "output": "No events scheduled.",
                "events": [],
            }
        lines = ["📅 Upcoming Events:\n"]
        for ev in sorted(self._events, key=lambda x: x["date"]):
            lines.append(
                f"• {ev['date']} {ev['time']} — {ev['title']} "
                f"({ev['duration_minutes']}min)"
            )
        return {
            "status": "success",
            "output": "\n".join(lines),
            "events": self._events,
        }

    def _delete_event(self, event_id: str) -> dict[str, Any]:
        for i, ev in enumerate(self._events):
            if ev["id"] == event_id:
                self._events.pop(i)
                return {
                    "status": "success",
                    "output": f"Event deleted: {ev['title']}",
                }
        return {
            "status": "error",
            "error": f"Event not found: {event_id}",
            "output": f"No event found with ID: {event_id}",
        }
