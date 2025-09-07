#!/usr/bin/env python3
"""
Agent-to-Agent Communication Demo

This demo shows proper agent communication:
1. Weather Agent: Gets weather data for Mumbai
2. Weather Agent: Sends data to Email Agent via message bus
3. Email Agent: Receives weather data and sends formatted email
"""

import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('email_settings.env')

from agents.weather_agent import WeatherAgent
from agents.email_agent import EmailAgent
from core.message_bus import Message
from core.context_manager import ContextScope


class AgentToAgentDemo:
    """Demo showing proper agent-to-agent communication."""
    
    def __init__(self):
        self.logger = logging.getLogger("agent_to_agent_demo")
        
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
        
    async def setup_logging(self):
        """Setup logging for the demo."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger.info("Agent-to-Agent Demo logging setup complete")
    
    async def initialize_agents(self):
        """Initialize and start both agents."""
        self.logger.info("Initializing Weather and Email agents...")
        
        # Create agent instances
        self.weather_agent = WeatherAgent("weather_agent", {})
        self.email_agent = EmailAgent("email_agent", self.smtp_config)
        
        # Start agents
        await self.weather_agent.start()
        await self.email_agent.start()
        
        # Set SMTP config directly on email agent
        self.email_agent.smtp_config = self.smtp_config
        
        self.logger.info("✅ Weather and Email agents initialized successfully!")
        
        # Wait for agents to fully initialize
        await asyncio.sleep(2)
    
    async def add_mumbai_location_to_weather_agent(self):
        """Add Mumbai location to the weather agent."""
        self.logger.info(f"Adding {self.target_city} location to weather agent...")
        
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
            self.logger.error(f"❌ Failed to add {self.target_city} location: {response.data.get('error', 'Unknown error') if response else 'No response'}")
            return False
    
    async def get_weather_from_weather_agent(self):
        """Get weather data from the weather agent."""
        self.logger.info(f"Requesting weather data from weather agent for {self.target_city}...")
        
        # Create message to get current weather
        import uuid
        weather_request_message = Message(
            id=str(uuid.uuid4()),
            sender="demo",
            recipient="weather_agent",
            type="weather_request",
            data={"action": "get_current_weather", "location_id": "mumbai"}
        )
        
        # Send message to weather agent
        response = await self.weather_agent.process_message(weather_request_message)
        
        if response and response.data.get("action") == "current_weather":
            weather_data = response.data.get("weather")
            self.logger.info(f"✅ Weather data received from weather agent: {weather_data['location']} - {weather_data['temperature']}°C")
            return weather_data
        else:
            self.logger.error(f"❌ Failed to get weather data: {response.data.get('error', 'Unknown error') if response else 'No response'}")
            return None
    
    async def get_forecast_from_weather_agent(self):
        """Get weather forecast from the weather agent."""
        self.logger.info(f"Requesting 3-day forecast from weather agent for {self.target_city}...")
        
        # Create message to get forecast
        import uuid
        forecast_request_message = Message(
            id=str(uuid.uuid4()),
            sender="demo",
            recipient="weather_agent",
            type="weather_request",
            data={"action": "get_forecast", "location_id": "mumbai", "days": 3}
        )
        
        # Send message to weather agent
        response = await self.weather_agent.process_message(forecast_request_message)
        
        if response and response.data.get("action") == "weather_forecast":
            forecast_data = response.data.get("forecast")
            self.logger.info(f"✅ Forecast data received from weather agent: {len(forecast_data)} days")
            return forecast_data
        else:
            self.logger.error(f"❌ Failed to get forecast data: {response.data.get('error', 'Unknown error') if response else 'No response'}")
            return []
    
    def format_weather_email_content(self, weather_data: dict, forecast_data: list) -> str:
        """Format weather data into email content."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        email_content = f"""
🌤️ WEATHER REPORT FOR {weather_data['location'].upper()}
Generated on: {current_time}

📍 CURRENT WEATHER:
==================
Location: {weather_data['location']}
Temperature: {weather_data['temperature']}°C
Condition: {weather_data['condition'].title()}
Humidity: {weather_data['humidity']}%
Wind Speed: {weather_data['wind_speed']} km/h
Wind Direction: {weather_data['wind_direction']}
Pressure: {weather_data['pressure']} hPa
Visibility: {weather_data['visibility']} km

📅 3-DAY FORECAST:
==================
"""
        
        for day in forecast_data:
            email_content += f"""
📅 {day['date']}
   High: {day['high_temp']}°C | Low: {day['low_temp']}°C
   Condition: {day['condition'].title()}
   Humidity: {day['humidity']}%
   Wind: {day['wind_speed']} km/h
   Precipitation Chance: {day['precipitation_chance']}%
   {'─' * 40}
"""
        
        email_content += f"""

🤖 This weather report was automatically generated by the Agentic Framework.
🌤️ Weather data provided by Weather Agent
📧 Email delivery handled by Email Agent

Best regards,
Agentic Framework Weather Bot 🌤️
"""
        
        return email_content
    
    async def send_weather_email_via_email_agent(self, weather_data: dict, forecast_data: list):
        """Send weather email via the email agent."""
        self.logger.info("Sending weather data to email agent for processing...")
        
        # Format the email content
        email_content = self.format_weather_email_content(weather_data, forecast_data)
        
        # Create email data
        email_data = {
            "sender": self.smtp_config["username"],
            "recipients": [self.target_email],
            "subject": f"🌤️ Weather Report for {weather_data['location']} - {datetime.now().strftime('%Y-%m-%d')}",
            "body": email_content,
            "priority": "normal"
        }
        
        # Create message to compose email
        import uuid
        compose_message = Message(
            id=str(uuid.uuid4()),
            sender="demo",
            recipient="email_agent",
            type="email_request",
            data={"action": "compose_email", "email_data": email_data}
        )
        
        # Send message to email agent
        self.logger.info("📝 Composing weather email via email agent...")
        compose_response = await self.email_agent.process_message(compose_message)
        
        if compose_response and compose_response.data.get("action") == "email_composed":
            email_id = compose_response.data.get("email_id")
            self.logger.info(f"✅ Email composed by email agent with ID: {email_id}")
            
            # Create message to send email
            send_message = Message(
                id=str(uuid.uuid4()),
                sender="demo",
                recipient="email_agent",
                type="email_request",
                data={"action": "send_email", "email_id": email_id}
            )
            
            # Send message to email agent
            self.logger.info("📤 Sending weather email via email agent...")
            send_response = await self.email_agent.process_message(send_message)
            
            if send_response and send_response.data.get("action") == "email_sent":
                self.logger.info("✅ Weather email sent successfully by email agent!")
                self.logger.info(f"📧 Weather report sent to {self.target_email}")
                return True
            else:
                self.logger.error(f"❌ Email agent failed to send email: {send_response.data.get('error', 'Unknown error') if send_response else 'No response'}")
                return False
        else:
            self.logger.error(f"❌ Email agent failed to compose email: {compose_response.data.get('error', 'Unknown error') if compose_response else 'No response'}")
            return False
    
    async def run_agent_to_agent_demo(self):
        """Run the complete agent-to-agent communication demo."""
        try:
            self.logger.info("🤖 Starting Agent-to-Agent Communication Demo")
            self.logger.info("=" * 60)
            
            # Setup
            await self.setup_logging()
            
            # Initialize agents
            await self.initialize_agents()
            
            # Step 1: Add Mumbai location to weather agent
            if not await self.add_mumbai_location_to_weather_agent():
                return False
            
            # Step 2: Get weather data from weather agent
            weather_data = await self.get_weather_from_weather_agent()
            if not weather_data:
                return False
            
            # Step 3: Get forecast data from weather agent
            forecast_data = await self.get_forecast_from_weather_agent()
            
            # Step 4: Send weather data to email agent for processing
            success = await self.send_weather_email_via_email_agent(weather_data, forecast_data)
            
            if success:
                self.logger.info("\n" + "=" * 60)
                self.logger.info("✅ Agent-to-Agent Communication Demo completed successfully!")
                self.logger.info("🌤️ Weather Agent → Email Agent → Email Sent")
                return True
            else:
                self.logger.error("❌ Agent-to-Agent Communication Demo failed")
                return False
                
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
            except:
                pass
            self.logger.info("✅ Cleanup complete")


async def main():
    """Main function to run the agent-to-agent demo."""
    print("🤖 Agent-to-Agent Communication Demo")
    print("This demo shows proper agent communication:")
    print("1. Weather Agent gets Mumbai weather data")
    print("2. Weather Agent passes data to Email Agent")
    print("3. Email Agent sends formatted weather report")
    print("Press Ctrl+C to stop the demo at any time.\n")
    
    demo = AgentToAgentDemo()
    success = await demo.run_agent_to_agent_demo()
    
    if success:
        print("\n🎉 Agent-to-Agent Demo completed successfully!")
        print("Check your email for the Mumbai weather report!")
        print("🤖 This demonstrates proper agent communication!")
    else:
        print("\n❌ Agent-to-Agent Demo failed. Check the log output for details.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
