"""
Task Automation Agent

Handles task scheduling, workflow automation, and process management.
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


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Task:
    task_id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskAgent(BaseAgent):
    """
    Task Automation Agent for managing tasks, workflows, and process automation.
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.tasks: Dict[str, Task] = {}
        self.workflows: Dict[str, Dict] = {}
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
    async def start(self) -> bool:
        """Start the task agent and initialize task management."""
        if await super().start():
            self.logger.info("Task agent started successfully")
            # Start background task for monitoring scheduled tasks
            asyncio.create_task(self._monitor_scheduled_tasks())
            return True
        return False
    
    async def stop(self) -> bool:
        """Stop the task agent and cancel all scheduled tasks."""
        # Cancel all scheduled tasks
        for task_id, task in self.scheduled_tasks.items():
            task.cancel()
        self.scheduled_tasks.clear()
        
        if await super().stop():
            self.logger.info("Task agent stopped successfully")
            return True
        return False
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages for task management."""
        try:
            if message.content.get("action") == "create_task":
                return await self._handle_create_task(message)
            elif message.content.get("action") == "update_task":
                return await self._handle_update_task(message)
            elif message.content.get("action") == "delete_task":
                return await self._handle_delete_task(message)
            elif message.content.get("action") == "list_tasks":
                return await self._handle_list_tasks(message)
            elif message.content.get("action") == "schedule_task":
                return await self._handle_schedule_task(message)
            elif message.content.get("action") == "create_workflow":
                return await self._handle_create_workflow(message)
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
    
    async def _handle_create_task(self, message: Message) -> Message:
        """Handle task creation request."""
        task_data = message.content.get("task_data", {})
        task = Task(
            task_id=task_data.get("task_id", f"task_{len(self.tasks) + 1}"),
            title=task_data.get("title", "Untitled Task"),
            description=task_data.get("description", ""),
            priority=TaskPriority(task_data.get("priority", "medium")),
            due_date=datetime.fromisoformat(task_data["due_date"]) if task_data.get("due_date") else None,
            assigned_to=task_data.get("assigned_to"),
            tags=task_data.get("tags", []),
            metadata=task_data.get("metadata", {})
        )
        
        self.tasks[task.task_id] = task
        self.logger.info(f"Created task: {task.task_id} - {task.title}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "task_created",
                "task_id": task.task_id,
                "task": self._task_to_dict(task)
            }
        )
    
    async def _handle_update_task(self, message: Message) -> Message:
        """Handle task update request."""
        task_id = message.content.get("task_id")
        updates = message.content.get("updates", {})
        
        if task_id not in self.tasks:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Task {task_id} not found"}
            )
        
        task = self.tasks[task_id]
        
        # Update task fields
        if "title" in updates:
            task.title = updates["title"]
        if "description" in updates:
            task.description = updates["description"]
        if "status" in updates:
            task.status = TaskStatus(updates["status"])
        if "priority" in updates:
            task.priority = TaskPriority(updates["priority"])
        if "due_date" in updates:
            task.due_date = datetime.fromisoformat(updates["due_date"]) if updates["due_date"] else None
        if "assigned_to" in updates:
            task.assigned_to = updates["assigned_to"]
        if "tags" in updates:
            task.tags = updates["tags"]
        if "metadata" in updates:
            task.metadata.update(updates["metadata"])
        
        self.logger.info(f"Updated task: {task_id}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "task_updated",
                "task_id": task_id,
                "task": self._task_to_dict(task)
            }
        )
    
    async def _handle_delete_task(self, message: Message) -> Message:
        """Handle task deletion request."""
        task_id = message.content.get("task_id")
        
        if task_id not in self.tasks:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Task {task_id} not found"}
            )
        
        # Cancel scheduled task if exists
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].cancel()
            del self.scheduled_tasks[task_id]
        
        del self.tasks[task_id]
        self.logger.info(f"Deleted task: {task_id}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "task_deleted",
                "task_id": task_id
            }
        )
    
    async def _handle_list_tasks(self, message: Message) -> Message:
        """Handle task listing request."""
        filters = message.content.get("filters", {})
        tasks = self._filter_tasks(filters)
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "tasks_listed",
                "tasks": [self._task_to_dict(task) for task in tasks],
                "count": len(tasks)
            }
        )
    
    async def _handle_schedule_task(self, message: Message) -> Message:
        """Handle task scheduling request."""
        task_id = message.content.get("task_id")
        schedule_time = message.content.get("schedule_time")
        
        if task_id not in self.tasks:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Task {task_id} not found"}
            )
        
        if not schedule_time:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": "Schedule time is required"}
            )
        
        # Parse schedule time
        try:
            if isinstance(schedule_time, str):
                schedule_dt = datetime.fromisoformat(schedule_time)
            else:
                schedule_dt = schedule_time
            
            # Calculate delay
            delay = (schedule_dt - datetime.now()).total_seconds()
            if delay <= 0:
                return Message(
                    sender=self.agent_id,
                    recipient=message.sender,
                    content={"error": "Schedule time must be in the future"}
                )
            
            # Schedule the task
            scheduled_task = asyncio.create_task(self._execute_scheduled_task(task_id, delay))
            self.scheduled_tasks[task_id] = scheduled_task
            
            self.logger.info(f"Scheduled task {task_id} for {schedule_dt}")
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "task_scheduled",
                    "task_id": task_id,
                    "schedule_time": schedule_dt.isoformat()
                }
            )
            
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Invalid schedule time: {e}"}
            )
    
    async def _handle_create_workflow(self, message: Message) -> Message:
        """Handle workflow creation request."""
        workflow_data = message.content.get("workflow_data", {})
        workflow_id = workflow_data.get("workflow_id", f"workflow_{len(self.workflows) + 1}")
        
        workflow = {
            "workflow_id": workflow_id,
            "name": workflow_data.get("name", "Untitled Workflow"),
            "description": workflow_data.get("description", ""),
            "steps": workflow_data.get("steps", []),
            "triggers": workflow_data.get("triggers", []),
            "created_at": datetime.now(),
            "enabled": workflow_data.get("enabled", True)
        }
        
        self.workflows[workflow_id] = workflow
        self.logger.info(f"Created workflow: {workflow_id} - {workflow['name']}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "workflow_created",
                "workflow_id": workflow_id,
                "workflow": workflow
            }
        )
    
    async def _execute_scheduled_task(self, task_id: str, delay: float):
        """Execute a scheduled task after the specified delay."""
        try:
            await asyncio.sleep(delay)
            
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.IN_PROGRESS
                
                # Execute the task (placeholder for actual task execution)
                self.logger.info(f"Executing scheduled task: {task_id}")
                
                # Simulate task execution
                await asyncio.sleep(1)
                
                task.status = TaskStatus.COMPLETED
                self.logger.info(f"Completed scheduled task: {task_id}")
                
                # Notify other agents about task completion
                await self.message_bus.broadcast(Message(
                    sender=self.agent_id,
                    content={
                        "action": "task_completed",
                        "task_id": task_id,
                        "task": self._task_to_dict(task)
                    }
                ))
            
        except asyncio.CancelledError:
            self.logger.info(f"Scheduled task {task_id} was cancelled")
        except Exception as e:
            self.logger.error(f"Error executing scheduled task {task_id}: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = TaskStatus.FAILED
    
    async def _monitor_scheduled_tasks(self):
        """Monitor and clean up completed scheduled tasks."""
        while self.status.is_running():
            try:
                # Clean up completed tasks
                completed_tasks = [
                    task_id for task_id, task in self.scheduled_tasks.items()
                    if task.done()
                ]
                
                for task_id in completed_tasks:
                    del self.scheduled_tasks[task_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in scheduled task monitor: {e}")
                await asyncio.sleep(60)
    
    def _filter_tasks(self, filters: Dict[str, Any]) -> List[Task]:
        """Filter tasks based on criteria."""
        tasks = list(self.tasks.values())
        
        if "status" in filters:
            status = TaskStatus(filters["status"])
            tasks = [t for t in tasks if t.status == status]
        
        if "priority" in filters:
            priority = TaskPriority(filters["priority"])
            tasks = [t for t in tasks if t.priority == priority]
        
        if "assigned_to" in filters:
            tasks = [t for t in tasks if t.assigned_to == filters["assigned_to"]]
        
        if "tags" in filters:
            required_tags = set(filters["tags"])
            tasks = [t for t in tasks if required_tags.issubset(set(t.tags))]
        
        if "due_before" in filters:
            due_before = datetime.fromisoformat(filters["due_before"])
            tasks = [t for t in tasks if t.due_date and t.due_date <= due_before]
        
        return tasks
    
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at.isoformat(),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "assigned_to": task.assigned_to,
            "dependencies": task.dependencies,
            "tags": task.tags,
            "metadata": task.metadata
        }
    
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for task agent."""
        try:
            action = message.content.get("action")
            
            if action == "create_task":
                return await self._handle_create_task(message)
            elif action == "update_task":
                return await self._handle_update_task(message)
            elif action == "delete_task":
                return await self._handle_delete_task(message)
            elif action == "list_tasks":
                return await self._handle_list_tasks(message)
            elif action == "schedule_task":
                return await self._handle_schedule_task(message)
            elif action == "create_workflow":
                return await self._handle_create_workflow(message)
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
        """Get task agent metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "total_tasks": len(self.tasks),
            "tasks_by_status": {
                status.value: len([t for t in self.tasks.values() if t.status == status])
                for status in TaskStatus
            },
            "tasks_by_priority": {
                priority.value: len([t for t in self.tasks.values() if t.priority == priority])
                for priority in TaskPriority
            },
            "scheduled_tasks": len(self.scheduled_tasks),
            "total_workflows": len(self.workflows)
        })
        return metrics
