"""
Message Bus - Inter-agent communication system
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Message structure for inter-agent communication"""
    id: str
    sender: str
    recipient: str  # "*" for broadcast
    type: str
    data: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.type,
            "data": self.data,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "ttl": self.ttl
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            id=data["id"],
            sender=data["sender"],
            recipient=data["recipient"],
            type=data["type"],
            data=data["data"],
            priority=MessagePriority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            ttl=data.get("ttl")
        )


class MessageBus:
    """
    Message bus for inter-agent communication.
    
    Features:
    - Direct messaging between agents
    - Broadcast messaging to all agents
    - Message routing and filtering
    - Priority-based message processing
    - Message persistence and replay
    - Dead letter queue for failed messages
    """
    
    def __init__(self):
        self.logger = logging.getLogger("message_bus")
        self.subscribers: Dict[str, Callable] = {}
        self.broadcast_subscribers: Set[str] = set()
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.dead_letter_queue: asyncio.Queue = asyncio.Queue()
        self.message_history: List[Message] = []
        self.max_history_size = 1000
        self.is_running = False
        
        # Statistics
        self.messages_sent = 0
        self.messages_delivered = 0
        self.messages_failed = 0
        self.broadcasts_sent = 0
    
    async def start(self):
        """Start the message bus"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Message bus started")
        
        # Start dead letter queue processor
        asyncio.create_task(self._process_dead_letter_queue())
    
    async def stop(self):
        """Stop the message bus"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all processing tasks
        for task in self.processing_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks.values(), return_exceptions=True)
        
        self.logger.info("Message bus stopped")
    
    async def subscribe(self, agent_id: str, callback: Callable):
        """
        Subscribe an agent to receive messages.
        
        Args:
            agent_id: ID of the agent subscribing
            callback: Function to call when message is received
        """
        self.subscribers[agent_id] = callback
        self.message_queues[agent_id] = asyncio.Queue()
        
        # Start message processor for this agent
        self.processing_tasks[agent_id] = asyncio.create_task(
            self._process_agent_messages(agent_id)
        )
        
        self.logger.info(f"Agent {agent_id} subscribed to message bus")
    
    async def unsubscribe(self, agent_id: str):
        """
        Unsubscribe an agent from receiving messages.
        
        Args:
            agent_id: ID of the agent to unsubscribe
        """
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
        
        if agent_id in self.message_queues:
            del self.message_queues[agent_id]
        
        if agent_id in self.processing_tasks:
            self.processing_tasks[agent_id].cancel()
            del self.processing_tasks[agent_id]
        
        self.broadcast_subscribers.discard(agent_id)
        self.logger.info(f"Agent {agent_id} unsubscribed from message bus")
    
    async def subscribe_to_broadcasts(self, agent_id: str):
        """Subscribe an agent to receive broadcast messages"""
        self.broadcast_subscribers.add(agent_id)
        self.logger.info(f"Agent {agent_id} subscribed to broadcasts")
    
    async def unsubscribe_from_broadcasts(self, agent_id: str):
        """Unsubscribe an agent from broadcast messages"""
        self.broadcast_subscribers.discard(agent_id)
        self.logger.info(f"Agent {agent_id} unsubscribed from broadcasts")
    
    async def send_message(self, message: Message) -> bool:
        """
        Send a message to a specific agent.
        
        Args:
            message: The message to send
            
        Returns:
            bool: True if message was queued successfully
        """
        try:
            # Check if message has expired
            if message.ttl and (datetime.now() - message.timestamp).total_seconds() > message.ttl:
                self.logger.warning(f"Message {message.id} has expired")
                return False
            
            # Add to message history
            self._add_to_history(message)
            
            # Route message to recipient
            if message.recipient in self.message_queues:
                await self.message_queues[message.recipient].put(message)
                self.messages_sent += 1
                self.logger.debug(f"Message {message.id} sent to {message.recipient}")
                return True
            else:
                # Recipient not found, send to dead letter queue
                await self.dead_letter_queue.put(message)
                self.messages_failed += 1
                self.logger.warning(f"Recipient {message.recipient} not found for message {message.id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending message {message.id}: {e}")
            self.messages_failed += 1
            return False
    
    async def broadcast_message(self, message: Message) -> bool:
        """
        Broadcast a message to all subscribed agents.
        
        Args:
            message: The message to broadcast
            
        Returns:
            bool: True if message was broadcast successfully
        """
        try:
            # Check if message has expired
            if message.ttl and (datetime.now() - message.timestamp).total_seconds() > message.ttl:
                self.logger.warning(f"Broadcast message {message.id} has expired")
                return False
            
            # Add to message history
            self._add_to_history(message)
            
            # Send to all broadcast subscribers
            sent_count = 0
            for agent_id in self.broadcast_subscribers:
                if agent_id in self.message_queues:
                    await self.message_queues[agent_id].put(message)
                    sent_count += 1
            
            self.broadcasts_sent += 1
            self.messages_sent += sent_count
            self.logger.debug(f"Broadcast message {message.id} sent to {sent_count} agents")
            return sent_count > 0
            
        except Exception as e:
            self.logger.error(f"Error broadcasting message {message.id}: {e}")
            self.messages_failed += 1
            return False
    
    async def send_message_with_reply(self, message: Message, timeout: float = 30.0) -> Optional[Message]:
        """
        Send a message and wait for a reply.
        
        Args:
            message: The message to send
            timeout: Timeout in seconds for waiting for reply
            
        Returns:
            Optional[Message]: The reply message if received within timeout
        """
        # Generate correlation ID for this request
        correlation_id = str(uuid.uuid4())
        message.correlation_id = correlation_id
        
        # Create a future to wait for the reply
        reply_future = asyncio.Future()
        
        # Store the future to be resolved when reply is received
        self._pending_replies[correlation_id] = reply_future
        
        try:
            # Send the message
            success = await self.send_message(message)
            if not success:
                return None
            
            # Wait for reply
            reply = await asyncio.wait_for(reply_future, timeout=timeout)
            return reply
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for reply to message {message.id}")
            return None
        except Exception as e:
            self.logger.error(f"Error in send_message_with_reply: {e}")
            return None
        finally:
            # Clean up
            self._pending_replies.pop(correlation_id, None)
    
    async def _process_agent_messages(self, agent_id: str):
        """Process messages for a specific agent"""
        queue = self.message_queues[agent_id]
        callback = self.subscribers[agent_id]
        
        while self.is_running:
            try:
                # Wait for message with timeout
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process the message
                try:
                    await callback(message)
                    self.messages_delivered += 1
                    self.logger.debug(f"Message {message.id} delivered to {agent_id}")
                except Exception as e:
                    self.logger.error(f"Error processing message {message.id} for {agent_id}: {e}")
                    self.messages_failed += 1
                    # Send to dead letter queue
                    await self.dead_letter_queue.put(message)
                
                # Mark task as done
                queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in message processor for {agent_id}: {e}")
    
    async def _process_dead_letter_queue(self):
        """Process messages in the dead letter queue"""
        while self.is_running:
            try:
                # Wait for message with timeout
                try:
                    message = await asyncio.wait_for(self.dead_letter_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Log dead letter message
                self.logger.warning(f"Dead letter message: {message.id} from {message.sender} to {message.recipient}")
                
                # Mark task as done
                self.dead_letter_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in dead letter processor: {e}")
    
    def _add_to_history(self, message: Message):
        """Add message to history, maintaining max size"""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history_size:
            self.message_history.pop(0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        return {
            "messages_sent": self.messages_sent,
            "messages_delivered": self.messages_delivered,
            "messages_failed": self.messages_failed,
            "broadcasts_sent": self.broadcasts_sent,
            "active_subscribers": len(self.subscribers),
            "broadcast_subscribers": len(self.broadcast_subscribers),
            "dead_letter_queue_size": self.dead_letter_queue.qsize(),
            "message_history_size": len(self.message_history)
        }
    
    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message history"""
        recent_messages = self.message_history[-limit:]
        return [msg.to_dict() for msg in recent_messages]
    
    async def clear_dead_letter_queue(self):
        """Clear the dead letter queue"""
        while not self.dead_letter_queue.empty():
            try:
                self.dead_letter_queue.get_nowait()
                self.dead_letter_queue.task_done()
            except asyncio.QueueEmpty:
                break
    
    def is_agent_subscribed(self, agent_id: str) -> bool:
        """Check if an agent is subscribed"""
        return agent_id in self.subscribers
    
    def get_subscribed_agents(self) -> List[str]:
        """Get list of subscribed agent IDs"""
        return list(self.subscribers.keys())
    
    def get_broadcast_subscribers(self) -> List[str]:
        """Get list of broadcast subscriber IDs"""
        return list(self.broadcast_subscribers)





