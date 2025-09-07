#!/usr/bin/env python3
"""
Agentic Framework Demo

This script demonstrates the capabilities of the agentic framework by:
1. Starting all available agents
2. Testing inter-agent communication
3. Demonstrating various agent functionalities
4. Showing real-time agent interactions

Run this script to see the framework in action!
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Import the framework components
from core.agent_manager import AgentManager
from core.message_bus import Message, MessagePriority
from core.context_manager import ContextScope
from config.settings import get_settings

# Import all agents
from agents.chat_agent import ChatAgent
from agents.task_agent import TaskAgent
from agents.email_agent import EmailAgent
from agents.calendar_agent import CalendarAgent
from agents.data_agent import DataAgent
from agents.weather_agent import WeatherAgent
from agents.news_agent import NewsAgent
from agents.translation_agent import TranslationAgent


class AgenticFrameworkDemo:
    """Demo class for showcasing the agentic framework capabilities."""
    
    def __init__(self):
        self.agent_manager = AgentManager()
        self.settings = get_settings()
        self.logger = logging.getLogger("demo")
        
        # Demo data
        self.demo_data = {
            "user_id": "demo_user",
            "session_id": "demo_session",
            "demo_start_time": datetime.now()
        }
    
    async def setup_logging(self):
        """Setup logging for the demo."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('demo.log')
            ]
        )
        self.logger.info("Demo logging setup complete")
    
    async def initialize_agents(self):
        """Initialize and start all agents."""
        self.logger.info("Initializing agents...")
        
        # Create agent instances
        agents = [
            ChatAgent("chat_agent", {"max_history_length": 20}),
            TaskAgent("task_agent", {"max_concurrent_tasks": 5}),
            EmailAgent("email_agent", {"smtp_server": "localhost"}),
            CalendarAgent("calendar_agent", {"default_calendar": "demo"}),
            DataAgent("data_agent", {"max_data_size_mb": 10}),
            WeatherAgent("weather_agent", {"default_location": "New York"}),
            NewsAgent("news_agent", {"update_interval": 60}),
            TranslationAgent("translation_agent", {"supported_languages": ["en", "es", "fr"]})
        ]
        
        # Register and start agents
        for agent in agents:
            await self.agent_manager.register_agent(agent)
            await agent.start()
            self.logger.info(f"Started agent: {agent.agent_id}")
        
        # Wait a moment for agents to fully initialize
        await asyncio.sleep(2)
        self.logger.info("All agents initialized successfully!")
    
    async def demo_chat_agent(self):
        """Demonstrate chat agent capabilities."""
        self.logger.info("\n=== CHAT AGENT DEMO ===")
        
        # Test basic conversation
        messages = [
            "Hello! How are you today?",
            "What can you help me with?",
            "Tell me a joke",
            "What's the weather like?",
            "Thank you for your help!"
        ]
        
        for message in messages:
            self.logger.info(f"User: {message}")
            
            # Send message to chat agent
            response = await self.agent_manager.send_message(
                "chat_agent",
                "chat_message",
                {
                    "user_id": self.demo_data["user_id"],
                    "session_id": self.demo_data["session_id"],
                    "message": message
                }
            )
            
            if response and response.get("success"):
                self.logger.info(f"Chat Agent: {response.get('response', 'No response')}")
            else:
                self.logger.error(f"Chat agent error: {response.get('error', 'Unknown error')}")
            
            await asyncio.sleep(1)  # Pause between messages
    
    async def demo_task_agent(self):
        """Demonstrate task agent capabilities."""
        self.logger.info("\n=== TASK AGENT DEMO ===")
        
        # Create some sample tasks
        tasks = [
            {
                "title": "Review project proposal",
                "description": "Review the Q4 project proposal and provide feedback",
                "priority": "high",
                "due_date": (datetime.now() + timedelta(days=3)).isoformat()
            },
            {
                "title": "Update documentation",
                "description": "Update API documentation for new endpoints",
                "priority": "medium",
                "due_date": (datetime.now() + timedelta(days=7)).isoformat()
            },
            {
                "title": "Team meeting preparation",
                "description": "Prepare agenda for weekly team meeting",
                "priority": "low",
                "due_date": (datetime.now() + timedelta(days=1)).isoformat()
            }
        ]
        
        for i, task_data in enumerate(tasks, 1):
            self.logger.info(f"Creating task {i}: {task_data['title']}")
            
            response = await self.agent_manager.send_message(
                "task_agent",
                "create_task",
                {"task_data": task_data}
            )
            
            if response and response.get("success"):
                task_id = response.get("task_id")
                self.logger.info(f"Task created with ID: {task_id}")
            else:
                self.logger.error(f"Task creation failed: {response.get('error', 'Unknown error')}")
        
        # List all tasks
        self.logger.info("Listing all tasks...")
        response = await self.agent_manager.send_message(
            "task_agent",
            "list_tasks",
            {"filters": {}}
        )
        
        if response and response.get("success"):
            tasks = response.get("tasks", [])
            self.logger.info(f"Found {len(tasks)} tasks:")
            for task in tasks:
                self.logger.info(f"  - {task['title']} (Status: {task['status']}, Priority: {task['priority']})")
    
    async def demo_calendar_agent(self):
        """Demonstrate calendar agent capabilities."""
        self.logger.info("\n=== CALENDAR AGENT DEMO ===")
        
        # Create a sample event
        event_data = {
            "title": "Demo Meeting",
            "description": "Demonstration of the agentic framework",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "end_time": (datetime.now() + timedelta(hours=2)).isoformat(),
            "location": "Virtual Meeting Room",
            "attendees": ["demo_user", "admin"],
            "reminder_minutes": 15
        }
        
        self.logger.info("Creating calendar event...")
        response = await self.agent_manager.send_message(
            "calendar_agent",
            "create_event",
            {"event_data": event_data}
        )
        
        if response and response.get("success"):
            event_id = response.get("event_id")
            self.logger.info(f"Event created with ID: {event_id}")
        else:
            self.logger.error(f"Event creation failed: {response.get('error', 'Unknown error')}")
        
        # List events
        self.logger.info("Listing calendar events...")
        response = await self.agent_manager.send_message(
            "calendar_agent",
            "list_events",
            {"calendar_id": "default", "filters": {}}
        )
        
        if response and response.get("success"):
            events = response.get("events", [])
            self.logger.info(f"Found {len(events)} events:")
            for event in events:
                self.logger.info(f"  - {event['title']} at {event['start_time']}")
    
    async def demo_weather_agent(self):
        """Demonstrate weather agent capabilities."""
        self.logger.info("\n=== WEATHER AGENT DEMO ===")
        
        # Get current weather for New York
        self.logger.info("Getting current weather for New York...")
        response = await self.agent_manager.send_message(
            "weather_agent",
            "get_current_weather",
            {"location_id": "new_york"}
        )
        
        if response and response.get("success"):
            weather = response.get("weather", {})
            self.logger.info(f"Weather in {weather.get('location', 'Unknown')}:")
            self.logger.info(f"  Temperature: {weather.get('temperature', 'N/A')}°C")
            self.logger.info(f"  Condition: {weather.get('condition', 'N/A')}")
            self.logger.info(f"  Humidity: {weather.get('humidity', 'N/A')}%")
        else:
            self.logger.error(f"Weather request failed: {response.get('error', 'Unknown error')}")
        
        # Get weather forecast
        self.logger.info("Getting 3-day weather forecast...")
        response = await self.agent_manager.send_message(
            "weather_agent",
            "get_forecast",
            {"location_id": "new_york", "days": 3}
        )
        
        if response and response.get("success"):
            forecast = response.get("forecast", [])
            self.logger.info("3-day forecast:")
            for day in forecast:
                self.logger.info(f"  {day['date']}: {day['condition']} (High: {day['high_temp']}°C, Low: {day['low_temp']}°C)")
    
    async def demo_translation_agent(self):
        """Demonstrate translation agent capabilities."""
        self.logger.info("\n=== TRANSLATION AGENT DEMO ===")
        
        # Test translations
        translations = [
            {"text": "Hello, how are you?", "target_language": "es"},
            {"text": "Good morning", "target_language": "fr"},
            {"text": "Thank you very much", "target_language": "de"}
        ]
        
        for translation in translations:
            self.logger.info(f"Translating: '{translation['text']}' to {translation['target_language']}")
            
            response = await self.agent_manager.send_message(
                "translation_agent",
                "translate_text",
                {
                    "source_text": translation["text"],
                    "target_language": translation["target_language"]
                }
            )
            
            if response and response.get("success"):
                result = response.get("result", {})
                translated_text = result.get("translated_text", "Translation failed")
                confidence = result.get("confidence_score", 0)
                self.logger.info(f"  Result: '{translated_text}' (Confidence: {confidence:.2f})")
            else:
                self.logger.error(f"Translation failed: {response.get('error', 'Unknown error')}")
    
    async def demo_data_agent(self):
        """Demonstrate data agent capabilities."""
        self.logger.info("\n=== DATA AGENT DEMO ===")
        
        # Add a data source
        source_data = {
            "name": "Demo Data Source",
            "type": "file",
            "location": "demo_data.json",
            "format": "json"
        }
        
        self.logger.info("Adding data source...")
        response = await self.agent_manager.send_message(
            "data_agent",
            "add_source",
            {"source_data": source_data}
        )
        
        if response and response.get("success"):
            source_id = response.get("source_id")
            self.logger.info(f"Data source added with ID: {source_id}")
            
            # Write some sample data
            sample_data = {
                "users": [
                    {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
                    {"id": 2, "name": "Bob", "age": 25, "city": "London"},
                    {"id": 3, "name": "Charlie", "age": 35, "city": "Tokyo"}
                ],
                "metadata": {"created": datetime.now().isoformat()}
            }
            
            self.logger.info("Writing sample data...")
            response = await self.agent_manager.send_message(
                "data_agent",
                "write_data",
                {
                    "source_id": source_id,
                    "data": sample_data,
                    "operation": "write"
                }
            )
            
            if response and response.get("success"):
                self.logger.info("Sample data written successfully")
                
                # Analyze the data
                self.logger.info("Analyzing data...")
                response = await self.agent_manager.send_message(
                    "data_agent",
                    "analyze_data",
                    {
                        "source_id": source_id,
                        "analysis_type": "basic"
                    }
                )
                
                if response and response.get("success"):
                    analysis = response.get("result", {})
                    self.logger.info(f"Data analysis result: {analysis}")
        else:
            self.logger.error(f"Data source creation failed: {response.get('error', 'Unknown error')}")
    
    async def demo_news_agent(self):
        """Demonstrate news agent capabilities."""
        self.logger.info("\n=== NEWS AGENT DEMO ===")
        
        # Get latest news
        self.logger.info("Getting latest news...")
        response = await self.agent_manager.send_message(
            "news_agent",
            "get_latest_news",
            {"limit": 3}
        )
        
        if response and response.get("success"):
            articles = response.get("articles", [])
            self.logger.info(f"Found {len(articles)} articles:")
            for article in articles:
                self.logger.info(f"  - {article['title']} (Source: {article['source']})")
        else:
            self.logger.error(f"News request failed: {response.get('error', 'Unknown error')}")
        
        # Get trending topics
        self.logger.info("Getting trending topics...")
        response = await self.agent_manager.send_message(
            "news_agent",
            "get_trending_topics",
            {"limit": 5}
        )
        
        if response and response.get("success"):
            topics = response.get("topics", [])
            self.logger.info("Trending topics:")
            for topic in topics:
                self.logger.info(f"  - {topic['topic']} (Count: {topic['count']})")
    
    async def demo_inter_agent_communication(self):
        """Demonstrate agents communicating with each other."""
        self.logger.info("\n=== INTER-AGENT COMMUNICATION DEMO ===")
        
        # Chat agent asks weather agent for weather info
        self.logger.info("Chat agent requesting weather information...")
        
        # Simulate a user asking about weather through chat
        chat_response = await self.agent_manager.send_message(
            "chat_agent",
            "chat_message",
            {
                "user_id": self.demo_data["user_id"],
                "session_id": self.demo_data["session_id"],
                "message": "What's the weather like in New York?"
            }
        )
        
        if chat_response and chat_response.get("success"):
            self.logger.info(f"Chat agent response: {chat_response.get('response', 'No response')}")
        
        # Task agent creates a task and calendar agent schedules a reminder
        self.logger.info("Creating a task with calendar reminder...")
        
        # Create task
        task_response = await self.agent_manager.send_message(
            "task_agent",
            "create_task",
            {
                "task_data": {
                    "title": "Follow up on weather report",
                    "description": "Check weather conditions and plan accordingly",
                    "priority": "medium"
                }
            }
        )
        
        if task_response and task_response.get("success"):
            task_id = task_response.get("task_id")
            self.logger.info(f"Task created: {task_id}")
            
            # Schedule a calendar event for the task
            event_response = await self.agent_manager.send_message(
                "calendar_agent",
                "create_event",
                {
                    "event_data": {
                        "title": f"Task Reminder: {task_id}",
                        "description": "Reminder to follow up on weather report task",
                        "start_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                        "end_time": (datetime.now() + timedelta(hours=2, minutes=30)).isoformat(),
                        "reminder_minutes": 30
                    }
                }
            )
            
            if event_response and event_response.get("success"):
                event_id = event_response.get("event_id")
                self.logger.info(f"Calendar reminder created: {event_id}")
    
    async def demo_agent_metrics(self):
        """Display agent metrics and health status."""
        self.logger.info("\n=== AGENT METRICS DEMO ===")
        
        agents = ["chat_agent", "task_agent", "calendar_agent", "weather_agent", "translation_agent", "data_agent", "news_agent"]
        
        for agent_id in agents:
            agent = self.agent_manager.get_agent(agent_id)
            if agent:
                health = agent.get_health()
                self.logger.info(f"{agent_id.upper()}:")
                self.logger.info(f"  Status: {health['status']}")
                self.logger.info(f"  Uptime: {health['uptime']:.2f} seconds")
                self.logger.info(f"  Messages Processed: {health['metrics']['messages_processed']}")
                self.logger.info(f"  Error Count: {health['error_count']}")
    
    async def run_demo(self):
        """Run the complete demo."""
        try:
            self.logger.info("🚀 Starting Agentic Framework Demo")
            self.logger.info("=" * 50)
            
            # Setup
            await self.setup_logging()
            await self.initialize_agents()
            
            # Run individual agent demos
            await self.demo_chat_agent()
            await self.demo_task_agent()
            await self.demo_calendar_agent()
            await self.demo_weather_agent()
            await self.demo_translation_agent()
            await self.demo_data_agent()
            await self.demo_news_agent()
            
            # Demonstrate inter-agent communication
            await self.demo_inter_agent_communication()
            
            # Show agent metrics
            await self.demo_agent_metrics()
            
            self.logger.info("\n" + "=" * 50)
            self.logger.info("✅ Demo completed successfully!")
            self.logger.info("All agents are working and communicating properly.")
            
        except Exception as e:
            self.logger.error(f"Demo failed with error: {e}")
            raise
        finally:
            # Cleanup
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up...")
        await self.agent_manager.stop_all_agents()
        self.logger.info("Cleanup complete")


async def main():
    """Main function to run the demo."""
    demo = AgenticFrameworkDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("🤖 Agentic Framework Demo")
    print("This demo will showcase all available agents and their capabilities.")
    print("Press Ctrl+C to stop the demo at any time.\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Check the demo.log file for detailed error information.")
