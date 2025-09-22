"""Message repository interface for dependency inversion."""

from abc import ABC, abstractmethod
from typing import Optional, List
import uuid

from ..entities.message import Message


class MessageRepositoryInterface(ABC):
    """Abstract interface for message repository operations.
    
    This interface defines the contract for message data operations,
    following the dependency inversion principle.
    """
    
    @abstractmethod
    async def create(self, message: Message) -> Message:
        """Create a new message in the repository.
        
        Args:
            message: Message entity to create
            
        Returns:
            Message: Created message with assigned ID
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        """Retrieve a message by its ID.
        
        Args:
            message_id: UUID of the message to retrieve
            
        Returns:
            Message if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_session(self, session_id: uuid.UUID) -> List[Message]:
        """Get all messages for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            List of all messages ordered by created_at asc
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_session_paginated(
        self, 
        session_id: uuid.UUID, 
        offset: int = 0,
        limit: int = 20
    ) -> List[Message]:
        """Get messages for a session with pagination.
        
        Args:
            session_id: UUID of the session
            offset: Number of messages to skip
            limit: Maximum number of messages to return
            
        Returns:
            List of messages ordered by created_at desc (most recent first)
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def count_by_session(self, session_id: uuid.UUID) -> int:
        """Count total messages for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Total number of messages in the session
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_session_id(
        self, 
        session_id: uuid.UUID, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Message]:
        """Get messages for a session with pagination.
        
        Args:
            session_id: UUID of the session
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of messages ordered by created_at asc
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_recent_by_session_id(self, session_id: uuid.UUID, count: int = 10) -> List[Message]:
        """Get the most recent messages for a session.
        
        Args:
            session_id: UUID of the session
            count: Number of recent messages to return (default 10)
            
        Returns:
            List of recent messages ordered by created_at desc
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_conversation_history(
        self, 
        session_id: uuid.UUID,
        before_message_id: Optional[uuid.UUID] = None,
        limit: int = 50
    ) -> List[Message]:
        """Get conversation history with cursor-based pagination.
        
        Args:
            session_id: UUID of the session
            before_message_id: Get messages before this message ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages ordered by created_at desc
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update(self, message: Message) -> Message:
        """Update an existing message in the repository.
        
        Args:
            message: Message entity with updated data
            
        Returns:
            Updated message entity
            
        Raises:
            MessageNotFoundException: If message doesn't exist
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, message_id: uuid.UUID) -> bool:
        """Delete a message from the repository.
        
        Args:
            message_id: UUID of the message to delete
            
        Returns:
            True if message was deleted, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def delete_by_session_id(self, session_id: uuid.UUID) -> int:
        """Delete all messages for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Number of messages deleted
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def count_by_session_id(self, session_id: uuid.UUID) -> int:
        """Count total messages for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Total number of messages in the session
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_messages_with_corrections(self, session_id: uuid.UUID) -> List[Message]:
        """Get all messages with corrections for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            List of messages that have corrections
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_messages_with_exercises(self, session_id: uuid.UUID) -> List[Message]:
        """Get all messages with micro exercises for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            List of messages that have micro exercises
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass