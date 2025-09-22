"""Memory management configuration."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryConfig:
    """Configuration for memory management system."""
    
    # Cache settings
    cache_capacity: int = 50
    """Maximum number of sessions to cache in memory"""
    
    messages_per_session: int = 10
    """Number of recent messages to keep per session in cache"""
    
    # Summary settings
    summary_threshold: int = 20
    """Number of messages before creating/updating conversation summary"""
    
    summary_update_interval: int = 10
    """Update summary every N new messages after threshold"""
    
    # Cleanup settings
    inactive_session_timeout_minutes: int = 60
    """Minutes after which inactive sessions are considered for cleanup"""
    
    cleanup_interval_minutes: int = 30
    """How often to run cleanup of inactive sessions"""
    
    # Performance settings
    max_concurrent_operations: int = 10
    """Maximum concurrent memory operations"""
    
    enable_async_persistence: bool = True
    """Enable asynchronous persistence of overflow messages"""
    
    # Logging settings
    enable_cache_metrics: bool = True
    """Enable collection of cache performance metrics"""
    
    log_cache_operations: bool = False
    """Log individual cache operations (for debugging)"""
    
    def validate(self) -> None:
        """Validate configuration values."""
        if self.cache_capacity <= 0:
            raise ValueError("cache_capacity must be positive")
        
        if self.messages_per_session <= 0:
            raise ValueError("messages_per_session must be positive")
        
        if self.summary_threshold <= 0:
            raise ValueError("summary_threshold must be positive")
        
        if self.summary_update_interval <= 0:
            raise ValueError("summary_update_interval must be positive")
        
        if self.inactive_session_timeout_minutes <= 0:
            raise ValueError("inactive_session_timeout_minutes must be positive")
        
        if self.cleanup_interval_minutes <= 0:
            raise ValueError("cleanup_interval_minutes must be positive")
        
        if self.max_concurrent_operations <= 0:
            raise ValueError("max_concurrent_operations must be positive")
    
    @classmethod
    def for_development(cls) -> 'MemoryConfig':
        """Create configuration optimized for development."""
        return cls(
            cache_capacity=10,
            messages_per_session=5,
            summary_threshold=5,
            summary_update_interval=3,
            inactive_session_timeout_minutes=30,
            cleanup_interval_minutes=15,
            log_cache_operations=True
        )
    
    @classmethod
    def for_production(cls) -> 'MemoryConfig':
        """Create configuration optimized for production."""
        return cls(
            cache_capacity=100,
            messages_per_session=15,
            summary_threshold=30,
            summary_update_interval=10,
            inactive_session_timeout_minutes=120,
            cleanup_interval_minutes=60,
            enable_cache_metrics=True,
            log_cache_operations=False
        )
    
    @classmethod
    def for_testing(cls) -> 'MemoryConfig':
        """Create configuration optimized for testing."""
        return cls(
            cache_capacity=5,
            messages_per_session=3,
            summary_threshold=3,
            summary_update_interval=2,
            inactive_session_timeout_minutes=5,
            cleanup_interval_minutes=2,
            enable_async_persistence=False,  # Synchronous for testing
            log_cache_operations=True
        )