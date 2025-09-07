#!/usr/bin/env python3
"""
Debug Email Test

A debug version to see what's happening with the email agent.
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


async def debug_email_test():
    """Debug test of email functionality."""
    print("🐛 Debug Email Test")
    print("=" * 30)
    
    # Set up detailed logging
    logging.basicConfig(level=logging.DEBUG)
    
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
    print(f"🔧 TLS: {smtp_config['use_tls']}")
    print(f"🔧 SSL: {smtp_config['use_ssl']}")
    
    # Create and start email agent
    email_agent = EmailAgent("debug_email_agent", smtp_config)
    
    try:
        print("\n🚀 Starting email agent...")
        await email_agent.start()
        print("✅ Email agent started")
        
        # Set SMTP config in context
        if email_agent.context_manager:
            email_agent.context_manager.set(
                "smtp_config",
                smtp_config,
                scope=ContextScope.GLOBAL
            )
            print("✅ SMTP config set in context")
        
        # Create test email data
        test_email_data = {
            "sender": sender_email,
            "recipients": [test_recipient],
            "subject": f"Debug Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "body": f"""
Hello!

This is a debug test email from the Agentic Framework.

Test Details:
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- SMTP: {smtp_config['host']}:{smtp_config['port']}
- TLS: {smtp_config['use_tls']}

Best regards,
Debug Test Bot 🐛
""",
            "priority": "normal"
        }
        
        print(f"\n📝 Test email data: {test_email_data}")
        
        # Create message
        import uuid
        message = Message(
            id=str(uuid.uuid4()),
            sender="debug_test",
            recipient="debug_email_agent",
            type="email_request",
            data={"action": "compose_email", "email_data": test_email_data}
        )
        
        print(f"📨 Message created: {message}")
        
        print("📝 Composing email...")
        response = await email_agent.process_message(message)
        
        print(f"📨 Response received: {response}")
        print(f"📨 Response type: {type(response)}")
        
        if response:
            print(f"📨 Response data: {response.data}")
            print(f"📨 Response success: {response.data.get('success')}")
            print(f"📨 Response error: {response.data.get('error')}")
        
        if response and response.data.get("success"):
            email_id = response.data.get("email_id")
            print(f"✅ Email composed: {email_id}")
            
            # Send the email
            send_message = Message(
                id=str(uuid.uuid4()),
                sender="debug_test",
                recipient="debug_email_agent",
                type="email_request",
                data={"action": "send_email", "email_id": email_id}
            )
            
            print("📤 Sending email...")
            send_response = await email_agent.process_message(send_message)
            
            print(f"📨 Send response: {send_response}")
            
            if send_response and send_response.data.get("success"):
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
    """Main debug function."""
    print("🐛 Debug Email Test")
    print("This will show detailed information about the email process.\n")
    
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("Please run 'python email_config.py' first.")
        return
    
    success = await debug_email_test()
    
    if success:
        print("\n🎉 Debug test passed!")
    else:
        print("\n❌ Debug test failed!")
        print("Check the detailed output above for issues.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Debug test cancelled.")
    except Exception as e:
        print(f"\n❌ Debug test failed: {e}")
