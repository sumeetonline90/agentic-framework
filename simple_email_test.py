#!/usr/bin/env python3
"""
Simple Email Test

A simplified test to verify email functionality works.
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('email_settings.env')

from agents.email_agent import EmailAgent
from core.message_bus import Message
from core.context_manager import ContextScope


async def simple_email_test():
    """Simple test of email functionality."""
    print("🧪 Simple Email Test")
    print("=" * 30)
    
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
    
    print(f"📧 From: {sender_email}")
    print(f"📧 To: {test_recipient}")
    print(f"🔧 SMTP: {smtp_config['host']}:{smtp_config['port']}")
    
    # Create and start email agent
    email_agent = EmailAgent("test_email_agent", smtp_config)
    
    try:
        print("\n🚀 Starting email agent...")
        await email_agent.start()
        print("✅ Email agent started")
        
        # Set SMTP config directly on the agent
        email_agent.smtp_config = smtp_config
        print("✅ SMTP config set directly on agent")
        
        # Create test email data
        test_email_data = {
            "sender": sender_email,
            "recipients": [test_recipient],
            "subject": f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "body": f"""
Hello!

This is a test email from the Agentic Framework.

If you're receiving this, your email configuration works! 🎉

Test Details:
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- SMTP: {smtp_config['host']}:{smtp_config['port']}
- TLS: {smtp_config['use_tls']}

Best regards,
Test Bot 🤖
""",
            "priority": "normal"
        }
        
        # Create message
        import uuid
        message = Message(
            id=str(uuid.uuid4()),
            sender="test",
            recipient="test_email_agent",
            type="email_request",
            data={"action": "compose_email", "email_data": test_email_data}
        )
        
        print("📝 Composing email...")
        response = await email_agent.process_message(message)
        
        if response and response.data.get("action") == "email_composed":
            email_id = response.data.get("email_id")
            print(f"✅ Email composed: {email_id}")
            
            # Send the email
            send_message = Message(
                id=str(uuid.uuid4()),
                sender="test",
                recipient="test_email_agent",
                type="email_request",
                data={"action": "send_email", "email_id": email_id}
            )
            
            print("📤 Sending email...")
            send_response = await email_agent.process_message(send_message)
            
            if send_response and send_response.data.get("action") == "email_sent":
                print("✅ Email sent successfully!")
                print(f"📧 Check {test_recipient} for the test email")
                return True
            else:
                print(f"❌ Send failed: {send_response.data.get('error', 'Unknown error') if send_response else 'No response'}")
                return False
        else:
            print(f"❌ Compose failed: {response.data.get('error', 'Unknown error') if response else 'No response'}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await email_agent.stop()
        print("🧹 Email agent stopped")


async def main():
    """Main test function."""
    print("🌤️ Simple Email Test")
    print("This will test your email setup.\n")
    
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("Please run 'python email_config.py' first.")
        return
    
    success = await simple_email_test()
    
    if success:
        print("\n🎉 Email test passed!")
        print("You can now run the weather_email_demo.py script.")
    else:
        print("\n❌ Email test failed!")
        print("Please check your email settings.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
