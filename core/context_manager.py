"""
Context Manager - Shared state and context management for agents
"""

import asyncio
import logging
import json
import pickle
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import weakref


class ContextScope(Enum):
    """Context scope levels"""
    GLOBAL = "global"      # Shared across all agents
    AGENT = "agent"        # Specific to an agent
    SESSION = "session"    # Temporary session data
    USER = "user"          # User-specific data


@dataclass
class ContextItem:
    """Context item with metadata"""
    key: str
    value: Any
    scope: ContextScope
    owner: str  # Agent ID or "system"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None  # Time to live in seconds
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if the item has expired"""
        if self.ttl is None:
            return False
        return (datetime.now() - self.updated_at).total_seconds() > self.ttl
    
    def update(self, value: Any, metadata: Optional[Dict[str, Any]] = None):
        """Update the item value and metadata"""
        self.value = value
        self.updated_at = datetime.now()
        if metadata:
            self.metadata.update(metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "key": self.key,
            "value": self.value,
            "scope": self.scope.value,
            "owner": self.owner,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "ttl": self.ttl,
            "tags": list(self.tags),
            "metadata": self.metadata
        }


class ContextManager:
    """
    Manages shared context and state across all agents.
    
    Features:
    - Multi-scope context storage (global, agent, session, user)
    - Automatic cleanup of expired items
    - Event-driven updates
    - Data persistence
    - Tag-based organization
    - Thread-safe operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger("context_manager")
        
        # Context storage by scope
        self.global_context: Dict[str, ContextItem] = {}
        self.agent_contexts: Dict[str, Dict[str, ContextItem]] = {}
        self.session_contexts: Dict[str, Dict[str, ContextItem]] = {}
        self.user_contexts: Dict[str, Dict[str, ContextItem]] = {}
        
        # Event callbacks
        self.update_callbacks: Dict[str, List[Callable]] = {}
        self.delete_callbacks: Dict[str, List[Callable]] = {}
        
        # Cleanup and maintenance
        self.cleanup_interval = 300  # 5 minutes
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self.total_items = 0
        self.expired_items = 0
        self.update_count = 0
    
    async def start(self):
        """Start the context manager"""
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())
        self.logger.info("Context manager started")
    
    async def stop(self):
        """Stop the context manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Context manager stopped")
    
    def set(self, key: str, value: Any, scope: ContextScope = ContextScope.GLOBAL,
            owner: str = "system", ttl: Optional[int] = None, tags: Optional[Set[str]] = None,
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a context item.
        
        Args:
            key: Item key
            value: Item value
            scope: Context scope
            owner: Owner agent ID
            ttl: Time to live in seconds
            tags: Tags for organization
            metadata: Additional metadata
            
        Returns:
            bool: True if set successfully
        """
        try:
            with self._lock:
                item = ContextItem(
                    key=key,
                    value=value,
                    scope=scope,
                    owner=owner,
                    ttl=ttl,
                    tags=tags or set(),
                    metadata=metadata or {}
                )
                
                # Store in appropriate scope
                if scope == ContextScope.GLOBAL:
                    self.global_context[key] = item
                elif scope == ContextScope.AGENT:
                    if owner not in self.agent_contexts:
                        self.agent_contexts[owner] = {}
                    self.agent_contexts[owner][key] = item
                elif scope == ContextScope.SESSION:
                    if owner not in self.session_contexts:
                        self.session_contexts[owner] = {}
                    self.session_contexts[owner][key] = item
                elif scope == ContextScope.USER:
                    if owner not in self.user_contexts:
                        self.user_contexts[owner] = {}
                    self.user_contexts[owner][key] = item
                
                self.total_items += 1
                self.update_count += 1
                
                # Trigger update callbacks
                self._trigger_callbacks("update", key, item)
                
                self.logger.debug(f"Set context item: {key} in scope {scope.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting context item {key}: {e}")
            return False
    
    def get(self, key: str, scope: ContextScope = ContextScope.GLOBAL,
            owner: str = "system", default: Any = None) -> Any:
        """
        Get a context item.
        
        Args:
            key: Item key
            scope: Context scope
            owner: Owner agent ID
            default: Default value if not found
            
        Returns:
            The item value or default
        """
        try:
            with self._lock:
                item = self._get_item(key, scope, owner)
                
                if item is None or item.is_expired():
                    return default
                
                return item.value
                
        except Exception as e:
            self.logger.error(f"Error getting context item {key}: {e}")
            return default
    
    def get_item(self, key: str, scope: ContextScope = ContextScope.GLOBAL,
                 owner: str = "system") -> Optional[ContextItem]:
        """
        Get a context item with full metadata.
        
        Args:
            key: Item key
            scope: Context scope
            owner: Owner agent ID
            
        Returns:
            ContextItem or None if not found
        """
        try:
            with self._lock:
                item = self._get_item(key, scope, owner)
                
                if item is None or item.is_expired():
                    return None
                
                return item
                
        except Exception as e:
            self.logger.error(f"Error getting context item {key}: {e}")
            return None
    
    def delete(self, key: str, scope: ContextScope = ContextScope.GLOBAL,
               owner: str = "system") -> bool:
        """
        Delete a context item.
        
        Args:
            key: Item key
            scope: Context scope
            owner: Owner agent ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            with self._lock:
                item = self._get_item(key, scope, owner)
                
                if item is None:
                    return False
                
                # Remove from storage
                if scope == ContextScope.GLOBAL:
                    del self.global_context[key]
                elif scope == ContextScope.AGENT:
                    if owner in self.agent_contexts and key in self.agent_contexts[owner]:
                        del self.agent_contexts[owner][key]
                elif scope == ContextScope.SESSION:
                    if owner in self.session_contexts and key in self.session_contexts[owner]:
                        del self.session_contexts[owner][key]
                elif scope == ContextScope.USER:
                    if owner in self.user_contexts and key in self.user_contexts[owner]:
                        del self.user_contexts[owner][key]
                
                self.total_items -= 1
                
                # Trigger delete callbacks
                self._trigger_callbacks("delete", key, item)
                
                self.logger.debug(f"Deleted context item: {key} from scope {scope.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting context item {key}: {e}")
            return False
    
    def exists(self, key: str, scope: ContextScope = ContextScope.GLOBAL,
               owner: str = "system") -> bool:
        """
        Check if a context item exists.
        
        Args:
            key: Item key
            scope: Context scope
            owner: Owner agent ID
            
        Returns:
            bool: True if item exists and is not expired
        """
        try:
            with self._lock:
                item = self._get_item(key, scope, owner)
                return item is not None and not item.is_expired()
                
        except Exception as e:
            self.logger.error(f"Error checking context item {key}: {e}")
            return False
    
    def update(self, key: str, value: Any, scope: ContextScope = ContextScope.GLOBAL,
               owner: str = "system", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing context item.
        
        Args:
            key: Item key
            value: New value
            scope: Context scope
            owner: Owner agent ID
            metadata: Additional metadata
            
        Returns:
            bool: True if updated successfully
        """
        try:
            with self._lock:
                item = self._get_item(key, scope, owner)
                
                if item is None:
                    return False
                
                item.update(value, metadata)
                self.update_count += 1
                
                # Trigger update callbacks
                self._trigger_callbacks("update", key, item)
                
                self.logger.debug(f"Updated context item: {key} in scope {scope.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating context item {key}: {e}")
            return False
    
    def get_by_tags(self, tags: Set[str], scope: ContextScope = ContextScope.GLOBAL,
                    owner: str = "system") -> Dict[str, Any]:
        """
        Get all items that have the specified tags.
        
        Args:
            tags: Set of tags to match
            scope: Context scope
            owner: Owner agent ID
            
        Returns:
            Dict of key-value pairs
        """
        try:
            with self._lock:
                result = {}
                
                if scope == ContextScope.GLOBAL:
                    items = self.global_context.values()
                elif scope == ContextScope.AGENT:
                    items = self.agent_contexts.get(owner, {}).values()
                elif scope == ContextScope.SESSION:
                    items = self.session_contexts.get(owner, {}).values()
                elif scope == ContextScope.USER:
                    items = self.user_contexts.get(owner, {}).values()
                
                for item in items:
                    if not item.is_expired() and tags.issubset(item.tags):
                        result[item.key] = item.value
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error getting items by tags: {e}")
            return {}
    
    def clear_scope(self, scope: ContextScope, owner: str = "system") -> int:
        """
        Clear all items in a scope.
        
        Args:
            scope: Context scope to clear
            owner: Owner agent ID
            
        Returns:
            int: Number of items cleared
        """
        try:
            with self._lock:
                count = 0
                
                if scope == ContextScope.GLOBAL:
                    count = len(self.global_context)
                    self.global_context.clear()
                elif scope == ContextScope.AGENT:
                    if owner in self.agent_contexts:
                        count = len(self.agent_contexts[owner])
                        self.agent_contexts[owner].clear()
                elif scope == ContextScope.SESSION:
                    if owner in self.session_contexts:
                        count = len(self.session_contexts[owner])
                        self.session_contexts[owner].clear()
                elif scope == ContextScope.USER:
                    if owner in self.user_contexts:
                        count = len(self.user_contexts[owner])
                        self.user_contexts[owner].clear()
                
                self.total_items -= count
                self.logger.info(f"Cleared {count} items from scope {scope.value}")
                return count
                
        except Exception as e:
            self.logger.error(f"Error clearing scope {scope.value}: {e}")
            return 0
    
    def on_update(self, key: str, callback: Callable):
        """Register a callback for item updates"""
        if key not in self.update_callbacks:
            self.update_callbacks[key] = []
        self.update_callbacks[key].append(callback)
    
    def on_delete(self, key: str, callback: Callable):
        """Register a callback for item deletions"""
        if key not in self.delete_callbacks:
            self.delete_callbacks[key] = []
        self.delete_callbacks[key].append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get context manager statistics"""
        with self._lock:
            return {
                "total_items": self.total_items,
                "expired_items": self.expired_items,
                "update_count": self.update_count,
                "global_items": len(self.global_context),
                "agent_contexts": len(self.agent_contexts),
                "session_contexts": len(self.session_contexts),
                "user_contexts": len(self.user_contexts),
                "update_callbacks": sum(len(callbacks) for callbacks in self.update_callbacks.values()),
                "delete_callbacks": sum(len(callbacks) for callbacks in self.delete_callbacks.values())
            }
    
    def export_data(self) -> Dict[str, Any]:
        """Export all context data for persistence"""
        with self._lock:
            return {
                "global_context": {k: v.to_dict() for k, v in self.global_context.items()},
                "agent_contexts": {
                    agent: {k: v.to_dict() for k, v in items.items()}
                    for agent, items in self.agent_contexts.items()
                },
                "session_contexts": {
                    session: {k: v.to_dict() for k, v in items.items()}
                    for session, items in self.session_contexts.items()
                },
                "user_contexts": {
                    user: {k: v.to_dict() for k, v in items.items()}
                    for user, items in self.user_contexts.items()
                }
            }
    
    def import_data(self, data: Dict[str, Any]):
        """Import context data from persistence"""
        try:
            with self._lock:
                # Clear existing data
                self.global_context.clear()
                self.agent_contexts.clear()
                self.session_contexts.clear()
                self.user_contexts.clear()
                
                # Import global context
                for key, item_data in data.get("global_context", {}).items():
                    item = self._dict_to_item(item_data)
                    if item and not item.is_expired():
                        self.global_context[key] = item
                
                # Import agent contexts
                for agent, items in data.get("agent_contexts", {}).items():
                    self.agent_contexts[agent] = {}
                    for key, item_data in items.items():
                        item = self._dict_to_item(item_data)
                        if item and not item.is_expired():
                            self.agent_contexts[agent][key] = item
                
                # Import session contexts
                for session, items in data.get("session_contexts", {}).items():
                    self.session_contexts[session] = {}
                    for key, item_data in items.items():
                        item = self._dict_to_item(item_data)
                        if item and not item.is_expired():
                            self.session_contexts[session][key] = item
                
                # Import user contexts
                for user, items in data.get("user_contexts", {}).items():
                    self.user_contexts[user] = {}
                    for key, item_data in items.items():
                        item = self._dict_to_item(item_data)
                        if item and not item.is_expired():
                            self.user_contexts[user][key] = item
                
                self.total_items = (
                    len(self.global_context) +
                    sum(len(items) for items in self.agent_contexts.values()) +
                    sum(len(items) for items in self.session_contexts.values()) +
                    sum(len(items) for items in self.user_contexts.values())
                )
                
                self.logger.info(f"Imported {self.total_items} context items")
                
        except Exception as e:
            self.logger.error(f"Error importing context data: {e}")
    
    def _get_item(self, key: str, scope: ContextScope, owner: str) -> Optional[ContextItem]:
        """Get an item from the appropriate scope"""
        if scope == ContextScope.GLOBAL:
            return self.global_context.get(key)
        elif scope == ContextScope.AGENT:
            return self.agent_contexts.get(owner, {}).get(key)
        elif scope == ContextScope.SESSION:
            return self.session_contexts.get(owner, {}).get(key)
        elif scope == ContextScope.USER:
            return self.user_contexts.get(owner, {}).get(key)
        return None
    
    def _trigger_callbacks(self, event_type: str, key: str, item: ContextItem):
        """Trigger callbacks for an event"""
        callbacks = self.update_callbacks if event_type == "update" else self.delete_callbacks
        
        if key in callbacks:
            for callback in callbacks[key]:
                try:
                    callback(key, item)
                except Exception as e:
                    self.logger.error(f"Error in callback for {key}: {e}")
    
    def _dict_to_item(self, data: Dict[str, Any]) -> Optional[ContextItem]:
        """Convert dictionary to ContextItem"""
        try:
            return ContextItem(
                key=data["key"],
                value=data["value"],
                scope=ContextScope(data["scope"]),
                owner=data["owner"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                ttl=data.get("ttl"),
                tags=set(data.get("tags", [])),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            self.logger.error(f"Error converting dict to item: {e}")
            return None
    
    async def _cleanup_worker(self):
        """Background worker for cleaning up expired items"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_items()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup worker: {e}")
    
    async def _cleanup_expired_items(self):
        """Remove expired items from all scopes"""
        try:
            with self._lock:
                # Clean global context
                expired_keys = [k for k, v in self.global_context.items() if v.is_expired()]
                for key in expired_keys:
                    del self.global_context[key]
                    self.expired_items += 1
                
                # Clean agent contexts
                for agent, items in self.agent_contexts.items():
                    expired_keys = [k for k, v in items.items() if v.is_expired()]
                    for key in expired_keys:
                        del items[key]
                        self.expired_items += 1
                
                # Clean session contexts
                for session, items in self.session_contexts.items():
                    expired_keys = [k for k, v in items.items() if v.is_expired()]
                    for key in expired_keys:
                        del items[key]
                        self.expired_items += 1
                
                # Clean user contexts
                for user, items in self.user_contexts.items():
                    expired_keys = [k for k, v in items.items() if v.is_expired()]
                    for key in expired_keys:
                        del items[key]
                        self.expired_items += 1
                
                if expired_keys:
                    self.logger.debug(f"Cleaned up {len(expired_keys)} expired items")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up expired items: {e}")

