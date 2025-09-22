"""Memory management service for conversation caching."""

import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio
import logging

from src.domain.entities.message import Message
from src.domain.entities.session import Session
from src.domain.repositories.message_repository_interface import MessageRepositoryInterface
from .memory_config import MemoryConfig


logger = logging.getLogger(__name__)


class LRUCache:
    """LRU (Least Recently Used) cache implementation."""
    
    def __init__(self, capacity: int = 100):
        """Initialize LRU cache with given capacity.
        
        Args:
            capacity: Maximum number of items to store
        """
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[any]:
        """Get item from cache and mark as recently used.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if key not in self.cache:
            return None
        
        # Move to end (most recently used)
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def put(self, key: str, value: any) -> None:
        """Put item in cache, evicting LRU item if necessary.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing item
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            # Remove least recently used item
            self.cache.popitem(last=False)
        
        # Add new item (most recently used)
        self.cache[key] = value
    
    def remove(self, key: str) -> bool:
        """Remove item from cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if item was removed, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all items from cache."""
        self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)
    
    def keys(self) -> List[str]:
        """Get all cache keys."""
        return list(self.cache.keys())


class ConversationSummary:
    """Conversation summary data structure."""
    
    def __init__(
        self,
        session_id: uuid.UUID,
        summary: str,
        message_count: int,
        last_updated: datetime,
        key_topics: List[str] = None
    ):
        """Initialize conversation summary.
        
        Args:
            session_id: UUID of the session
            summary: Text summary of the conversation
            message_count: Number of messages summarized
            last_updated: When summary was last updated
            key_topics: List of key topics discussed
        """
        self.session_id = session_id
        self.summary = summary
        self.message_count = message_count
        self.last_updated = last_updated
        self.key_topics = key_topics or []
    
    def to_dict(self) -> dict:
        """Convert summary to dictionary."""
        return {
            'session_id': str(self.session_id),
            'summary': self.summary,
            'message_count': self.message_count,
            'last_updated': self.last_updated.isoformat(),
            'key_topics': self.key_topics
        }


class MemoryManager:
    """Memory manager for conversation caching and overflow handling."""
    
    def __init__(
        self,
        message_repository: MessageRepositoryInterface,
        config: Optional[MemoryConfig] = None
    ):
        """Initialize memory manager.
        
        Args:
            message_repository: Repository for persistent message storage
            config: Memory management configuration
        """
        self.message_repository = message_repository
        self.config = config or MemoryConfig()
        self.config.validate()
        
        # LRU cache for recent messages by session
        self.message_cache: LRUCache = LRUCache(self.config.cache_capacity)
        
        # Cache for conversation summaries
        self.summary_cache: Dict[str, ConversationSummary] = {}
        
        # Track message counts per session
        self.message_counts: Dict[str, int] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.overflow_persisted = 0
    
    async def add_message(self, message: Message) -> None:
        """Add a message to memory cache.
        
        Args:
            message: Message to add to cache
        """
        async with self._lock:
            session_key = str(message.session_id)
            
            # Get current messages for session
            cached_messages = self.message_cache.get(session_key) or []
            
            # Add new message
            cached_messages.append(message)
            
            # Keep only recent messages
            if len(cached_messages) > self.config.messages_per_session:
                # Move oldest messages to database
                overflow_messages = cached_messages[:-self.config.messages_per_session]
                await self._persist_overflow_messages(overflow_messages)
                
                # Keep only recent messages in cache
                cached_messages = cached_messages[-self.config.messages_per_session:]
            
            # Update cache
            self.message_cache.put(session_key, cached_messages)
            
            # Update message count
            self.message_counts[session_key] = self.message_counts.get(session_key, 0) + 1
            
            # Check if we need to create/update summary
            if self.message_counts[session_key] >= self.config.summary_threshold:
                await self._update_conversation_summary(message.session_id)
    
    async def get_recent_messages(self, session_id: uuid.UUID, count: int = None) -> List[Message]:
        """Get recent messages for a session.
        
        Args:
            session_id: UUID of the session
            count: Number of messages to return (default: all cached)
            
        Returns:
            List of recent messages
        """
        async with self._lock:
            session_key = str(session_id)
            cached_messages = self.message_cache.get(session_key) or []
            
            if count is None:
                return cached_messages.copy()
            
            return cached_messages[-count:] if cached_messages else []
    
    async def get_conversation_context(self, session_id: uuid.UUID) -> Tuple[List[Message], Optional[str]]:
        """Get conversation context (recent messages + summary).
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Tuple of (recent_messages, summary_text)
        """
        async with self._lock:
            # Get recent messages from cache directly (avoid nested lock)
            session_key = str(session_id)
            cached_messages = self.message_cache.get(session_key) or []
            recent_messages = cached_messages.copy()
            
            # Get summary if available
            summary = self.summary_cache.get(session_key)
            summary_text = summary.summary if summary else None
            
            return recent_messages, summary_text
    
    async def get_conversation_summary(self, session_id: uuid.UUID) -> Optional[str]:
        """Get conversation summary for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Summary text or None if no summary exists
        """
        async with self._lock:
            session_key = str(session_id)
            summary = self.summary_cache.get(session_key)
            return summary.summary if summary else None
    
    async def clear_session_cache(self, session_id: uuid.UUID) -> None:
        """Clear cache for a specific session.
        
        Args:
            session_id: UUID of the session to clear
        """
        async with self._lock:
            session_key = str(session_id)
            
            # Get cached messages before clearing
            cached_messages = self.message_cache.get(session_key) or []
            
            # Persist any remaining cached messages
            if cached_messages:
                await self._persist_overflow_messages(cached_messages)
            
            # Clear from caches
            self.message_cache.remove(session_key)
            if session_key in self.summary_cache:
                del self.summary_cache[session_key]
            if session_key in self.message_counts:
                del self.message_counts[session_key]
    
    async def load_session_context(self, session_id: uuid.UUID) -> None:
        """Load session context from database into cache.
        
        Args:
            session_id: UUID of the session to load
        """
        session_key = str(session_id)
        
        # Check if already cached (without lock for performance)
        if self.message_cache.get(session_key):
            return
        
        try:
            # Load recent messages from database (outside lock)
            recent_messages = await self.message_repository.get_recent_by_session_id(
                session_id, self.config.messages_per_session
            )
            
            total_count = await self.message_repository.count_by_session_id(session_id)
            
            # Now acquire lock to update cache
            async with self._lock:
                # Double-check if still not cached
                if not self.message_cache.get(session_key):
                    # Cache the messages
                    if recent_messages:
                        self.message_cache.put(session_key, recent_messages)
                    
                    # Update message count
                    self.message_counts[session_key] = total_count
            
            logger.info(f"Loaded {len(recent_messages)} messages for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to load session context: {e}")
            raise
    
    async def get_cache_stats(self) -> dict:
        """Get memory cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        async with self._lock:
            total_cached_messages = sum(
                len(messages) for messages in self.message_cache.cache.values()
                if isinstance(messages, list)
            )
            
            return {
                'cached_sessions': self.message_cache.size(),
                'total_cached_messages': total_cached_messages,
                'cache_capacity': self.config.cache_capacity,
                'messages_per_session': self.config.messages_per_session,
                'cached_summaries': len(self.summary_cache),
                'session_message_counts': dict(self.message_counts),
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'overflow_persisted': self.overflow_persisted
            }
    
    async def _persist_overflow_messages(self, messages: List[Message]) -> None:
        """Persist overflow messages to database.
        
        Args:
            messages: List of messages to persist
        """
        try:
            for message in messages:
                await self.message_repository.create(message)
            
            self.overflow_persisted += len(messages)
            if self.config.log_cache_operations:
                logger.info(f"Persisted {len(messages)} overflow messages to database")
            
        except Exception as e:
            logger.error(f"Failed to persist overflow messages: {e}")
            raise
    
    async def _update_conversation_summary(self, session_id: uuid.UUID) -> None:
        """Update conversation summary for a session.
        
        Args:
            session_id: UUID of the session
        """
        try:
            session_key = str(session_id)
            
            # Get all messages for the session (from cache and database)
            cached_messages = self.message_cache.get(session_key) or []
            
            # For now, create a simple summary
            # In a real implementation, this would use an LLM to generate summaries
            message_count = self.message_counts.get(session_key, 0)
            
            if message_count < self.config.summary_threshold:
                return
            
            # Create basic summary
            user_messages = [msg for msg in cached_messages if msg.is_user_message()]
            assistant_messages = [msg for msg in cached_messages if msg.is_assistant_message()]
            
            summary_text = f"Conversation with {len(user_messages)} user messages and {len(assistant_messages)} assistant responses. "
            
            # Extract key topics from recent messages
            key_topics = []
            for message in cached_messages[-5:]:  # Last 5 messages
                if len(message.content) > 20:  # Skip very short messages
                    # Simple keyword extraction (in real implementation, use NLP)
                    words = message.content.lower().split()
                    content_words = [w for w in words if len(w) > 4][:3]
                    key_topics.extend(content_words)
            
            # Remove duplicates and limit
            key_topics = list(set(key_topics))[:5]
            
            if key_topics:
                summary_text += f"Key topics: {', '.join(key_topics)}."
            
            # Create summary object
            summary = ConversationSummary(
                session_id=session_id,
                summary=summary_text,
                message_count=message_count,
                last_updated=datetime.utcnow(),
                key_topics=key_topics
            )
            
            # Cache the summary
            self.summary_cache[session_key] = summary
            
            logger.info(f"Updated conversation summary for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to update conversation summary: {e}")
            # Don't raise - summary generation is not critical 
    
    async def initialize_session_cache(self, session_id: uuid.UUID) -> None:
        """Initialize cache for a new session.
        
        Args:
            session_id: Session ID to initialize cache for
        """
        if session_id not in self.session_caches:
            self.session_caches[session_id] = LRUCache(
                max_size=self.config.max_messages_per_session
            )
            logger.info(f"Initialized cache for session {session_id}")
    
    async def get_session_cache_status(self, session_id: uuid.UUID) -> Dict[str, Any]:
        """Get cache status for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Cache status information
        """
        if session_id in self.session_caches:
            cache = self.session_caches[session_id]
            return {
                'exists': True,
                'message_count': len(cache.messages),
                'max_capacity': cache.max_size,
                'is_full': len(cache.messages) >= cache.max_size
            }
        else:
            return {
                'exists': False,
                'message_count': 0,
                'max_capacity': 0,
                'is_full': False
            }