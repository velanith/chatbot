"""Session repository interface for dependency inversion."""

from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
from datetime import datetime

from ..entities.session import Session
from ..entities.topic import Topic


class SessionRepositoryInterface(ABC):
    """Abstract interface for session repository operations.
    
    This interface defines the contract for session data operations,
    following the dependency inversion principle.
    """
    
    @abstractmethod
    async def create(self, session: Session) -> Session:
        """Create a new session in the repository.
        
        Args:
            session: Session entity to create
            
        Returns:
            Session: Created session with assigned ID
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, session_id: uuid.UUID) -> Optional[Session]:
        """Retrieve a session by its ID.
        
        Args:
            session_id: UUID of the session to retrieve
            
        Returns:
            Session if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_active_by_user_id(self, user_id: uuid.UUID) -> Optional[Session]:
        """Get the active session for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Active session if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID, limit: Optional[int] = None) -> List[Session]:
        """Get all sessions for a user.
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions ordered by created_at desc
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update(self, session: Session) -> Session:
        """Update an existing session in the repository.
        
        Args:
            session: Session entity with updated data
            
        Returns:
            Updated session entity
            
        Raises:
            SessionNotFoundException: If session doesn't exist
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def deactivate(self, session_id: uuid.UUID) -> bool:
        """Deactivate a session.
        
        Args:
            session_id: UUID of the session to deactivate
            
        Returns:
            True if session was deactivated, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, session_id: uuid.UUID) -> bool:
        """Delete a session from the repository.
        
        Args:
            session_id: UUID of the session to delete
            
        Returns:
            True if session was deleted, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def count_by_user_id(self, user_id: uuid.UUID) -> int:
        """Count total sessions for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Total number of sessions for the user
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_inactive_sessions(self, older_than_minutes: int) -> List[Session]:
        """Get inactive sessions older than specified minutes.
        
        Args:
            older_than_minutes: Sessions older than this will be returned
            
        Returns:
            List of inactive sessions
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_activity(self, session_id: uuid.UUID, timestamp: datetime) -> bool:
        """Update session activity timestamp.
        
        Args:
            session_id: UUID of the session to update
            timestamp: New activity timestamp
            
        Returns:
            True if session was updated, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_current_topic(self, session_id: uuid.UUID, topic_id: Optional[str]) -> bool:
        """Update the current topic for a session.
        
        Args:
            session_id: UUID of the session to update
            topic_id: ID of the current topic, or None to clear
            
        Returns:
            True if session was updated, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def add_topic_to_history(self, session_id: uuid.UUID, topic_id: str) -> bool:
        """Add a topic to the session's topic history.
        
        Args:
            session_id: UUID of the session to update
            topic_id: ID of the topic to add to history
            
        Returns:
            True if topic was added, False if session not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_topic_history(self, session_id: uuid.UUID) -> List[str]:
        """Get the topic history for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            List of topic IDs in chronological order
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_feedback_count(self, session_id: uuid.UUID, count: int) -> bool:
        """Update the feedback count for a session.
        
        Args:
            session_id: UUID of the session to update
            count: New feedback count
            
        Returns:
            True if session was updated, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def increment_feedback_count(self, session_id: uuid.UUID) -> bool:
        """Increment the feedback count for a session.
        
        Args:
            session_id: UUID of the session to update
            
        Returns:
            True if session was updated, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_last_feedback_message(self, session_id: uuid.UUID, message_number: int) -> bool:
        """Update the last feedback message number for a session.
        
        Args:
            session_id: UUID of the session to update
            message_number: Message number when last feedback was given
            
        Returns:
            True if session was updated, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_sessions_by_topic(self, topic_id: str, limit: Optional[int] = None) -> List[Session]:
        """Get sessions that used a specific topic.
        
        Args:
            topic_id: ID of the topic to search for
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions that used the topic
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_sessions_with_topics(self, user_id: uuid.UUID, limit: Optional[int] = None) -> List[Session]:
        """Get sessions for a user that have topic information.
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions with topic information
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_topic_usage_statistics(self, topic_id: str) -> dict:
        """Get usage statistics for a specific topic.
        
        Args:
            topic_id: ID of the topic
            
        Returns:
            Dictionary with usage statistics (session_count, unique_users, 
            average_duration, last_used)
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass