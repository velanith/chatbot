"""Assessment session repository interface for dependency inversion."""

from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
from datetime import datetime

from ..entities.assessment import AssessmentSession, AssessmentStatus, LanguagePair


class AssessmentSessionRepositoryInterface(ABC):
    """Abstract interface for assessment session repository operations.
    
    This interface defines the contract for assessment session data operations,
    following the dependency inversion principle.
    """
    
    @abstractmethod
    async def create(self, session: AssessmentSession) -> AssessmentSession:
        """Create a new assessment session in the repository.
        
        Args:
            session: AssessmentSession entity to create
            
        Returns:
            AssessmentSession: Created session with assigned ID
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, session_id: uuid.UUID) -> Optional[AssessmentSession]:
        """Retrieve an assessment session by its ID.
        
        Args:
            session_id: UUID of the session to retrieve
            
        Returns:
            AssessmentSession if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID, limit: Optional[int] = None) -> List[AssessmentSession]:
        """Get all assessment sessions for a user.
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of sessions to return
            
        Returns:
            List of assessment sessions ordered by created_at desc
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_active_by_user_id(self, user_id: uuid.UUID) -> Optional[AssessmentSession]:
        """Get the active assessment session for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Active assessment session if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_status(self, status: AssessmentStatus, limit: Optional[int] = None) -> List[AssessmentSession]:
        """Get assessment sessions by status.
        
        Args:
            status: Assessment status to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of assessment sessions with the specified status
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_language_pair(
        self, 
        language_pair: LanguagePair, 
        limit: Optional[int] = None
    ) -> List[AssessmentSession]:
        """Get assessment sessions by language pair.
        
        Args:
            language_pair: Language pair to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of assessment sessions for the language pair
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update(self, session: AssessmentSession) -> AssessmentSession:
        """Update an existing assessment session in the repository.
        
        Args:
            session: AssessmentSession entity with updated data
            
        Returns:
            Updated assessment session entity
            
        Raises:
            AssessmentSessionNotFoundException: If session doesn't exist
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, session_id: uuid.UUID) -> bool:
        """Delete an assessment session from the repository.
        
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
        """Count total assessment sessions for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Total number of assessment sessions for the user
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_completed_by_user_id(self, user_id: uuid.UUID) -> List[AssessmentSession]:
        """Get completed assessment sessions for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of completed assessment sessions ordered by completed_at desc
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_latest_by_user_and_language_pair(
        self, 
        user_id: uuid.UUID, 
        language_pair: LanguagePair
    ) -> Optional[AssessmentSession]:
        """Get the latest assessment session for a user and language pair.
        
        Args:
            user_id: UUID of the user
            language_pair: Language pair to filter by
            
        Returns:
            Latest assessment session if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_expired_sessions(self, older_than_hours: int = 24) -> List[AssessmentSession]:
        """Get active assessment sessions that should be expired.
        
        Args:
            older_than_hours: Sessions older than this will be returned
            
        Returns:
            List of active sessions that should be expired
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_status(self, session_id: uuid.UUID, status: AssessmentStatus) -> bool:
        """Update assessment session status.
        
        Args:
            session_id: UUID of the session to update
            status: New status for the session
            
        Returns:
            True if session was updated, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_statistics_by_language_pair(self, language_pair: LanguagePair) -> dict:
        """Get assessment statistics for a language pair.
        
        Args:
            language_pair: Language pair to get statistics for
            
        Returns:
            Dictionary with statistics (total_sessions, completed_sessions, 
            average_duration, level_distribution)
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass