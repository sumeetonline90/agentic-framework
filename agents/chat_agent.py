"""
Chat Agent - Handles conversational interactions and AI-powered responses
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime

from core.base_agent import BaseAgent
from core.message_bus import Message
from core.context_manager import ContextScope


class ChatAgent(BaseAgent):
    """
    Chat agent for handling conversational interactions.
    
    Capabilities:
    - Natural language processing
    - AI-powered responses
    - Conversation history management
    - Intent recognition
    - Multi-turn conversations
    - Context awareness
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        # Set capabilities
        self.capabilities = [
            "chat",
            "conversation",
            "nlp",
            "intent_recognition",
            "context_awareness"
        ]
        
        # Chat-specific configuration
        self.max_history_length = config.get("max_history_length", 50)
        self.response_timeout = config.get("response_timeout", 30)
        self.enable_ai = config.get("enable_ai", True)
        self.ai_service = config.get("ai_service", "openai")
        
        # Conversation state
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Intent patterns
        self.intent_patterns = {
            "greeting": [
                r"\b(hi|hello|hey|good morning|good afternoon|good evening)\b",
                r"\bhow are you\b",
                r"\bnice to meet you\b"
            ],
            "farewell": [
                r"\b(bye|goodbye|see you|take care|have a good day)\b",
                r"\bthanks|thank you\b"
            ],
            "help": [
                r"\bhelp\b",
                r"\bwhat can you do\b",
                r"\bcapabilities\b",
                r"\bsupport\b"
            ],
            "weather": [
                r"\bweather\b",
                r"\btemperature\b",
                r"\bforecast\b",
                r"\b(rain|sunny|cloudy)\b"
            ],
            "time": [
                r"\bwhat time\b",
                r"\bcurrent time\b",
                r"\bdate\b",
                r"\btoday\b"
            ],
            "joke": [
                r"\btell me a joke\b",
                r"\bmake me laugh\b",
                r"\bfunny\b"
            ]
        }
        
        # Response templates
        self.response_templates = {
            "greeting": [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Greetings! I'm here to assist you.",
                "Hello! Nice to meet you. How may I help?"
            ],
            "farewell": [
                "Goodbye! Have a great day!",
                "See you later! Take care!",
                "Bye! It was nice chatting with you!",
                "Farewell! Come back anytime!"
            ],
            "help": [
                "I can help you with various tasks like chatting, answering questions, providing information, and more!",
                "I'm a conversational AI assistant. I can chat, answer questions, help with tasks, and provide information.",
                "I'm here to help! I can assist with conversations, questions, information, and various tasks."
            ],
            "weather": [
                "I'd be happy to help with weather information! However, I don't have access to real-time weather data. You might want to check a weather service or ask another agent that specializes in weather.",
                "Weather information would be great! I don't have weather data access, but I can help you find a weather service or connect you to a weather agent."
            ],
            "time": [
                f"The current time is {datetime.now().strftime('%H:%M:%S')} on {datetime.now().strftime('%B %d, %Y')}.",
                f"It's {datetime.now().strftime('%I:%M %p')} on {datetime.now().strftime('%A, %B %d, %Y')}."
            ],
            "joke": [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a fake noodle? An impasta! 😂",
                "Why did the scarecrow win an award? Because he was outstanding in his field! 🌾",
                "I told my wife she was drawing her eyebrows too high. She looked surprised! 😲"
            ],
            "unknown": [
                "I'm not sure I understand. Could you rephrase that?",
                "I didn't quite catch that. Can you try asking in a different way?",
                "I'm still learning! Could you explain that differently?",
                "I'm not sure how to respond to that. Can you be more specific?"
            ]
        }
    
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Process incoming chat messages"""
        try:
            message_type = message.type
            data = message.data
            
            if message_type == "chat_message":
                return await self._handle_chat_message(data)
            elif message_type == "get_conversation_history":
                return await self._get_conversation_history(data)
            elif message_type == "clear_conversation":
                return await self._clear_conversation(data)
            elif message_type == "get_capabilities":
                return await self._get_capabilities()
            else:
                return {
                    "success": False,
                    "error": f"Unknown message type: {message_type}",
                    "supported_types": ["chat_message", "get_conversation_history", "clear_conversation", "get_capabilities"]
                }
                
        except Exception as e:
            self.logger.error(f"Error processing chat message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_chat_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a chat message from a user"""
        try:
            user_id = data.get("user_id", "anonymous")
            message_text = data.get("message", "").strip()
            session_id = data.get("session_id", user_id)
            
            if not message_text:
                return {
                    "success": False,
                    "error": "Empty message"
                }
            
            # Store message in conversation history
            self._add_to_conversation_history(session_id, "user", message_text)
            
            # Analyze intent
            intent = self._analyze_intent(message_text)
            
            # Generate response
            response = await self._generate_response(message_text, intent, session_id)
            
            # Store response in conversation history
            self._add_to_conversation_history(session_id, "assistant", response)
            
            # Update user session
            self._update_user_session(session_id, user_id, intent)
            
            # Store context for future reference
            if self.context_manager:
                self.context_manager.set(
                    f"last_intent_{session_id}",
                    intent,
                    ContextScope.SESSION,
                    owner=session_id,
                    ttl=3600  # 1 hour
                )
            
            return {
                "success": True,
                "response": response,
                "intent": intent,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error handling chat message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_intent(self, message: str) -> str:
        """Analyze the intent of a message"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return intent
        
        return "unknown"
    
    async def _generate_response(self, message: str, intent: str, session_id: str) -> str:
        """Generate a response based on intent and context"""
        try:
            # Get conversation context
            context = self._get_conversation_context(session_id)
            
            # Check if we should use AI service
            if self.enable_ai and intent == "unknown":
                # Try to get AI response
                ai_response = await self._get_ai_response(message, context)
                if ai_response:
                    return ai_response
            
            # Use template-based responses
            templates = self.response_templates.get(intent, self.response_templates["unknown"])
            
            # Simple template selection (could be enhanced with more sophisticated logic)
            import random
            response = random.choice(templates)
            
            # Personalize response based on context
            response = self._personalize_response(response, session_id)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I'm sorry, I encountered an error while processing your message."
    
    async def _get_ai_response(self, message: str, context: List[Dict[str, Any]]) -> Optional[str]:
        """Get response from AI service"""
        try:
            # This is a placeholder for AI service integration
            # In a real implementation, you would call OpenAI, Claude, or other AI services
            
            # For now, return None to fall back to template responses
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting AI response: {e}")
            return None
    
    def _get_conversation_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        history = self.conversation_history.get(session_id, [])
        return history[-10:]  # Last 10 messages
    
    def _personalize_response(self, response: str, session_id: str) -> str:
        """Personalize response based on user session"""
        session = self.user_sessions.get(session_id, {})
        
        # Add user's name if available
        user_name = session.get("user_name")
        if user_name and "{name}" in response:
            response = response.replace("{name}", user_name)
        
        return response
    
    def _add_to_conversation_history(self, session_id: str, sender: str, message: str):
        """Add message to conversation history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "sender": sender,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Limit history length
        if len(self.conversation_history[session_id]) > self.max_history_length:
            self.conversation_history[session_id] = self.conversation_history[session_id][-self.max_history_length:]
    
    def _update_user_session(self, session_id: str, user_id: str, intent: str):
        """Update user session information"""
        if session_id not in self.user_sessions:
            self.user_sessions[session_id] = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "last_intent": None,
                "common_intents": {}
            }
        
        session = self.user_sessions[session_id]
        session["message_count"] += 1
        session["last_intent"] = intent
        session["last_activity"] = datetime.now().isoformat()
        
        # Track intent frequency
        if intent not in session["common_intents"]:
            session["common_intents"][intent] = 0
        session["common_intents"][intent] += 1
    
    async def _get_conversation_history(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation history for a session"""
        try:
            session_id = data.get("session_id", "default")
            limit = data.get("limit", 50)
            
            history = self.conversation_history.get(session_id, [])
            if limit:
                history = history[-limit:]
            
            return {
                "success": True,
                "session_id": session_id,
                "history": history,
                "total_messages": len(self.conversation_history.get(session_id, []))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _clear_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clear conversation history for a session"""
        try:
            session_id = data.get("session_id", "default")
            
            if session_id in self.conversation_history:
                del self.conversation_history[session_id]
            
            if session_id in self.user_sessions:
                del self.user_sessions[session_id]
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "Conversation history cleared"
            }
            
        except Exception as e:
            self.logger.error(f"Error clearing conversation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        return {
            "success": True,
            "capabilities": self.capabilities,
            "intents_supported": list(self.intent_patterns.keys()),
            "ai_enabled": self.enable_ai,
            "max_history_length": self.max_history_length
        }
    
    async def _on_start(self):
        """Called when agent starts"""
        self.logger.info(f"Chat agent {self.agent_id} started")
        
        # Subscribe to broadcast messages for system-wide announcements
        if self.message_bus:
            await self.message_bus.subscribe_to_broadcasts(self.agent_id)
    
    async def _on_stop(self):
        """Called when agent stops"""
        self.logger.info(f"Chat agent {self.agent_id} stopped")
        
        # Save conversation history to context for persistence
        if self.context_manager:
            for session_id, history in self.conversation_history.items():
                self.context_manager.set(
                    f"conversation_history_{session_id}",
                    history,
                    ContextScope.SESSION,
                    owner=session_id,
                    ttl=86400  # 24 hours
                )

