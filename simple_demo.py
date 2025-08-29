#!/usr/bin/env python3
"""
Simple Demo - Agentic Framework

A working demo that shows the framework in action.
"""

import asyncio
import logging
from main import AgenticFramework

# Set up basic logging
logging.basicConfig(level=logging.INFO)

async def simple_demo():
    """Simple demo of the agentic framework."""
    print("🚀 Starting Simple Agentic Framework Demo")
    
    # Create framework instance
    framework = AgenticFramework()
    
    try:
        # Initialize the framework
        print("🔧 Initializing framework...")
        await framework.initialize()
        print("✅ Framework initialized successfully")
        
        # Get framework status
        status = await framework.get_status()
        print(f"📊 Framework Status: {status['agents_count']} agents running")
        
        # Test basic functionality
        print("\n🧪 Testing basic functionality...")
        
        # Test message bus
        print("📡 Testing message bus...")
        await framework.message_bus.publish(
            sender="demo",
            content={"test": "message"},
            priority="normal"
        )
        print("✅ Message bus working")
        
        # Test context manager
        print("🗂️ Testing context manager...")
        framework.context_manager.set(
            "demo_key", "demo_value", scope="global"
        )
        value = framework.context_manager.get("demo_key", scope="global")
        print(f"✅ Context manager working: {value}")
        
        # Test agent manager
        print("🤖 Testing agent manager...")
        agent_status = framework.agent_manager.get_agent_status()
        print(f"✅ Agent manager working: {len(agent_status)} agents registered")
        
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")
        logging.error(f"Demo error: {e}")
    
    finally:
        # Stop the framework
        print("🛑 Stopping framework...")
        await framework.stop()
        print("✅ Framework stopped. Goodbye!")

if __name__ == "__main__":
    asyncio.run(simple_demo())
