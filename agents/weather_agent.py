"""
Weather Information Agent

Handles weather data retrieval and forecasting.
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


class WeatherCondition(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"
    STORM = "storm"
    FOG = "fog"
    WINDY = "windy"
    HOT = "hot"
    COLD = "cold"


@dataclass
class WeatherData:
    location: str
    temperature: float
    condition: WeatherCondition
    humidity: float
    wind_speed: float
    wind_direction: str
    pressure: float
    visibility: float
    timestamp: datetime = field(default_factory=datetime.now)
    forecast: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Location:
    location_id: str
    name: str
    latitude: float
    longitude: float
    timezone: str
    country: str
    created_at: datetime = field(default_factory=datetime.now)


class WeatherAgent(BaseAgent):
    """
    Weather Information Agent for handling weather data and forecasts.
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.locations: Dict[str, Location] = {}
        self.weather_cache: Dict[str, WeatherData] = {}
        self.api_key: Optional[str] = None
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
    async def start(self) -> bool:
        """Start the weather agent and initialize weather services."""
        if await super().start():
            self.logger.info("Weather agent started successfully")
            # Load API key from context
            self.api_key = await self.context_manager.get("weather_api_key", scope="global")
            # Initialize default locations
            await self._initialize_default_locations()
            return True
        return False
    
    async def stop(self) -> bool:
        """Stop the weather agent."""
        if await super().stop():
            self.logger.info("Weather agent stopped successfully")
            return True
        return False
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages for weather operations."""
        try:
            if message.content.get("action") == "get_current_weather":
                return await self._handle_get_current_weather(message)
            elif message.content.get("action") == "get_forecast":
                return await self._handle_get_forecast(message)
            elif message.content.get("action") == "add_location":
                return await self._handle_add_location(message)
            elif message.content.get("action") == "get_weather_alerts":
                return await self._handle_get_weather_alerts(message)
            elif message.content.get("action") == "get_weather_history":
                return await self._handle_get_weather_history(message)
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
    
    async def _handle_get_current_weather(self, message: Message) -> Message:
        """Handle current weather request."""
        location_id = message.content.get("location_id")
        
        if location_id not in self.locations:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Location {location_id} not found"}
            )
        
        try:
            weather_data = await self._get_current_weather(location_id)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "current_weather",
                    "location_id": location_id,
                    "weather": self._weather_to_dict(weather_data)
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error getting weather: {str(e)}"}
            )
    
    async def _handle_get_forecast(self, message: Message) -> Message:
        """Handle weather forecast request."""
        location_id = message.content.get("location_id")
        days = message.content.get("days", 5)
        
        if location_id not in self.locations:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Location {location_id} not found"}
            )
        
        try:
            forecast = await self._get_weather_forecast(location_id, days)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "weather_forecast",
                    "location_id": location_id,
                    "forecast": forecast,
                    "days": days
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error getting forecast: {str(e)}"}
            )
    
    async def _handle_add_location(self, message: Message) -> Message:
        """Handle location addition request."""
        location_data = message.content.get("location_data", {})
        
        location = Location(
            location_id=location_data.get("location_id", f"location_{len(self.locations) + 1}"),
            name=location_data.get("name", "Unknown Location"),
            latitude=location_data.get("latitude", 0.0),
            longitude=location_data.get("longitude", 0.0),
            timezone=location_data.get("timezone", "UTC"),
            country=location_data.get("country", "")
        )
        
        self.locations[location.location_id] = location
        self.logger.info(f"Added location: {location.location_id} - {location.name}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "location_added",
                "location_id": location.location_id,
                "location": {
                    "location_id": location.location_id,
                    "name": location.name,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "timezone": location.timezone,
                    "country": location.country,
                    "created_at": location.created_at.isoformat()
                }
            }
        )
    
    async def _handle_get_weather_alerts(self, message: Message) -> Message:
        """Handle weather alerts request."""
        location_id = message.content.get("location_id")
        
        if location_id not in self.locations:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Location {location_id} not found"}
            )
        
        try:
            alerts = await self._get_weather_alerts(location_id)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "weather_alerts",
                    "location_id": location_id,
                    "alerts": alerts
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error getting alerts: {str(e)}"}
            )
    
    async def _handle_get_weather_history(self, message: Message) -> Message:
        """Handle weather history request."""
        location_id = message.content.get("location_id")
        days_back = message.content.get("days_back", 7)
        
        if location_id not in self.locations:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Location {location_id} not found"}
            )
        
        try:
            history = await self._get_weather_history(location_id, days_back)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "weather_history",
                    "location_id": location_id,
                    "history": history,
                    "days_back": days_back
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error getting history: {str(e)}"}
            )
    
    async def _initialize_default_locations(self):
        """Initialize default weather locations."""
        # Add some default locations
        default_locations = [
            {
                "location_id": "new_york",
                "name": "New York",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timezone": "America/New_York",
                "country": "USA"
            },
            {
                "location_id": "london",
                "name": "London",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "timezone": "Europe/London",
                "country": "UK"
            },
            {
                "location_id": "tokyo",
                "name": "Tokyo",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "timezone": "Asia/Tokyo",
                "country": "Japan"
            }
        ]
        
        for loc_data in default_locations:
            location = Location(**loc_data)
            self.locations[location.location_id] = location
    
    async def _get_current_weather(self, location_id: str) -> WeatherData:
        """Get current weather for a location."""
        location = self.locations[location_id]
        
        # Check cache first
        cache_key = f"{location_id}_current"
        if cache_key in self.weather_cache:
            cached_data = self.weather_cache[cache_key]
            # Check if cache is still valid (less than 30 minutes old)
            if datetime.now() - cached_data.timestamp < timedelta(minutes=30):
                return cached_data
        
        # Simulate weather API call
        weather_data = await self._simulate_weather_api_call(location)
        
        # Cache the result
        self.weather_cache[cache_key] = weather_data
        
        return weather_data
    
    async def _get_weather_forecast(self, location_id: str, days: int) -> List[Dict[str, Any]]:
        """Get weather forecast for a location."""
        location = self.locations[location_id]
        
        # Simulate forecast API call
        forecast = []
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            forecast_day = {
                "date": date.strftime("%Y-%m-%d"),
                "high_temp": 20 + (i * 2),  # Simulated temperature
                "low_temp": 10 + (i * 1),
                "condition": "clear",
                "humidity": 60 + (i * 5),
                "wind_speed": 10 + (i * 2),
                "precipitation_chance": 20 + (i * 10)
            }
            forecast.append(forecast_day)
        
        return forecast
    
    async def _get_weather_alerts(self, location_id: str) -> List[Dict[str, Any]]:
        """Get weather alerts for a location."""
        # Simulate weather alerts
        alerts = []
        
        # Randomly generate some alerts
        import random
        if random.random() < 0.3:  # 30% chance of having alerts
            alert_types = ["Severe Thunderstorm", "Flood Warning", "Heat Advisory", "Winter Storm"]
            for i in range(random.randint(1, 3)):
                alert = {
                    "alert_id": f"alert_{location_id}_{i}",
                    "type": random.choice(alert_types),
                    "severity": random.choice(["Minor", "Moderate", "Severe"]),
                    "description": f"Weather alert for {self.locations[location_id].name}",
                    "start_time": datetime.now().isoformat(),
                    "end_time": (datetime.now() + timedelta(hours=6)).isoformat()
                }
                alerts.append(alert)
        
        return alerts
    
    async def _get_weather_history(self, location_id: str, days_back: int) -> List[Dict[str, Any]]:
        """Get weather history for a location."""
        history = []
        
        for i in range(days_back):
            date = datetime.now() - timedelta(days=i)
            history_day = {
                "date": date.strftime("%Y-%m-%d"),
                "high_temp": 18 + (i * 1),
                "low_temp": 8 + (i * 1),
                "condition": "clear",
                "humidity": 65 + (i * 2),
                "wind_speed": 12 + (i * 1),
                "precipitation": 0.0
            }
            history.append(history_day)
        
        return history
    
    async def _simulate_weather_api_call(self, location: Location) -> WeatherData:
        """Simulate a weather API call."""
        # This would normally call a real weather API
        # For now, we'll simulate the response
        
        import random
        
        # Simulate different weather conditions based on location
        if location.name == "New York":
            base_temp = 15
            conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY, WeatherCondition.RAIN]
        elif location.name == "London":
            base_temp = 10
            conditions = [WeatherCondition.CLOUDY, WeatherCondition.RAIN, WeatherCondition.FOG]
        elif location.name == "Tokyo":
            base_temp = 20
            conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY, WeatherCondition.RAIN]
        else:
            base_temp = 15
            conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY]
        
        weather_data = WeatherData(
            location=location.name,
            temperature=base_temp + random.uniform(-5, 5),
            condition=random.choice(conditions),
            humidity=random.uniform(40, 80),
            wind_speed=random.uniform(5, 20),
            wind_direction=random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            pressure=random.uniform(1000, 1020),
            visibility=random.uniform(5, 15)
        )
        
        return weather_data
    
    def _weather_to_dict(self, weather: WeatherData) -> Dict[str, Any]:
        """Convert weather data to dictionary for serialization."""
        return {
            "location": weather.location,
            "temperature": weather.temperature,
            "condition": weather.condition.value,
            "humidity": weather.humidity,
            "wind_speed": weather.wind_speed,
            "wind_direction": weather.wind_direction,
            "pressure": weather.pressure,
            "visibility": weather.visibility,
            "timestamp": weather.timestamp.isoformat(),
            "forecast": weather.forecast
        }

    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for weather agent."""
        try:
            action = message.content.get("action")
            
            if action == "get_current_weather":
                return await self._handle_get_current_weather(message)
            elif action == "get_forecast":
                return await self._handle_get_forecast(message)
            elif action == "add_location":
                return await self._handle_add_location(message)
            elif action == "get_weather_alerts":
                return await self._handle_get_weather_alerts(message)
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
        """Get weather agent metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "total_locations": len(self.locations),
            "cache_size": len(self.weather_cache),
            "api_key_configured": self.api_key is not None
        })
        return metrics
