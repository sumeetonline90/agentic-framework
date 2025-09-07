#!/usr/bin/env python3
"""
Email Setup Test

This script tests your email configuration to ensure it works
before running the full weather-email automation.
"""

import asyncio
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from core.agent_manager import AgentManager
from agents.email_agent import EmailAgent


async def test_email_configuration():
    """Test the email configuration."""
    print("🧪 Testing Email Configuration")
    print("=" * 40)
    
    # Load configuration from environment
    smtp_config = {
        "host": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("EMAIL_USERNAME"),
        "password": os.getenv("EMAIL_PASSWORD"),
        "use_tls": os.getenv("SMTP_USE_TLS", "True").lower() == "true",
        "use_ssl": os.getenv("SMTP_USE_SSL", "False").lower() == "true"
    }
    
    sender_email = os.getenv("SENDER_EMAIL", os.getenv("EMAIL_USERNAME"))
    test_recipient = input("Enter test recipient email (or press Enter to use sender): ").strip()
    if not test_recipient:
        test_recipient = sender_email
    
    print(f"\n📧 Testing email from: {sender_email}")
    print(f"📧 Testing email to: {test_recipient}")
    print(f"🔧 SMTP Server: {smtp_config['host']}:{smtp_config['port']}")
    
    # Create email agent
    email_agent = EmailAgent("test_email_agent", smtp_config)
    
    try:
        # Start the agent
        print("\n🚀 Starting email agent...")
        await email_agent.start()
        print("✅ Email agent started successfully")
        
        # Set SMTP configuration in context
        if email_agent.context_manager:
            from core.context_manager import ContextScope
            email_agent.context_manager.set(
                "smtp_config",
                smtp_config,
                scope=ContextScope.GLOBAL
            )
        
        # Compose test email
        print("\n📝 Composing test email...")
        test_email_data = {
            "sender": sender_email,
            "recipients": [test_recipient],
            "subject": f"Test Email from Agentic Framework - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "body": f"""
Hello!

This is a test email from the Agentic Framework.

If you're receiving this email, your email configuration is working correctly! 🎉

Test Details:
- Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- SMTP Server: {smtp_config['host']}
- Port: {smtp_config['port']}
- TLS: {smtp_config['use_tls']}

You can now run the weather-email automation demo.

Best regards,
Agentic Framework Test Bot 🤖
""",
            "priority": "normal"
        }
        
        # Send the test email
        print("📤 Sending test email...")
        from core.message_bus import Message
        message = Message(
            sender="test",
            recipient="test_email_agent",
            type="compose_email",
            data={"email_data": test_email_data}
        )
        response = await email_agent.process_message(message)
        
        if response and response.get("success"):
            email_id = response.get("email_id")
            print(f"✅ Test email composed with ID: {email_id}")
            
            # Send the email
            send_message = Message(
                sender="test",
                recipient="test_email_agent",
                type="send_email",
                data={"email_id": email_id}
            )
            send_response = await email_agent.process_message(send_message)
            
            if send_response and send_response.get("success"):
                print("✅ Test email sent successfully!")
                print(f"📧 Check {test_recipient} for the test email")
                return True
            else:
                print(f"❌ Failed to send email: {send_response.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Failed to compose email: {response.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return False
    finally:
        # Cleanup
        await email_agent.stop()
        print("🧹 Email agent stopped")


async def main():
    """Main test function."""
    print("🌤️ Email Configuration Test")
    print("This will test your email setup before running the weather automation.\n")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("Please run 'python email_config.py' first to set up your email configuration.")
        return
    
    # Run the test
    success = await test_email_configuration()
    
    if success:
        print("\n🎉 Email configuration test passed!")
        print("You can now run the weather_email_demo.py script.")
    else:
        print("\n❌ Email configuration test failed!")
        print("Please check your email settings and try again.")
        print("Common issues:")
        print("- Incorrect username/password")
        print("- Need to use App Password for Gmail")
        print("- Firewall blocking SMTP port")
        print("- 2FA not enabled for Gmail")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
