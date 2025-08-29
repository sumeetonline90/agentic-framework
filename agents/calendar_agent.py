"""
Calendar Management Agent

Handles calendar operations, event scheduling, and availability management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.base_agent import BaseAgent
from core.message_bus import Message
from config.agent_config import AgentType


class EventStatus(Enum):
    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class EventType(Enum):
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    TASK = "task"
    OTHER = "other"


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    status: EventStatus = EventStatus.CONFIRMED
    event_type: EventType = EventType.MEETING
    created_at: datetime = field(default_factory=datetime.now)
    location: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    organizer: Optional[str] = None
    recurring: bool = False
    recurrence_pattern: Optional[str] = None
    reminder_minutes: int = 15
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Calendar:
    calendar_id: str
    name: str
    description: str
    owner: str
    color: str = "#4285f4"
    is_primary: bool = False
    is_shared: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    events: Dict[str, CalendarEvent] = field(default_factory=dict)


class CalendarAgent(BaseAgent):
    """
    Calendar Management Agent for handling calendar operations.
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.calendars: Dict[str, Calendar] = {}
        self.scheduled_reminders: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
    async def start(self) -> bool:
        """Start the calendar agent and initialize calendar management."""
        if await super().start():
            self.logger.info("Calendar agent started successfully")
            # Create default calendar if none exists
            if not self.calendars:
                default_calendar = Calendar(
                    calendar_id="default",
                    name="Default Calendar",
                    description="Default calendar for events",
                    owner="system",
                    is_primary=True
                )
                self.calendars["default"] = default_calendar
            
            # Start background task for monitoring reminders
            asyncio.create_task(self._monitor_reminders())
            return True
        return False
    
    async def stop(self) -> bool:
        """Stop the calendar agent and cancel all scheduled reminders."""
        # Cancel all scheduled reminders
        for reminder_id, task in self.scheduled_reminders.items():
            task.cancel()
        self.scheduled_reminders.clear()
        
        if await super().stop():
            self.logger.info("Calendar agent stopped successfully")
            return True
        return False
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages for calendar management."""
        try:
            if message.content.get("action") == "create_event":
                return await self._handle_create_event(message)
            elif message.content.get("action") == "update_event":
                return await self._handle_update_event(message)
            elif message.content.get("action") == "delete_event":
                return await self._handle_delete_event(message)
            elif message.content.get("action") == "list_events":
                return await self._handle_list_events(message)
            elif message.content.get("action") == "check_availability":
                return await self._handle_check_availability(message)
            elif message.content.get("action") == "create_calendar":
                return await self._handle_create_calendar(message)
            elif message.content.get("action") == "schedule_meeting":
                return await self._handle_schedule_meeting(message)
            else:
                return await super().process_message(message)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": str(e)},
                priority=message.priority
            )
    
    async def _handle_create_event(self, message: Message) -> Message:
        """Handle event creation request."""
        event_data = message.content.get("event_data", {})
        calendar_id = event_data.get("calendar_id", "default")
        
        if calendar_id not in self.calendars:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Calendar {calendar_id} not found"}
            )
        
        # Parse datetime strings
        start_time = datetime.fromisoformat(event_data["start_time"])
        end_time = datetime.fromisoformat(event_data["end_time"])
        
        event = CalendarEvent(
            event_id=event_data.get("event_id", f"event_{len(self.calendars[calendar_id].events) + 1}"),
            title=event_data.get("title", "Untitled Event"),
            description=event_data.get("description", ""),
            start_time=start_time,
            end_time=end_time,
            status=EventStatus(event_data.get("status", "confirmed")),
            event_type=EventType(event_data.get("event_type", "meeting")),
            location=event_data.get("location"),
            attendees=event_data.get("attendees", []),
            organizer=event_data.get("organizer"),
            recurring=event_data.get("recurring", False),
            recurrence_pattern=event_data.get("recurrence_pattern"),
            reminder_minutes=event_data.get("reminder_minutes", 15),
            metadata=event_data.get("metadata", {})
        )
        
        self.calendars[calendar_id].events[event.event_id] = event
        
        # Schedule reminder if specified
        if event.reminder_minutes > 0:
            await self._schedule_reminder(event, calendar_id)
        
        self.logger.info(f"Created event: {event.event_id} - {event.title}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "event_created",
                "event_id": event.event_id,
                "calendar_id": calendar_id,
                "event": self._event_to_dict(event)
            }
        )
    
    async def _handle_update_event(self, message: Message) -> Message:
        """Handle event update request."""
        event_id = message.content.get("event_id")
        calendar_id = message.content.get("calendar_id", "default")
        updates = message.content.get("updates", {})
        
        if calendar_id not in self.calendars:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Calendar {calendar_id} not found"}
            )
        
        if event_id not in self.calendars[calendar_id].events:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Event {event_id} not found"}
            )
        
        event = self.calendars[calendar_id].events[event_id]
        
        # Update event fields
        if "title" in updates:
            event.title = updates["title"]
        if "description" in updates:
            event.description = updates["description"]
        if "start_time" in updates:
            event.start_time = datetime.fromisoformat(updates["start_time"])
        if "end_time" in updates:
            event.end_time = datetime.fromisoformat(updates["end_time"])
        if "status" in updates:
            event.status = EventStatus(updates["status"])
        if "event_type" in updates:
            event.event_type = EventType(updates["event_type"])
        if "location" in updates:
            event.location = updates["location"]
        if "attendees" in updates:
            event.attendees = updates["attendees"]
        if "organizer" in updates:
            event.organizer = updates["organizer"]
        if "reminder_minutes" in updates:
            event.reminder_minutes = updates["reminder_minutes"]
        if "metadata" in updates:
            event.metadata.update(updates["metadata"])
        
        # Reschedule reminder if needed
        if "reminder_minutes" in updates or "start_time" in updates:
            # Cancel existing reminder
            reminder_id = f"{calendar_id}_{event_id}"
            if reminder_id in self.scheduled_reminders:
                self.scheduled_reminders[reminder_id].cancel()
                del self.scheduled_reminders[reminder_id]
            
            # Schedule new reminder
            if event.reminder_minutes > 0:
                await self._schedule_reminder(event, calendar_id)
        
        self.logger.info(f"Updated event: {event_id}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "event_updated",
                "event_id": event_id,
                "calendar_id": calendar_id,
                "event": self._event_to_dict(event)
            }
        )
    
    async def _handle_delete_event(self, message: Message) -> Message:
        """Handle event deletion request."""
        event_id = message.content.get("event_id")
        calendar_id = message.content.get("calendar_id", "default")
        
        if calendar_id not in self.calendars:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Calendar {calendar_id} not found"}
            )
        
        if event_id not in self.calendars[calendar_id].events:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Event {event_id} not found"}
            )
        
        # Cancel reminder if exists
        reminder_id = f"{calendar_id}_{event_id}"
        if reminder_id in self.scheduled_reminders:
            self.scheduled_reminders[reminder_id].cancel()
            del self.scheduled_reminders[reminder_id]
        
        del self.calendars[calendar_id].events[event_id]
        self.logger.info(f"Deleted event: {event_id}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "event_deleted",
                "event_id": event_id,
                "calendar_id": calendar_id
            }
        )
    
    async def _handle_list_events(self, message: Message) -> Message:
        """Handle event listing request."""
        calendar_id = message.content.get("calendar_id", "default")
        filters = message.content.get("filters", {})
        
        if calendar_id not in self.calendars:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Calendar {calendar_id} not found"}
            )
        
        events = self._filter_events(self.calendars[calendar_id].events.values(), filters)
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "events_listed",
                "calendar_id": calendar_id,
                "events": [self._event_to_dict(event) for event in events],
                "count": len(events)
            }
        )
    
    async def _handle_check_availability(self, message: Message) -> Message:
        """Handle availability checking request."""
        calendar_id = message.content.get("calendar_id", "default")
        start_time = datetime.fromisoformat(message.content["start_time"])
        end_time = datetime.fromisoformat(message.content["end_time"])
        
        if calendar_id not in self.calendars:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Calendar {calendar_id} not found"}
            )
        
        # Check for conflicts
        conflicts = []
        for event in self.calendars[calendar_id].events.values():
            if event.status != EventStatus.CANCELLED:
                # Check for overlap
                if (event.start_time < end_time and event.end_time > start_time):
                    conflicts.append(self._event_to_dict(event))
        
        is_available = len(conflicts) == 0
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "availability_checked",
                "calendar_id": calendar_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "is_available": is_available,
                "conflicts": conflicts
            }
        )
    
    async def _handle_create_calendar(self, message: Message) -> Message:
        """Handle calendar creation request."""
        calendar_data = message.content.get("calendar_data", {})
        
        calendar = Calendar(
            calendar_id=calendar_data.get("calendar_id", f"calendar_{len(self.calendars) + 1}"),
            name=calendar_data.get("name", "Untitled Calendar"),
            description=calendar_data.get("description", ""),
            owner=calendar_data.get("owner", "system"),
            color=calendar_data.get("color", "#4285f4"),
            is_primary=calendar_data.get("is_primary", False),
            is_shared=calendar_data.get("is_shared", False)
        )
        
        self.calendars[calendar.calendar_id] = calendar
        self.logger.info(f"Created calendar: {calendar.calendar_id} - {calendar.name}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "calendar_created",
                "calendar_id": calendar.calendar_id,
                "calendar": {
                    "calendar_id": calendar.calendar_id,
                    "name": calendar.name,
                    "description": calendar.description,
                    "owner": calendar.owner,
                    "color": calendar.color,
                    "is_primary": calendar.is_primary,
                    "is_shared": calendar.is_shared,
                    "created_at": calendar.created_at.isoformat()
                }
            }
        )
    
    async def _handle_schedule_meeting(self, message: Message) -> Message:
        """Handle meeting scheduling request."""
        meeting_data = message.content.get("meeting_data", {})
        calendar_id = meeting_data.get("calendar_id", "default")
        
        if calendar_id not in self.calendars:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Calendar {calendar_id} not found"}
            )
        
        # Check availability for all attendees
        start_time = datetime.fromisoformat(meeting_data["start_time"])
        end_time = datetime.fromisoformat(meeting_data["end_time"])
        attendees = meeting_data.get("attendees", [])
        
        # For now, just check the main calendar
        # In a real implementation, you'd check all attendee calendars
        conflicts = []
        for event in self.calendars[calendar_id].events.values():
            if event.status != EventStatus.CANCELLED:
                if (event.start_time < end_time and event.end_time > start_time):
                    conflicts.append(self._event_to_dict(event))
        
        if conflicts:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "meeting_scheduling_failed",
                    "reason": "Conflicts found",
                    "conflicts": conflicts
                }
            )
        
        # Create the meeting event
        event = CalendarEvent(
            event_id=f"meeting_{len(self.calendars[calendar_id].events) + 1}",
            title=meeting_data.get("title", "Meeting"),
            description=meeting_data.get("description", ""),
            start_time=start_time,
            end_time=end_time,
            event_type=EventType.MEETING,
            location=meeting_data.get("location"),
            attendees=attendees,
            organizer=meeting_data.get("organizer"),
            reminder_minutes=meeting_data.get("reminder_minutes", 15),
            metadata=meeting_data.get("metadata", {})
        )
        
        self.calendars[calendar_id].events[event.event_id] = event
        
        # Schedule reminder
        if event.reminder_minutes > 0:
            await self._schedule_reminder(event, calendar_id)
        
        self.logger.info(f"Scheduled meeting: {event.event_id} - {event.title}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "meeting_scheduled",
                "event_id": event.event_id,
                "calendar_id": calendar_id,
                "event": self._event_to_dict(event)
            }
        )
    
    async def _schedule_reminder(self, event: CalendarEvent, calendar_id: str):
        """Schedule a reminder for an event."""
        reminder_time = event.start_time - timedelta(minutes=event.reminder_minutes)
        delay = (reminder_time - datetime.now()).total_seconds()
        
        if delay > 0:
            reminder_id = f"{calendar_id}_{event.event_id}"
            scheduled_task = asyncio.create_task(self._send_reminder(event, calendar_id, delay))
            self.scheduled_reminders[reminder_id] = scheduled_task
    
    async def _send_reminder(self, event: CalendarEvent, calendar_id: str, delay: float):
        """Send a reminder for an event."""
        try:
            await asyncio.sleep(delay)
            
            # Check if event still exists and is not cancelled
            if (calendar_id in self.calendars and 
                event.event_id in self.calendars[calendar_id].events and
                self.calendars[calendar_id].events[event.event_id].status != EventStatus.CANCELLED):
                
                self.logger.info(f"Sending reminder for event: {event.event_id}")
                
                # Notify other agents about the reminder
                await self.message_bus.broadcast(Message(
                    sender=self.agent_id,
                    content={
                        "action": "event_reminder",
                        "event_id": event.event_id,
                        "calendar_id": calendar_id,
                        "event": self._event_to_dict(event),
                        "reminder_time": datetime.now().isoformat()
                    }
                ))
            
        except asyncio.CancelledError:
            self.logger.info(f"Reminder for event {event.event_id} was cancelled")
    
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for calendar agent."""
        try:
            action = message.content.get("action")
            
            if action == "create_event":
                return await self._handle_create_event(message)
            elif action == "update_event":
                return await self._handle_update_event(message)
            elif action == "delete_event":
                return await self._handle_delete_event(message)
            elif action == "list_events":
                return await self._handle_list_events(message)
            elif action == "check_availability":
                return await self._handle_check_availability(message)
            elif action == "create_calendar":
                return await self._handle_create_calendar(message)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error in _process_message_impl: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            self.logger.error(f"Error sending reminder for event {event.event_id}: {e}")
    
    async def _monitor_reminders(self):
        """Monitor and clean up completed reminders."""
        while self.status.is_running():
            try:
                # Clean up completed reminders
                completed_reminders = [
                    reminder_id for reminder_id, task in self.scheduled_reminders.items()
                    if task.done()
                ]
                
                for reminder_id in completed_reminders:
                    del self.scheduled_reminders[reminder_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in reminder monitor: {e}")
                await asyncio.sleep(60)
    
    def _filter_events(self, events: List[CalendarEvent], filters: Dict[str, Any]) -> List[CalendarEvent]:
        """Filter events based on criteria."""
        filtered_events = list(events)
        
        if "status" in filters:
            status = EventStatus(filters["status"])
            filtered_events = [e for e in filtered_events if e.status == status]
        
        if "event_type" in filters:
            event_type = EventType(filters["event_type"])
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        
        if "start_date" in filters:
            start_date = datetime.fromisoformat(filters["start_date"])
            filtered_events = [e for e in filtered_events if e.start_time >= start_date]
        
        if "end_date" in filters:
            end_date = datetime.fromisoformat(filters["end_date"])
            filtered_events = [e for e in filtered_events if e.end_time <= end_date]
        
        if "attendee" in filters:
            attendee = filters["attendee"]
            filtered_events = [e for e in filtered_events if attendee in e.attendees]
        
        if "organizer" in filters:
            organizer = filters["organizer"]
            filtered_events = [e for e in filtered_events if e.organizer == organizer]
        
        return filtered_events
    
    def _event_to_dict(self, event: CalendarEvent) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": event.event_id,
            "title": event.title,
            "description": event.description,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "status": event.status.value,
            "event_type": event.event_type.value,
            "created_at": event.created_at.isoformat(),
            "location": event.location,
            "attendees": event.attendees,
            "organizer": event.organizer,
            "recurring": event.recurring,
            "recurrence_pattern": event.recurrence_pattern,
            "reminder_minutes": event.reminder_minutes,
            "metadata": event.metadata
        }

    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for calendar agent."""
        try:
            action = message.content.get("action")
            
            if action == "create_event":
                return await self._handle_create_event(message)
            elif action == "update_event":
                return await self._handle_update_event(message)
            elif action == "delete_event":
                return await self._handle_delete_event(message)
            elif action == "list_events":
                return await self._handle_list_events(message)
            elif action == "check_availability":
                return await self._handle_check_availability(message)
            elif action == "create_calendar":
                return await self._handle_create_calendar(message)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error in _process_message_impl: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get calendar agent metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "total_calendars": len(self.calendars),
            "total_events": sum(len(cal.events) for cal in self.calendars.values()),
            "events_by_status": {
                status.value: sum(
                    len([e for e in cal.events.values() if e.status == status])
                    for cal in self.calendars.values()
                )
                for status in EventStatus
            },
            "events_by_type": {
                event_type.value: sum(
                    len([e for e in cal.events.values() if e.event_type == event_type])
                    for cal in self.calendars.values()
                )
                for event_type in EventType
            },
            "scheduled_reminders": len(self.scheduled_reminders)
        })
        return metrics
