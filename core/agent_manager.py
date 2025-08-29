"""
Agent Manager - Orchestrates and manages all agents in the framework
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Type, Set
from datetime import datetime
import json
import traceback
import uuid

from .base_agent import BaseAgent, AgentStatus
from .message_bus import MessageBus, Message
from .context_manager import ContextManager


class AgentManager:
    """
    Manages the lifecycle and orchestration of all agents in the framework.
    
    Features:
    - Agent registration and discovery
    - Dependency resolution and startup ordering
    - Health monitoring and recovery
    - Agent communication coordination
    - Configuration management
    - Performance monitoring
    """
    
    def __init__(self, message_bus: Optional[MessageBus] = None, context_manager: Optional[ContextManager] = None):
        self.logger = logging.getLogger("agent_manager")
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self.agent_dependencies: Dict[str, Set[str]] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self.agent_status: Dict[str, AgentStatus] = {}
        
        # Core services
        self.message_bus = message_bus or MessageBus()
        self.context_manager = context_manager or ContextManager()
        
        # Management state
        self.is_running = False
        self.startup_order: List[str] = []
        self.health_check_interval = 30  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.total_agents = 0
        self.running_agents = 0
        self.failed_agents = 0
        self.restart_count = 0
    
    async def start(self):
        """Start the agent manager and all registered agents"""
        if self.is_running:
            return
        
        try:
            self.logger.info("Starting agent manager")
            self.is_running = True
            
            # Start core services
            await self.message_bus.start()
            
            # Resolve dependencies and determine startup order
            self.startup_order = self._resolve_startup_order()
            self.logger.info(f"Startup order: {self.startup_order}")
            
            # Start agents in dependency order
            for agent_id in self.startup_order:
                await self._start_agent(agent_id)
            
            # Start health monitoring
            self.health_check_task = asyncio.create_task(self._health_monitor())
            
            self.logger.info("Agent manager started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start agent manager: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the agent manager and all agents"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("Stopping agent manager")
            self.is_running = False
            
            # Stop health monitoring
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Stop all agents in reverse startup order
            for agent_id in reversed(self.startup_order):
                await self._stop_agent(agent_id)
            
            # Stop core services
            await self.message_bus.stop()
            
            self.logger.info("Agent manager stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping agent manager: {e}")
    
    def register_agent(self, agent: BaseAgent, config: Dict[str, Any]):
        """
        Register an agent with the manager.
        
        Args:
            agent: The agent instance to register
            config: Configuration for the agent
        """
        agent_id = agent.agent_id
        
        if agent_id in self.agents:
            self.logger.warning(f"Agent {agent_id} already registered, replacing")
        
        # Store agent and configuration
        self.agents[agent_id] = agent
        self.agent_configs[agent_id] = config
        self.agent_dependencies[agent_id] = set(agent.dependencies)
        self.agent_capabilities[agent_id] = set(agent.capabilities)
        self.agent_status[agent_id] = AgentStatus.STOPPED
        
        # Set up agent with manager services
        agent.message_bus = self.message_bus
        agent.context_manager = self.context_manager
        
        # Set up callbacks
        agent.set_status_change_callback(
            lambda old_status, new_status: self._on_agent_status_change(agent_id, old_status, new_status)
        )
        
        self.total_agents += 1
        self.logger.info(f"Registered agent: {agent_id} with capabilities: {agent.capabilities}")
    
    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent from the manager.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if agent_id not in self.agents:
            self.logger.warning(f"Agent {agent_id} not found for unregistration")
            return
        
        # Stop the agent if running
        asyncio.create_task(self._stop_agent(agent_id))
        
        # Remove from tracking
        del self.agents[agent_id]
        del self.agent_configs[agent_id]
        del self.agent_dependencies[agent_id]
        del self.agent_capabilities[agent_id]
        del self.agent_status[agent_id]
        
        # Update startup order
        if agent_id in self.startup_order:
            self.startup_order.remove(agent_id)
        
        self.total_agents -= 1
        self.logger.info(f"Unregistered agent: {agent_id}")
    
    async def start_agent(self, agent_id: str) -> bool:
        """
        Start a specific agent.
        
        Args:
            agent_id: ID of the agent to start
            
        Returns:
            bool: True if started successfully
        """
        if agent_id not in self.agents:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        return await self._start_agent(agent_id)
    
    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop a specific agent.
        
        Args:
            agent_id: ID of the agent to stop
            
        Returns:
            bool: True if stopped successfully
        """
        if agent_id not in self.agents:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        return await self._stop_agent(agent_id)
    
    async def restart_agent(self, agent_id: str) -> bool:
        """
        Restart a specific agent.
        
        Args:
            agent_id: ID of the agent to restart
            
        Returns:
            bool: True if restarted successfully
        """
        if agent_id not in self.agents:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        self.logger.info(f"Restarting agent {agent_id}")
        
        # Stop the agent
        await self._stop_agent(agent_id)
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Start the agent
        success = await self._start_agent(agent_id)
        
        if success:
            self.restart_count += 1
        
        return success
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get the status of an agent"""
        return self.agent_status.get(agent_id)
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get all agents that have a specific capability"""
        return [
            agent_id for agent_id, capabilities in self.agent_capabilities.items()
            if capability in capabilities
        ]
    
    def get_agent_dependencies(self, agent_id: str) -> Set[str]:
        """Get the dependencies of an agent"""
        return self.agent_dependencies.get(agent_id, set())
    
    def get_agent_dependents(self, agent_id: str) -> Set[str]:
        """Get agents that depend on this agent"""
        dependents = set()
        for dep_agent_id, dependencies in self.agent_dependencies.items():
            if agent_id in dependencies:
                dependents.add(dep_agent_id)
        return dependents
    
    async def send_message_to_agent(self, target_agent: str, message_type: str, 
                                   data: Dict[str, Any], sender: str = "system") -> bool:
        """
        Send a message to a specific agent.
        
        Args:
            target_agent: ID of the target agent
            message_type: Type of message
            data: Message data
            sender: ID of the sender (default: "system")
            
        Returns:
            bool: True if message sent successfully
        """
        if target_agent not in self.agents:
            self.logger.error(f"Target agent {target_agent} not found")
            return False
        
        message = Message(
            id=str(uuid.uuid4()),
            sender=sender,
            recipient=target_agent,
            type=message_type,
            data=data,
            timestamp=datetime.now()
        )
        
        return await self.message_bus.send_message(message)
    
    async def broadcast_message(self, message_type: str, data: Dict[str, Any], 
                               sender: str = "system") -> bool:
        """
        Broadcast a message to all agents.
        
        Args:
            message_type: Type of message
            data: Message data
            sender: ID of the sender (default: "system")
            
        Returns:
            bool: True if message broadcast successfully
        """
        message = Message(
            id=str(uuid.uuid4()),
            sender=sender,
            recipient="*",
            type=message_type,
            data=data,
            timestamp=datetime.now()
        )
        
        return await self.message_bus.broadcast_message(message)
    
    def get_framework_status(self) -> Dict[str, Any]:
        """Get overall framework status"""
        running_count = sum(1 for status in self.agent_status.values() 
                           if status == AgentStatus.RUNNING)
        error_count = sum(1 for status in self.agent_status.values() 
                         if status == AgentStatus.ERROR)
        
        return {
            "manager_status": "running" if self.is_running else "stopped",
            "total_agents": self.total_agents,
            "running_agents": running_count,
            "stopped_agents": self.total_agents - running_count - error_count,
            "error_agents": error_count,
            "restart_count": self.restart_count,
            "message_bus_stats": self.message_bus.get_statistics(),
            "agents": {
                agent_id: {
                    "status": status.value,
                    "capabilities": list(self.agent_capabilities[agent_id]),
                    "dependencies": list(self.agent_dependencies[agent_id])
                }
                for agent_id, status in self.agent_status.items()
            }
        }
    
    def _resolve_startup_order(self) -> List[str]:
        """
        Resolve the startup order based on dependencies.
        Uses topological sorting to ensure dependencies are started first.
        """
        # Create a copy of dependencies for processing
        dependencies = {agent_id: deps.copy() for agent_id, deps in self.agent_dependencies.items()}
        
        # Find agents with no dependencies
        ready_agents = [agent_id for agent_id, deps in dependencies.items() if not deps]
        startup_order = []
        
        while ready_agents:
            # Take the first ready agent
            agent_id = ready_agents.pop(0)
            startup_order.append(agent_id)
            
            # Remove this agent from all dependency lists
            for other_agent_id, deps in dependencies.items():
                if agent_id in deps:
                    deps.remove(agent_id)
                    # If this agent now has no dependencies, add it to ready list
                    if not deps and other_agent_id not in startup_order:
                        ready_agents.append(other_agent_id)
        
        # Check for circular dependencies
        if len(startup_order) != len(self.agents):
            remaining = set(self.agents.keys()) - set(startup_order)
            self.logger.error(f"Circular dependency detected. Remaining agents: {remaining}")
            # Add remaining agents at the end (they may fail to start)
            startup_order.extend(list(remaining))
        
        return startup_order
    
    async def _start_agent(self, agent_id: str) -> bool:
        """Start a specific agent"""
        try:
            agent = self.agents[agent_id]
            config = self.agent_configs[agent_id]
            
            # Check if agent should auto-start
            if not config.get("auto_start", True):
                self.logger.info(f"Agent {agent_id} auto-start disabled")
                return True
            
            # Check dependencies
            for dep_id in self.agent_dependencies[agent_id]:
                if dep_id not in self.agents:
                    self.logger.error(f"Agent {agent_id} depends on {dep_id} which is not registered")
                    return False
                
                dep_status = self.agent_status[dep_id]
                if dep_status != AgentStatus.RUNNING:
                    self.logger.error(f"Agent {agent_id} depends on {dep_id} which is not running (status: {dep_status})")
                    return False
            
            # Start the agent
            success = await agent.start()
            if success:
                self.agent_status[agent_id] = AgentStatus.RUNNING
                self.running_agents += 1
                self.logger.info(f"Agent {agent_id} started successfully")
            else:
                self.agent_status[agent_id] = AgentStatus.ERROR
                self.failed_agents += 1
                self.logger.error(f"Failed to start agent {agent_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error starting agent {agent_id}: {e}")
            self.agent_status[agent_id] = AgentStatus.ERROR
            self.failed_agents += 1
            return False
    
    async def _stop_agent(self, agent_id: str) -> bool:
        """Stop a specific agent"""
        try:
            agent = self.agents[agent_id]
            
            # Stop the agent
            success = await agent.stop()
            if success:
                self.agent_status[agent_id] = AgentStatus.STOPPED
                if self.agent_status[agent_id] == AgentStatus.RUNNING:
                    self.running_agents -= 1
                elif self.agent_status[agent_id] == AgentStatus.ERROR:
                    self.failed_agents -= 1
                self.logger.info(f"Agent {agent_id} stopped successfully")
            else:
                self.logger.error(f"Failed to stop agent {agent_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error stopping agent {agent_id}: {e}")
            return False
    
    def _on_agent_status_change(self, agent_id: str, old_status: AgentStatus, new_status: AgentStatus):
        """Handle agent status changes"""
        self.agent_status[agent_id] = new_status
        
        # Update counters
        if old_status == AgentStatus.RUNNING and new_status != AgentStatus.RUNNING:
            self.running_agents -= 1
        elif old_status != AgentStatus.RUNNING and new_status == AgentStatus.RUNNING:
            self.running_agents += 1
        
        if old_status == AgentStatus.ERROR and new_status != AgentStatus.ERROR:
            self.failed_agents -= 1
        elif old_status != AgentStatus.ERROR and new_status == AgentStatus.ERROR:
            self.failed_agents += 1
        
        self.logger.info(f"Agent {agent_id} status changed: {old_status.value} -> {new_status.value}")
    
    async def _health_monitor(self):
        """Monitor agent health and restart failed agents"""
        while self.is_running:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Check each agent's health
                for agent_id, agent in self.agents.items():
                    config = self.agent_configs[agent_id]
                    
                    # Skip if auto-restart is disabled
                    if not config.get("auto_restart", True):
                        continue
                    
                    # Check if agent is in error state
                    if self.agent_status[agent_id] == AgentStatus.ERROR:
                        self.logger.warning(f"Agent {agent_id} is in error state, attempting restart")
                        await self.restart_agent(agent_id)
                    
                    # Check if agent has been running for too long without activity
                    health = agent.get_health()
                    if health.get("last_activity"):
                        last_activity = datetime.fromisoformat(health["last_activity"])
                        max_idle_time = config.get("max_idle_time", 300)  # 5 minutes default
                        
                        if (datetime.now() - last_activity).total_seconds() > max_idle_time:
                            self.logger.warning(f"Agent {agent_id} has been idle for too long, restarting")
                            await self.restart_agent(agent_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
    
    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific agent"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        return agent.get_health()
    
    def get_all_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all agents"""
        return {
            agent_id: agent.get_health()
            for agent_id, agent in self.agents.items()
        }

