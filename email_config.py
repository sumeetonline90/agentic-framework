#!/usr/bin/env python3
"""
Email Configuration Helper

This script helps you configure email settings for the Weather-Email demo.
It will guide you through setting up Gmail or other email providers.
"""

import os
import getpass
from typing import Dict, Any


def get_email_config() -> Dict[str, Any]:
    """Get email configuration from user input."""
    print("📧 Email Configuration Setup")
    print("=" * 40)
    
    # Email provider selection
    print("\nSelect your email provider:")
    print("1. Gmail (Recommended)")
    print("2. Outlook/Hotmail")
    print("3. Yahoo")
    print("4. Custom SMTP")
    
    choice = input("Enter your choice (1-4): ").strip()
    
    config = {}
    
    if choice == "1":  # Gmail
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_use_tls": True,
            "smtp_use_ssl": False
        }
        print("\n📋 Gmail Configuration (Based on Google Documentation):")
        print("- SMTP Server: smtp.gmail.com")
        print("- Port: 587 (TLS) - Recommended")
        print("- Alternative: Port 465 (SSL)")
        print("- Authentication: OAuth 2.0 or App Password")
        print("- You'll need to use an App Password (not your regular password)")
        print("- Reference: https://developers.google.com/workspace/gmail/imap/imap-smtp")
        
    elif choice == "2":  # Outlook
        config = {
            "smtp_server": "smtp-mail.outlook.com",
            "smtp_port": 587,
            "smtp_use_tls": True,
            "smtp_use_ssl": False
        }
        print("\n📋 Outlook Configuration:")
        print("- SMTP Server: smtp-mail.outlook.com")
        print("- Port: 587 (TLS)")
        
    elif choice == "3":  # Yahoo
        config = {
            "smtp_server": "smtp.mail.yahoo.com",
            "smtp_port": 587,
            "smtp_use_tls": True,
            "smtp_use_ssl": False
        }
        print("\n📋 Yahoo Configuration:")
        print("- SMTP Server: smtp.mail.yahoo.com")
        print("- Port: 587 (TLS)")
        
    elif choice == "4":  # Custom
        config = {
            "smtp_server": input("Enter SMTP server: ").strip(),
            "smtp_port": int(input("Enter SMTP port: ").strip()),
            "smtp_use_tls": input("Use TLS? (y/n): ").lower() == 'y',
            "smtp_use_ssl": input("Use SSL? (y/n): ").lower() == 'y'
        }
    else:
        print("Invalid choice. Using Gmail defaults.")
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_use_tls": True,
            "smtp_use_ssl": False
        }
    
    # Get email credentials
    print("\n📝 Email Credentials:")
    config["username"] = input("Enter your email address: ").strip()
    config["password"] = getpass.getpass("Enter your password/app password: ")
    
    return config


def save_config_to_env(config: Dict[str, Any]):
    """Save configuration to environment variables."""
    env_content = f"""# Email Configuration for Weather-Email Demo
# Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# SMTP Settings
SMTP_SERVER={config['smtp_server']}
SMTP_PORT={config['smtp_port']}
SMTP_USE_TLS={config['smtp_use_tls']}
SMTP_USE_SSL={config['smtp_use_ssl']}

# Email Credentials
EMAIL_USERNAME={config['username']}
EMAIL_PASSWORD={config['password']}

# Sender Email (same as username)
SENDER_EMAIL={config['username']}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n✅ Configuration saved to .env file")
    print("⚠️  Keep this file secure and don't share it!")


def print_gmail_setup_instructions():
    """Print Gmail App Password setup instructions."""
    print("""
🔐 GMAIL APP PASSWORD SETUP (Based on Google Documentation):

According to https://developers.google.com/workspace/gmail/imap/imap-smtp:

1. Go to your Google Account settings (myaccount.google.com)
2. Navigate to Security → 2-Step Verification
3. At the bottom, select "App passwords"
4. Select "Mail" and "Other (Custom name)"
5. Enter "Agentic Framework" as the name
6. Copy the generated 16-character password
7. Use this password (not your regular Gmail password) in the configuration

📋 Gmail SMTP Settings:
- Server: smtp.gmail.com
- Port: 587 (TLS) or 465 (SSL)
- Authentication: App Password (recommended) or OAuth 2.0
- TLS: Required for port 587

📱 Alternative: Use your regular password if 2FA is not enabled,
   but App Password is more secure and recommended by Google.
""")


def main():
    """Main configuration function."""
    print("🌤️ Weather-Email Demo Configuration")
    print("This will help you set up email settings for the automation.\n")
    
    # Show Gmail setup instructions
    show_gmail_help = input("Do you need Gmail App Password setup instructions? (y/n): ").lower().strip()
    if show_gmail_help == 'y':
        print_gmail_setup_instructions()
        input("Press Enter to continue...")
    
    # Get configuration
    config = get_email_config()
    
    # Show configuration summary
    print("\n📋 Configuration Summary:")
    print(f"SMTP Server: {config['smtp_server']}")
    print(f"Port: {config['smtp_port']}")
    print(f"TLS: {config['smtp_use_tls']}")
    print(f"SSL: {config['smtp_use_ssl']}")
    print(f"Username: {config['username']}")
    print(f"Password: {'*' * len(config['password'])}")
    
    # Confirm and save
    confirm = input("\nSave this configuration? (y/n): ").lower().strip()
    if confirm == 'y':
        save_config_to_env(config)
        print("\n🎉 Configuration complete!")
        print("You can now run the weather_email_demo.py script.")
    else:
        print("Configuration cancelled.")


if __name__ == "__main__":
    main()
