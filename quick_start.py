#!/usr/bin/env python3
"""
Quick Start Script - Agentic Framework

This script provides a quick way to start the agentic framework
with minimal configuration and setup.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from main import AgenticFramework


def setup_basic_logging():
    """Set up basic logging for quick start."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def create_default_directories():
    """Create default directories if they don't exist."""
    directories = ['data', 'logs', 'config']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)


def print_banner():
    """Print the framework banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    AGENTIC FRAMEWORK                         ║
    ║                                                              ║
    ║  🤖 A modular and extensible framework for AI agents        ║
    ║  🚀 Quick start mode - minimal configuration                ║
    ║  📦 8 agents ready to use: Chat, Task, Email, Calendar,     ║
    ║     Data, Weather, News, Translation                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def quick_start():
    """Quick start the framework."""
    print_banner()
    
    # Setup
    setup_basic_logging()
    create_default_directories()
    
    print("🔧 Setting up Agentic Framework...")
    
    # Create framework instance
    framework = AgenticFramework()
    
    try:
        # Initialize the framework
        print("🚀 Initializing framework and agents...")
        await framework.initialize()
        
        # Get status
        status = await framework.get_status()
        print(f"✅ Framework started successfully!")
        print(f"📊 Status: {status['agents_count']} agents running")
        
        # Show available agents
        print("\n🤖 Available Agents:")
        for agent_id, agent_status in status['agent_statuses'].items():
            status_emoji = "🟢" if agent_status['status'] == 'running' else "🔴"
            print(f"   {status_emoji} {agent_id}: {agent_status['status']}")
        
        # Quick demo
        print("\n🎯 Running quick demo...")
        
        # Demo 1: Chat agent
        print("\n💬 Testing Chat Agent...")
        chat_response = await framework.send_message(
            sender="user",
            recipient="chat_agent",
            content={
                "action": "process_message",
                "message": "Hello! This is a quick start demo.",
                "user_id": "quick_start_user"
            }
        )
        print(f"   Response: {chat_response.get('response', 'No response')}")
        
        # Demo 2: Task agent
        print("\n📋 Testing Task Agent...")
        task_response = await framework.send_message(
            sender="user",
            recipient="task_agent",
            content={
                "action": "create_task",
                "task_data": {
                    "title": "Quick Start Demo Task",
                    "description": "This task was created during the quick start demo",
                    "priority": "medium"
                }
            }
        )
        print(f"   Task created: {task_response.get('task_id', 'Unknown')}")
        
        # Demo 3: Weather agent
        print("\n🌤️ Testing Weather Agent...")
        weather_response = await framework.send_message(
            sender="user",
            recipient="weather_agent",
            content={
                "action": "get_current_weather",
                "location_id": "new_york"
            }
        )
        if 'weather' in weather_response:
            weather = weather_response['weather']
            print(f"   Weather in {weather.get('location', 'Unknown')}: {weather.get('temperature', 'Unknown')}°C")
        
        # Demo 4: Translation agent
        print("\n🌍 Testing Translation Agent...")
        translation_response = await framework.send_message(
            sender="user",
            recipient="translation_agent",
            content={
                "action": "translate_text",
                "source_text": "Hello, world!",
                "target_language": "es"
            }
        )
        if 'result' in translation_response:
            result = translation_response['result']
            print(f"   Translation: {result.get('translated_text', 'Translation failed')}")
        
        print("\n✅ Quick start demo completed successfully!")
        print("\n🎮 Framework is now running. You can:")
        print("   - Press Ctrl+C to stop the framework")
        print("   - Run 'python examples/basic_example.py' for more examples")
        print("   - Check the logs in the 'logs' directory")
        print("   - View data in the 'data' directory")
        
        # Keep the framework running
        print("\n🔄 Framework running... (Press Ctrl+C to stop)")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Received stop signal...")
    except Exception as e:
        print(f"\n❌ Error during quick start: {e}")
        logging.error(f"Quick start error: {e}")
    finally:
        # Stop the framework
        print("🛑 Stopping framework...")
        await framework.stop()
        print("✅ Framework stopped. Goodbye!")


def main():
    """Main entry point."""
    try:
        asyncio.run(quick_start())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
