#!/usr/bin/env python3
"""
Basic Example - Agentic Framework

This example demonstrates how to use the agentic framework with basic
agent interactions.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import AgenticFramework


async def basic_example():
    """Basic example demonstrating agent interactions."""
    print("🚀 Starting Agentic Framework Basic Example")
    
    # Create framework instance
    framework = AgenticFramework()
    
    try:
        # Initialize the framework
        await framework.initialize()
        print("✅ Framework initialized successfully")
        
        # Get framework status
        status = await framework.get_status()
        print(f"📊 Framework Status: {status['agents_count']} agents running")
        
        # Example 1: Send a message to the chat agent
        print("\n💬 Example 1: Chat Agent Interaction")
        chat_response = await framework.send_message(
            sender="user",
            recipient="chat_agent",
            content={
                "action": "process_message",
                "message": "Hello! How are you today?",
                "user_id": "example_user"
            }
        )
        print(f"Chat Agent Response: {chat_response}")
        
        # Example 2: Create a task
        print("\n📋 Example 2: Task Agent Interaction")
        task_response = await framework.send_message(
            sender="user",
            recipient="task_agent",
            content={
                "action": "create_task",
                "task_data": {
                    "title": "Complete framework documentation",
                    "description": "Write comprehensive documentation for the agentic framework",
                    "priority": "high",
                    "due_date": "2024-01-15T18:00:00",
                    "assigned_to": "developer"
                }
            }
        )
        print(f"Task Created: {task_response}")
        
        # Example 3: Get weather information
        print("\n🌤️ Example 3: Weather Agent Interaction")
        weather_response = await framework.send_message(
            sender="user",
            recipient="weather_agent",
            content={
                "action": "get_current_weather",
                "location_id": "new_york"
            }
        )
        print(f"Weather Information: {weather_response}")
        
        # Example 4: Translate text
        print("\n🌍 Example 4: Translation Agent Interaction")
        translation_response = await framework.send_message(
            sender="user",
            recipient="translation_agent",
            content={
                "action": "translate_text",
                "source_text": "Hello, how are you?",
                "target_language": "es"
            }
        )
        print(f"Translation: {translation_response}")
        
        # Example 5: Broadcast message to all agents
        print("\n📢 Example 5: Broadcast Message")
        broadcast_response = await framework.broadcast_message(
            sender="system",
            content={
                "action": "system_notification",
                "message": "System maintenance scheduled for tonight",
                "priority": "medium"
            }
        )
        print(f"Broadcast Responses: {len(broadcast_response)} agents responded")
        
        # Example 6: Get news
        print("\n📰 Example 6: News Agent Interaction")
        news_response = await framework.send_message(
            sender="user",
            recipient="news_agent",
            content={
                "action": "get_latest_news",
                "limit": 3,
                "category": "technology"
            }
        )
        print(f"Latest Tech News: {news_response}")
        
        # Example 7: Data analysis
        print("\n📊 Example 7: Data Agent Interaction")
        data_response = await framework.send_message(
            sender="user",
            recipient="data_agent",
            content={
                "action": "analyze_data",
                "source_id": "default_json",
                "analysis_type": "basic"
            }
        )
        print(f"Data Analysis: {data_response}")
        
        # Example 8: Schedule a meeting
        print("\n📅 Example 8: Calendar Agent Interaction")
        calendar_response = await framework.send_message(
            sender="user",
            recipient="calendar_agent",
            content={
                "action": "schedule_meeting",
                "meeting_data": {
                    "title": "Team Standup",
                    "description": "Daily team standup meeting",
                    "start_time": "2024-01-10T09:00:00",
                    "end_time": "2024-01-10T09:30:00",
                    "attendees": ["alice", "bob", "charlie"],
                    "organizer": "alice"
                }
            }
        )
        print(f"Meeting Scheduled: {calendar_response}")
        
        # Example 9: Send an email
        print("\n📧 Example 9: Email Agent Interaction")
        email_response = await framework.send_message(
            sender="user",
            recipient="email_agent",
            content={
                "action": "compose_email",
                "email_data": {
                    "sender": "user@example.com",
                    "recipients": ["recipient@example.com"],
                    "subject": "Test Email from Agentic Framework",
                    "body": "This is a test email sent through the agentic framework.",
                    "priority": "normal"
                }
            }
        )
        print(f"Email Composed: {email_response}")
        
        print("\n✅ All examples completed successfully!")
        
        # Get final status
        final_status = await framework.get_status()
        print(f"\n📈 Final Framework Status:")
        print(f"   - Agents Running: {final_status['agents_count']}")
        print(f"   - Framework Running: {final_status['framework_running']}")
        
    except Exception as e:
        print(f"❌ Error in example: {e}")
        logging.error(f"Example error: {e}")
    
    finally:
        # Stop the framework
        await framework.stop()
        print("🛑 Framework stopped")


async def interactive_example():
    """Interactive example where user can send commands."""
    print("🎮 Starting Interactive Agentic Framework Example")
    
    framework = AgenticFramework()
    
    try:
        await framework.initialize()
        print("✅ Framework ready for interaction!")
        print("\nAvailable commands:")
        print("  chat <message> - Send message to chat agent")
        print("  task <title> - Create a new task")
        print("  weather <location> - Get weather for location")
        print("  translate <text> <target_lang> - Translate text")
        print("  news <category> - Get latest news")
        print("  status - Get framework status")
        print("  quit - Exit the example")
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if command.lower() == "quit":
                    break
                elif command.lower() == "status":
                    status = await framework.get_status()
                    print(f"Framework Status: {status['agents_count']} agents running")
                
                elif command.lower().startswith("chat "):
                    message = command[5:]
                    response = await framework.send_message(
                        sender="user",
                        recipient="chat_agent",
                        content={
                            "action": "process_message",
                            "message": message,
                            "user_id": "interactive_user"
                        }
                    )
                    print(f"Chat: {response}")
                
                elif command.lower().startswith("task "):
                    title = command[5:]
                    response = await framework.send_message(
                        sender="user",
                        recipient="task_agent",
                        content={
                            "action": "create_task",
                            "task_data": {
                                "title": title,
                                "description": f"Task created via interactive example: {title}",
                                "priority": "medium"
                            }
                        }
                    )
                    print(f"Task: {response}")
                
                elif command.lower().startswith("weather "):
                    location = command[8:]
                    response = await framework.send_message(
                        sender="user",
                        recipient="weather_agent",
                        content={
                            "action": "get_current_weather",
                            "location_id": location
                        }
                    )
                    print(f"Weather: {response}")
                
                elif command.lower().startswith("translate "):
                    parts = command[10:].split(" ", 1)
                    if len(parts) == 2:
                        text, target_lang = parts
                        response = await framework.send_message(
                            sender="user",
                            recipient="translation_agent",
                            content={
                                "action": "translate_text",
                                "source_text": text,
                                "target_language": target_lang
                            }
                        )
                        print(f"Translation: {response}")
                    else:
                        print("Usage: translate <text> <target_language>")
                
                elif command.lower().startswith("news "):
                    category = command[5:]
                    response = await framework.send_message(
                        sender="user",
                        recipient="news_agent",
                        content={
                            "action": "get_latest_news",
                            "limit": 5,
                            "category": category
                        }
                    )
                    print(f"News: {response}")
                
                else:
                    print("Unknown command. Type 'quit' to exit.")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    finally:
        await framework.stop()
        print("🛑 Interactive example ended")


async def main():
    """Main function to run examples."""
    print("🎯 Agentic Framework Examples")
    print("1. Basic Example (automated)")
    print("2. Interactive Example")
    
    choice = input("Choose example (1 or 2): ").strip()
    
    if choice == "1":
        await basic_example()
    elif choice == "2":
        await interactive_example()
    else:
        print("Invalid choice. Running basic example...")
        await basic_example()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the example
    asyncio.run(main())
