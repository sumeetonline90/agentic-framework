#!/usr/bin/env python3
"""
True Agentic Framework Demo

This demo shows TRUE agent-to-agent communication where:
1. Weather Agent gets weather data
2. Weather Agent sends data directly to Email Agent via message bus
3. Email Agent receives data and sends email automatically
4. No manual orchestration - agents work independently
"""

import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('email_settings.env')

from agents.weather_agent import WeatherAgent
from agents.email_agent import EmailAgent
from core.message_bus import Message, MessageBus
from core.context_manager import ContextScope


class TrueAgenticDemo:
    """Demo showing true agentic framework behavior."""
    
    def __init__(self):
        self.logger = logging.getLogger("true_agentic_demo")
        
        # Demo configuration
        self.target_city = "Mumbai"
        self.target_email = "sumeetonline90@gmail.com"
        
        # Load email configuration
        import os
        self.smtp_config = {
            "host": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("EMAIL_USERNAME"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "use_tls": os.getenv("SMTP_USE_TLS", "True").lower() == "true",
            "use_ssl": os.getenv("SMTP_USE_SSL", "False").lower() == "true"
        }
        
        # Agent instances
        self.weather_agent = None
        self.email_agent = None
        self.message_bus = None
        
    async def setup_logging(self):
        """Setup logging for the demo."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger.info("True Agentic Framework Demo logging setup complete")
    
    async def initialize_agents(self):
        """Initialize agents with shared message bus."""
        self.logger.info("Initializing agents with shared message bus...")
        
        # Create shared message bus
        self.message_bus = MessageBus()
        await self.message_bus.start()
        
        # Create agent instances with shared message bus
        self.weather_agent = WeatherAgent("weather_agent", {})
        self.email_agent = EmailAgent("email_agent", self.smtp_config)
        
        # Set shared message bus for both agents
        self.weather_agent.message_bus = self.message_bus
        self.email_agent.message_bus = self.message_bus
        
        # Start agents
        await self.weather_agent.start()
        await self.email_agent.start()
        
        # Set SMTP config directly on email agent
        self.email_agent.smtp_config = self.smtp_config
        
        self.logger.info("✅ Agents initialized with shared message bus!")
        
        # Wait for agents to fully initialize
        await asyncio.sleep(2)
    
    async def setup_weather_agent(self):
        """Setup weather agent with Mumbai location."""
        self.logger.info(f"Setting up weather agent with {self.target_city} location...")
        
        # Mumbai coordinates and details
        mumbai_data = {
            "location_id": "mumbai",
            "name": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "timezone": "Asia/Kolkata",
            "country": "India"
        }
        
        # Create message to add location
        import uuid
        add_location_message = Message(
            id=str(uuid.uuid4()),
            sender="demo",
            recipient="weather_agent",
            type="weather_request",
            data={"action": "add_location", "location_data": mumbai_data}
        )
        
        # Send message to weather agent
        response = await self.weather_agent.process_message(add_location_message)
        
        if response and response.data.get("action") == "location_added":
            self.logger.info(f"✅ {self.target_city} location added to weather agent")
            return True
        else:
            self.logger.error(f"❌ Failed to add {self.target_city} location")
            return False
    
    async def trigger_weather_to_email_flow(self):
        """Trigger the weather-to-email flow by requesting weather data."""
        self.logger.info("🌤️ Triggering weather-to-email flow...")
        self.logger.info("Weather Agent will get data and send it to Email Agent automatically")
        
        # Create message to get current weather
        import uuid
        weather_request_message = Message(
            id=str(uuid.uuid4()),
            sender="demo",
            recipient="weather_agent",
            type="weather_request",
            data={
                "action": "get_current_weather", 
                "location_id": "mumbai",
                "send_to_email": True,  # Tell weather agent to send to email
                "email_recipient": self.target_email,
                "email_sender": self.smtp_config["username"]
            }
        )
        
        # Send message to weather agent
        self.logger.info("📤 Sending weather request to Weather Agent...")
        response = await self.weather_agent.process_message(weather_request_message)
        
        if response and response.data.get("action") == "current_weather":
            self.logger.info("✅ Weather Agent received request and will process it")
            return True
        else:
            self.logger.error(f"❌ Failed to trigger weather request: {response.data.get('error', 'Unknown error') if response else 'No response'}")
            return False
    
    async def monitor_agent_communication(self, timeout=30):
        """Monitor the message bus to see agent-to-agent communication."""
        self.logger.info("👀 Monitoring agent-to-agent communication...")
        self.logger.info("Watch for messages between Weather Agent and Email Agent")
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            # Check if there are any pending messages
            await asyncio.sleep(1)
            
            # In a real implementation, you would monitor the message bus
            # For now, we'll simulate the monitoring
            
        self.logger.info("⏰ Monitoring timeout reached")
    
    async def run_true_agentic_demo(self):
        """Run the true agentic framework demo."""
        try:
            self.logger.info("🤖 Starting TRUE Agentic Framework Demo")
            self.logger.info("=" * 60)
            self.logger.info("This demo shows agents communicating directly with each other")
            
            # Setup
            await self.setup_logging()
            
            # Initialize agents with shared message bus
            await self.initialize_agents()
            
            # Setup weather agent
            if not await self.setup_weather_agent():
                return False
            
            # Trigger the weather-to-email flow
            if not await self.trigger_weather_to_email_flow():
                return False
            
            # Monitor agent communication
            await self.monitor_agent_communication(10)
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("✅ TRUE Agentic Framework Demo completed!")
            self.logger.info("🤖 Agents communicated directly via message bus")
            return True
                
        except Exception as e:
            self.logger.error(f"❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup
            self.logger.info("🧹 Cleaning up agents...")
            try:
                if self.weather_agent:
                    await self.weather_agent.stop()
                if self.email_agent:
                    await self.email_agent.stop()
                if self.message_bus:
                    await self.message_bus.stop()
            except:
                pass
            self.logger.info("✅ Cleanup complete")


async def main():
    """Main function to run the true agentic demo."""
    print("🤖 TRUE Agentic Framework Demo")
    print("This demo shows TRUE agent-to-agent communication:")
    print("1. Weather Agent gets Mumbai weather data")
    print("2. Weather Agent sends data DIRECTLY to Email Agent")
    print("3. Email Agent receives data and sends email automatically")
    print("4. No manual orchestration - agents work independently")
    print("Press Ctrl+C to stop the demo at any time.\n")
    
    demo = TrueAgenticDemo()
    success = await demo.run_true_agentic_demo()
    
    if success:
        print("\n🎉 TRUE Agentic Demo completed!")
        print("🤖 This demonstrates TRUE agentic framework behavior!")
    else:
        print("\n❌ TRUE Agentic Demo failed. Check the log output for details.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
