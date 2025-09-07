#!/usr/bin/env python3
"""
Weather to Email Demo - Agentic Framework

This demo shows how two agents can work together:
1. Weather Agent: Gets weather information for Mumbai
2. Email Agent: Sends the weather details via email

Requirements for this demo to work:
- SMTP server configuration (Gmail, Outlook, etc.)
- Email credentials (username/password or app password)
- Internet connection for weather data
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Import the framework components
from core.agent_manager import AgentManager
from core.message_bus import Message, MessagePriority
from core.context_manager import ContextScope
from config.settings import get_settings

# Import the specific agents we need
from agents.weather_agent import WeatherAgent
from agents.email_agent import EmailAgent


class WeatherEmailDemo:
    """Demo class for Weather Agent + Email Agent automation."""
    
    def __init__(self):
        self.agent_manager = AgentManager()
        self.settings = get_settings()
        self.logger = logging.getLogger("weather_email_demo")
        
        # Demo configuration
        self.target_city = "Mumbai"
        self.target_email = "sumeetonline90@gmail.com"
        self.sender_email = "your-email@gmail.com"  # You'll need to configure this
        
    async def setup_logging(self):
        """Setup logging for the demo."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('weather_email_demo.log')
            ]
        )
        self.logger.info("Weather-Email Demo logging setup complete")
    
    async def initialize_agents(self):
        """Initialize and start the Weather and Email agents."""
        self.logger.info("Initializing Weather and Email agents...")
        
        # Create agent instances
        weather_agent = WeatherAgent("weather_agent", {
            "default_location": self.target_city,
            "update_interval": 300  # 5 minutes
        })
        
        email_agent = EmailAgent("email_agent", {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_use_tls": True,
            "check_interval": 60
        })
        
        # Register and start agents
        await self.agent_manager.register_agent(weather_agent)
        await self.agent_manager.register_agent(email_agent)
        
        await weather_agent.start()
        await email_agent.start()
        
        self.logger.info("Weather and Email agents initialized successfully!")
        
        # Wait for agents to fully initialize
        await asyncio.sleep(2)
    
    async def add_mumbai_location(self):
        """Add Mumbai as a location for weather monitoring."""
        self.logger.info(f"Adding {self.target_city} location to weather agent...")
        
        # Mumbai coordinates
        mumbai_data = {
            "location_id": "mumbai",
            "name": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "timezone": "Asia/Kolkata",
            "country": "India"
        }
        
        from core.message_bus import Message
        message = Message(
            sender="demo",
            recipient="weather_agent",
            type="add_location",
            data={"location_data": mumbai_data}
        )
        response = await self.agent_manager.send_message_to_agent("weather_agent", message)
        
        if response and response.get("success"):
            self.logger.info(f"✅ {self.target_city} location added successfully")
        else:
            self.logger.error(f"❌ Failed to add {self.target_city} location: {response.get('error', 'Unknown error')}")
    
    async def get_mumbai_weather(self) -> Dict[str, Any]:
        """Get current weather for Mumbai."""
        self.logger.info(f"Getting current weather for {self.target_city}...")
        
        response = await self.agent_manager.send_message(
            "weather_agent",
            "get_current_weather",
            {"location_id": "mumbai"}
        )
        
        if response and response.get("success"):
            weather_data = response.get("weather", {})
            self.logger.info(f"✅ Weather data retrieved for {self.target_city}")
            return weather_data
        else:
            self.logger.error(f"❌ Failed to get weather data: {response.get('error', 'Unknown error')}")
            return {}
    
    async def get_weather_forecast(self) -> list:
        """Get 3-day weather forecast for Mumbai."""
        self.logger.info(f"Getting 3-day forecast for {self.target_city}...")
        
        response = await self.agent_manager.send_message(
            "weather_agent",
            "get_forecast",
            {"location_id": "mumbai", "days": 3}
        )
        
        if response and response.get("success"):
            forecast_data = response.get("forecast", [])
            self.logger.info(f"✅ Forecast data retrieved for {self.target_city}")
            return forecast_data
        else:
            self.logger.error(f"❌ Failed to get forecast data: {response.get('error', 'Unknown error')}")
            return []
    
    async def compose_weather_email(self, weather_data: Dict[str, Any], forecast_data: list) -> str:
        """Compose the weather email content."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        email_content = f"""
Weather Report for Mumbai
Generated on: {current_time}

CURRENT WEATHER:
================
Location: {weather_data.get('location', 'Mumbai')}
Temperature: {weather_data.get('temperature', 'N/A')}°C
Condition: {weather_data.get('condition', 'N/A').title()}
Humidity: {weather_data.get('humidity', 'N/A')}%
Wind Speed: {weather_data.get('wind_speed', 'N/A')} km/h
Wind Direction: {weather_data.get('wind_direction', 'N/A')}
Pressure: {weather_data.get('pressure', 'N/A')} hPa
Visibility: {weather_data.get('visibility', 'N/A')} km

3-DAY FORECAST:
===============
"""
        
        for day in forecast_data:
            email_content += f"""
Date: {day.get('date', 'N/A')}
High: {day.get('high_temp', 'N/A')}°C | Low: {day.get('low_temp', 'N/A')}°C
Condition: {day.get('condition', 'N/A').title()}
Humidity: {day.get('humidity', 'N/A')}%
Wind: {day.get('wind_speed', 'N/A')} km/h
Precipitation Chance: {day.get('precipitation_chance', 'N/A')}%
---
"""
        
        email_content += f"""

This weather report was automatically generated by the Agentic Framework.
For more detailed weather information, please visit your local weather service.

Best regards,
Weather Bot 🤖
"""
        
        return email_content
    
    async def send_weather_email(self, email_content: str):
        """Send the weather email."""
        self.logger.info(f"Composing weather email for {self.target_email}...")
        
        # Compose the email
        email_data = {
            "sender": self.sender_email,
            "recipients": [self.target_email],
            "subject": f"Weather Report for Mumbai - {datetime.now().strftime('%Y-%m-%d')}",
            "body": email_content,
            "priority": "normal"
        }
        
        response = await self.agent_manager.send_message(
            "email_agent",
            "compose_email",
            {"email_data": email_data}
        )
        
        if response and response.get("success"):
            email_id = response.get("email_id")
            self.logger.info(f"✅ Email composed with ID: {email_id}")
            
            # Send the email
            self.logger.info("Sending weather email...")
            send_response = await self.agent_manager.send_message(
                "email_agent",
                "send_email",
                {"email_id": email_id}
            )
            
            if send_response and send_response.get("success"):
                self.logger.info(f"✅ Weather email sent successfully to {self.target_email}")
                return True
            else:
                self.logger.error(f"❌ Failed to send email: {send_response.get('error', 'Unknown error')}")
                return False
        else:
            self.logger.error(f"❌ Failed to compose email: {response.get('error', 'Unknown error')}")
            return False
    
    async def run_automation(self):
        """Run the complete weather-to-email automation."""
        try:
            self.logger.info("🌤️ Starting Weather-to-Email Automation")
            self.logger.info("=" * 60)
            
            # Setup
            await self.setup_logging()
            await self.initialize_agents()
            
            # Add Mumbai location
            await self.add_mumbai_location()
            
            # Get weather data
            weather_data = await self.get_mumbai_weather()
            if not weather_data:
                self.logger.error("❌ Cannot proceed without weather data")
                return False
            
            # Get forecast data
            forecast_data = await self.get_weather_forecast()
            
            # Compose email content
            email_content = await self.compose_weather_email(weather_data, forecast_data)
            self.logger.info("📧 Email content composed")
            
            # Send the email
            success = await self.send_weather_email(email_content)
            
            if success:
                self.logger.info("\n" + "=" * 60)
                self.logger.info("✅ Weather-to-Email automation completed successfully!")
                self.logger.info(f"📧 Weather report sent to {self.target_email}")
                return True
            else:
                self.logger.error("❌ Weather-to-Email automation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Automation failed with error: {e}")
            return False
        finally:
            # Cleanup
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("🧹 Cleaning up...")
        await self.agent_manager.stop_all_agents()
        self.logger.info("✅ Cleanup complete")


def print_requirements():
    """Print the requirements for this demo to work."""
    print("""
🔧 REQUIREMENTS FOR WEATHER-EMAIL AUTOMATION:

1. EMAIL CONFIGURATION:
   - SMTP Server: Gmail (smtp.gmail.com), Outlook, or your email provider
   - Port: 587 (TLS) or 465 (SSL)
   - Email credentials: Username and password/app password
   
2. GMAIL SETUP (Recommended):
   - Enable 2-factor authentication
   - Generate an App Password (not your regular password)
   - Use the App Password in the configuration
   
3. CONFIGURATION NEEDED:
   - Update 'sender_email' in the demo script
   - Set up SMTP credentials in the email agent configuration
   - Ensure internet connection for weather data
   
4. OPTIONAL ENHANCEMENTS:
   - Add weather API key for real weather data (currently using simulated data)
   - Configure email templates
   - Add error handling and retry logic
   - Schedule the automation to run periodically

📝 TO RUN THIS DEMO:
1. Update the sender_email variable in the script
2. Configure SMTP settings in the email agent
3. Run: python weather_email_demo.py

⚠️  NOTE: This demo uses simulated weather data. For real weather data,
   you'll need to configure a weather API key in the weather agent.
""")


async def main():
    """Main function to run the demo."""
    print_requirements()
    
    # Ask user if they want to proceed
    proceed = input("\nDo you want to run the demo? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Demo cancelled. Configure the requirements and try again.")
        return
    
    demo = WeatherEmailDemo()
    success = await demo.run_automation()
    
    if success:
        print("\n🎉 Demo completed successfully!")
        print("Check your email for the weather report!")
    else:
        print("\n❌ Demo failed. Check the log file for details.")


if __name__ == "__main__":
    print("🌤️ Weather-to-Email Automation Demo")
    print("This demo will get Mumbai's weather and email it to you.")
    print("Press Ctrl+C to stop the demo at any time.\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Check the weather_email_demo.log file for detailed error information.")
