#!/usr/bin/env python3
"""
Quick fix script to add missing _process_message_impl method to all agents
"""

import os

# Method template for each agent
method_templates = {
    "email_agent.py": '''
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for email agent."""
        try:
            action = message.content.get("action")
            
            if action == "compose_email":
                return await self._handle_compose_email(message)
            elif action == "send_email":
                return await self._handle_send_email(message)
            elif action == "schedule_email":
                return await self._handle_schedule_email(message)
            elif action == "create_template":
                return await self._handle_create_template(message)
            elif action == "list_emails":
                return await self._handle_list_emails(message)
            elif action == "delete_email":
                return await self._handle_delete_email(message)
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
''',
    
    "calendar_agent.py": '''
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for calendar agent."""
        try:
            action = message.content.get("action")
            
            if action == "create_event":
                return await self._handle_create_event(message)
            elif action == "update_event":
                return await self._handle_update_event(message)
            elif action == "delete_event":
                return await self._handle_delete_event(message)
            elif action == "list_events":
                return await self._handle_list_events(message)
            elif action == "check_availability":
                return await self._handle_check_availability(message)
            elif action == "create_calendar":
                return await self._handle_create_calendar(message)
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
''',
    
    "data_agent.py": '''
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for data agent."""
        try:
            action = message.content.get("action")
            
            if action == "read_data":
                return await self._handle_read_data(message)
            elif action == "write_data":
                return await self._handle_write_data(message)
            elif action == "analyze_data":
                return await self._handle_analyze_data(message)
            elif action == "transform_data":
                return await self._handle_transform_data(message)
            elif action == "query_data":
                return await self._handle_query_data(message)
            elif action == "add_data_source":
                return await self._handle_add_data_source(message)
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
''',
    
    "weather_agent.py": '''
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
''',
    
    "news_agent.py": '''
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for news agent."""
        try:
            action = message.content.get("action")
            
            if action == "get_latest_news":
                return await self._handle_get_latest_news(message)
            elif action == "search_news":
                return await self._handle_search_news(message)
            elif action == "categorize_news":
                return await self._handle_categorize_news(message)
            elif action == "add_feed":
                return await self._handle_add_feed(message)
            elif action == "get_trending_topics":
                return await self._handle_get_trending_topics(message)
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
''',
    
    "translation_agent.py": '''
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for translation agent."""
        try:
            action = message.content.get("action")
            
            if action == "translate_text":
                return await self._handle_translate_text(message)
            elif action == "detect_language":
                return await self._handle_detect_language(message)
            elif action == "batch_translate":
                return await self._handle_batch_translate(message)
            elif action == "add_language_model":
                return await self._handle_add_language_model(message)
            elif action == "get_supported_languages":
                return await self._handle_get_supported_languages(message)
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
'''
}

def fix_agent_file(filename, method_template):
    """Add the missing method to an agent file."""
    filepath = f"agents/{filename}"
    
    if not os.path.exists(filepath):
        print(f"File {filepath} not found, skipping...")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if method already exists
    if "_process_message_impl" in content:
        print(f"Method already exists in {filename}, skipping...")
        return
    
    # Find the last method and add our method before it
    lines = content.split('\n')
    
    # Find a good place to insert (before the last method)
    insert_index = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('def ') and not lines[i].strip().startswith('def _'):
            insert_index = i
            break
    
    if insert_index == -1:
        # If no good place found, add at the end before the last line
        insert_index = len(lines) - 1
    
    # Insert the method
    method_lines = method_template.strip().split('\n')
    lines.insert(insert_index, '')
    for line in method_lines:
        lines.insert(insert_index, line)
        insert_index += 1
    
    # Write back to file
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Added _process_message_impl method to {filename}")

def main():
    """Main function to fix all agents."""
    print("Fixing agent files...")
    
    for filename, template in method_templates.items():
        fix_agent_file(filename, template)
    
    print("Done!")

if __name__ == "__main__":
    main()
