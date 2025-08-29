"""
Base Agent Class - Foundation for all agents in the framework
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

from .message_bus import Message, MessageBus
from .context_manager import ContextManager


class AgentStatus(Enum):
    """Agent status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


class AgentPriority(Enum):
    """Agent priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    messages_processed: int = 0
    messages_failed: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    last_activity: Optional[datetime] = None
    uptime: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


class BaseAgent(ABC):
    """
    Base class for all agents in the framework.
    
    Provides common functionality including:
    - Message processing
    - Status management
    - Metrics tracking
    - Error handling
    - Lifecycle management
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration dictionary for the agent
        """
        self.agent_id = agent_id
        self.config = config
        self.status = AgentStatus.STOPPED
        self.priority = AgentPriority.NORMAL
        self.capabilities: List[str] = []
        self.dependencies: List[str] = []
        
        # Initialize components
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.message_bus: Optional[MessageBus] = None
        self.context_manager: Optional[ContextManager] = None
        
        # Metrics and monitoring
        self.metrics = AgentMetrics()
        self.start_time: Optional[datetime] = None
        self.error_count = 0
        self.max_retries = config.get("max_retries", 3)
        
        # Message processing
        self.message_queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        
        # Callbacks
        self.on_message_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        self.on_status_change_callback: Optional[Callable] = None
        
        # Initialize agent-specific components
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize agent-specific components. Override in subclasses."""
        pass
    
    async def start(self) -> bool:
        """
        Start the agent.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting agent {self.agent_id}")
            self._set_status(AgentStatus.STARTING)
            
            # Initialize dependencies
            if not await self._initialize_dependencies():
                raise Exception("Failed to initialize dependencies")
            
            # Start message processing
            self.processing_task = asyncio.create_task(self._message_processor())
            
            # Call agent-specific startup
            await self._on_start()
            
            self.start_time = datetime.now()
            self._set_status(AgentStatus.RUNNING)
            self.logger.info(f"Agent {self.agent_id} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start agent {self.agent_id}: {e}")
            self._set_status(AgentStatus.ERROR)
            return False
    
    async def stop(self) -> bool:
        """
        Stop the agent.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            self.logger.info(f"Stopping agent {self.agent_id}")
            self._set_status(AgentStatus.SHUTTING_DOWN)
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Stop message processing
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
            
            # Call agent-specific shutdown
            await self._on_stop()
            
            self._set_status(AgentStatus.STOPPED)
            self.logger.info(f"Agent {self.agent_id} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop agent {self.agent_id}: {e}")
            return False
    
    async def pause(self) -> bool:
        """Pause the agent."""
        try:
            self._set_status(AgentStatus.PAUSED)
            self.logger.info(f"Agent {self.agent_id} paused")
            return True
        except Exception as e:
            self.logger.error(f"Failed to pause agent {self.agent_id}: {e}")
            return False
    
    async def resume(self) -> bool:
        """Resume the agent."""
        try:
            if self.status == AgentStatus.PAUSED:
                self._set_status(AgentStatus.RUNNING)
                self.logger.info(f"Agent {self.agent_id} resumed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to resume agent {self.agent_id}: {e}")
            return False
    
    async def send_message(self, target_agent: str, message_type: str, data: Dict[str, Any], 
                          priority: AgentPriority = AgentPriority.NORMAL) -> bool:
        """
        Send a message to another agent.
        
        Args:
            target_agent: ID of the target agent
            message_type: Type of message
            data: Message data
            priority: Message priority
            
        Returns:
            bool: True if message sent successfully
        """
        if not self.message_bus:
            self.logger.error("Message bus not initialized")
            return False
        
        message = Message(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            recipient=target_agent,
            type=message_type,
            data=data,
            priority=priority,
            timestamp=datetime.now()
        )
        
        return await self.message_bus.send_message(message)
    
    async def broadcast_message(self, message_type: str, data: Dict[str, Any], 
                               priority: AgentPriority = AgentPriority.NORMAL) -> bool:
        """
        Broadcast a message to all agents.
        
        Args:
            message_type: Type of message
            data: Message data
            priority: Message priority
            
        Returns:
            bool: True if message broadcast successfully
        """
        if not self.message_bus:
            self.logger.error("Message bus not initialized")
            return False
        
        message = Message(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            recipient="*",  # Broadcast to all
            type=message_type,
            data=data,
            priority=priority,
            timestamp=datetime.now()
        )
        
        return await self.message_bus.broadcast_message(message)
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """
        Process an incoming message. Override in subclasses.
        
        Args:
            message: The message to process
            
        Returns:
            Dict containing the response
        """
        try:
            start_time = time.time()
            
            # Update metrics
            self.metrics.last_activity = datetime.now()
            
            # Process the message
            result = await self._process_message_impl(message)
            
            # Update processing metrics
            processing_time = time.time() - start_time
            self.metrics.messages_processed += 1
            self.metrics.total_processing_time += processing_time
            self.metrics.average_processing_time = (
                self.metrics.total_processing_time / self.metrics.messages_processed
            )
            
            # Call message callback if set
            if self.on_message_callback:
                await self.on_message_callback(message, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.metrics.messages_failed += 1
            self.error_count += 1
            
            # Call error callback if set
            if self.on_error_callback:
                await self.on_error_callback(message, e)
            
            return {"error": str(e), "success": False}
    
    @abstractmethod
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """
        Implementation of message processing. Must be implemented by subclasses.
        
        Args:
            message: The message to process
            
        Returns:
            Dict containing the response
        """
        pass
    
    async def _message_processor(self):
        """Background task for processing messages from the queue."""
        while not self.shutdown_event.is_set():
            try:
                # Wait for message with timeout
                try:
                    message = await asyncio.wait_for(
                        self.message_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process message if agent is running
                if self.status == AgentStatus.RUNNING:
                    await self.process_message(message)
                
                # Mark task as done
                self.message_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in message processor: {e}")
    
    async def _initialize_dependencies(self) -> bool:
        """Initialize agent dependencies."""
        try:
            # Initialize message bus if not set
            if not self.message_bus:
                self.message_bus = MessageBus()
                await self.message_bus.start()
            
            # Initialize context manager if not set
            if not self.context_manager:
                self.context_manager = ContextManager()
            
            # Subscribe to messages
            await self.message_bus.subscribe(self.agent_id, self._handle_incoming_message)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize dependencies: {e}")
            return False
    
    async def _handle_incoming_message(self, message: Message):
        """Handle incoming message by adding it to the queue."""
        await self.message_queue.put(message)
    
    def _set_status(self, status: AgentStatus):
        """Set agent status and notify callbacks."""
        old_status = self.status
        self.status = status
        
        # Call status change callback if set
        if self.on_status_change_callback:
            asyncio.create_task(self.on_status_change_callback(old_status, status))
    
    async def _on_start(self):
        """Called when agent starts. Override in subclasses."""
        pass
    
    async def _on_stop(self):
        """Called when agent stops. Override in subclasses."""
        pass
    
    def get_health(self) -> Dict[str, Any]:
        """Get agent health information."""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "uptime": uptime,
            "error_count": self.error_count,
            "capabilities": self.capabilities,
            "metrics": {
                "messages_processed": self.metrics.messages_processed,
                "messages_failed": self.metrics.messages_failed,
                "average_processing_time": self.metrics.average_processing_time,
                "last_activity": self.metrics.last_activity.isoformat() if self.metrics.last_activity else None
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return {
            "agent_id": self.agent_id,
            "config": self.config,
            "capabilities": self.capabilities,
            "dependencies": self.dependencies,
            "priority": self.priority.value
        }
    
    def set_message_callback(self, callback: Callable):
        """Set callback for message processing."""
        self.on_message_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """Set callback for error handling."""
        self.on_error_callback = callback
    
    def set_status_change_callback(self, callback: Callable):
        """Set callback for status changes."""
        self.on_status_change_callback = callback

