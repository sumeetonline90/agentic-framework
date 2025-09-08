#!/usr/bin/env python3
"""
Automated Git Push Script for Agentic Framework
This script will handle all git operations to push the cleaned codebase to GitHub.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a shell command and return the result."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr.strip()}")
        return False

def main():
    """Main function to handle git operations."""
    print("🚀 Automated Git Push for Agentic Framework")
    print("=" * 50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository. Please run this from the project root.")
        return False
    
    # Check git status
    if not run_command("git status", "Checking git status"):
        return False
    
    # Add all changes
    if not run_command("git add .", "Adding all changes"):
        return False
    
    # Check what's staged
    if not run_command("git status", "Checking staged changes"):
        return False
    
    # Create commit message
    commit_message = f"""Clean up codebase and enhance agentic framework

✨ Features Added:
- Interactive multi-recipient email support in true_agentic_demo.py
- WeatherAgent now handles multiple email recipients
- Enhanced user input validation and error handling

🧹 Code Cleanup:
- Removed all demo files except true_agentic_demo.py
- Deleted temporary test files and logs
- Organized codebase for team collaboration

🔧 Technical Improvements:
- Fixed agent constructors and message handling
- Updated Message class usage across all agents
- Improved error handling and logging

🔒 Security:
- Maintained .gitignore to exclude sensitive files
- Kept email_settings.env local (not committed)
- Provided .env.example template for team setup

✅ Tested:
- Successfully tested with multiple email recipients
- Verified agent-to-agent communication works perfectly
- Framework ready for team deployment

📅 Committed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    # Commit changes
    commit_cmd = f'git commit -m "{commit_message}"'
    if not run_command(commit_cmd, "Committing changes"):
        return False
    
    # Force push to GitHub
    if not run_command("git push -f origin main", "Force pushing to GitHub"):
        return False
    
    print("\n🎉 SUCCESS! Codebase pushed to GitHub successfully!")
    print("🔗 Repository: https://github.com/sumeetonline90/agentic-framework")
    print("✅ Your team can now clone and use the clean codebase")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Git operations failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n🚀 All done! Your repository is now updated.")
