#!/usr/bin/env python3
"""
Agentic Framework - Main Entry Point

This is the main entry point for the agentic framework that initializes
and manages all agents in the system.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, List, Any
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings
from core.agent_manager import AgentManager
from core.message_bus import MessageBus
from core.context_manager import ContextManager
from agents.chat_agent import ChatAgent
from agents.task_agent import TaskAgent
from agents.email_agent import EmailAgent
from agents.calendar_agent import CalendarAgent
from agents.data_agent import DataAgent
from agents.weather_agent import WeatherAgent
from agents.news_agent import NewsAgent
from agents.translation_agent import TranslationAgent


class AgenticFramework:
    """
    Main framework class that orchestrates all agents and services.
    """
    
    def __init__(self, config_file: str = None):
        self.settings = Settings(config_file)
        self.logger = logging.getLogger(__name__)
        
        # Initialize core services
        self.message_bus = MessageBus()
        self.context_manager = ContextManager()
        self.agent_manager = AgentManager(
            message_bus=self.message_bus,
            context_manager=self.context_manager
        )
        
        # Framework state
        self.running = False
        self.agents: Dict[str, Any] = {}
        
    async def initialize(self):
        """Initialize the framework and all agents."""
        self.logger.info("Initializing Agentic Framework...")
        
        try:
            # Initialize core services
            await self.message_bus.start()
            await self.context_manager.start()
            await self.agent_manager.start()
            
            # Initialize agents
            await self._initialize_agents()
            
            # Set up global context
            await self._setup_global_context()
            
            self.logger.info("Framework initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize framework: {e}")
            raise
    
    async def _initialize_agents(self):
        """Initialize all agents in the system."""
        self.logger.info("Initializing agents...")
        
        # Create agent instances
        agents_to_create = [
            ("chat_agent", ChatAgent),
            ("task_agent", TaskAgent),
            ("email_agent", EmailAgent),
            ("calendar_agent", CalendarAgent),
            ("data_agent", DataAgent),
            ("weather_agent", WeatherAgent),
            ("news_agent", NewsAgent),
            ("translation_agent", TranslationAgent),
        ]
        
        for agent_id, agent_class in agents_to_create:
            try:
                # Create config for the agent
                config = {
                    "agent_id": agent_id,
                    "enabled": True,
                    "auto_start": True,
                    "max_retries": 3,
                    "health_check_interval": 30
                }
                
                agent = agent_class(agent_id, config)
                self.agents[agent_id] = agent
                self.agent_manager.register_agent(agent, config)
                self.logger.info(f"Registered agent: {agent_id}")
            except Exception as e:
                self.logger.error(f"Failed to register agent {agent_id}: {e}")
        
        # Start all agents
        await self.agent_manager.start()
        self.logger.info(f"Started {len(self.agents)} agents")
    
    async def _setup_global_context(self):
        """Set up global context and configuration."""
        self.logger.info("Setting up global context...")
        
        try:
            # Add framework configuration to global context
            self.context_manager.set("framework_config", {
                "version": "1.0.0",
                "agents_count": len(self.agents),
                "startup_time": asyncio.get_event_loop().time()
            }, scope="global")
            
            # Add agent list to global context
            agent_list = list(self.agents.keys())
            self.context_manager.set("active_agents", agent_list, scope="global")
            
            # Add configuration settings to global context
            self.context_manager.set("settings", {
                "database": self.settings.database.__dict__,
                "logging": self.settings.logging.__dict__,
                "api": self.settings.api.__dict__,
                "security": self.settings.security.__dict__,
                "monitoring": self.settings.monitoring.__dict__
            }, scope="global")
        except Exception as e:
            self.logger.error(f"Error setting up global context: {e}")
    
    async def start(self):
        """Start the framework."""
        if self.running:
            self.logger.warning("Framework is already running")
            return
        
        try:
            await self.initialize()
            self.running = True
            self.logger.info("Agentic Framework started successfully")
            
            # Keep the framework running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Framework error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the framework and all agents."""
        if not self.running:
            return
        
        self.logger.info("Stopping Agentic Framework...")
        self.running = False
        
        try:
            # Stop core services
            await self.agent_manager.stop()
            await self.context_manager.stop()
            await self.message_bus.stop()
            
            self.logger.info("Framework stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping framework: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the framework."""
        agent_statuses = {}
        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = {
                "status": agent.status.value,
                "metrics": agent.get_metrics()
            }
        
        return {
            "framework_running": self.running,
            "agents_count": len(self.agents),
            "agent_statuses": agent_statuses,
            "message_bus_status": self.message_bus.get_status(),
            "context_manager_status": self.context_manager.get_status(),
            "agent_manager_status": self.agent_manager.get_status()
        }
    
    async def send_message(self, sender: str, recipient: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message between agents."""
        try:
            message = self.message_bus.create_message(sender, recipient, content)
            response = await self.message_bus.send_message(message)
            return response.content if response else {"error": "No response received"}
        except Exception as e:
            return {"error": str(e)}
    
    async def broadcast_message(self, sender: str, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Broadcast a message to all agents."""
        try:
            message = self.message_bus.create_message(sender, "broadcast", content)
            responses = await self.message_bus.broadcast(message)
            return [response.content for response in responses]
        except Exception as e:
            return [{"error": str(e)}]


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('agentic_framework.log')
        ]
    )


def setup_signal_handlers(framework: AgenticFramework):
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        asyncio.create_task(framework.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Agentic Framework...")
    
    # Create framework instance
    framework = AgenticFramework()
    
    # Set up signal handlers
    setup_signal_handlers(framework)
    
    try:
        # Start the framework
        await framework.start()
    except Exception as e:
        logger.error(f"Framework startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the framework
    asyncio.run(main())
