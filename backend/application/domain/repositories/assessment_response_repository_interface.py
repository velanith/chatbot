"""Assessment response repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.assessment import AssessmentResponse


class AssessmentResponseRepositoryInterface(ABC):
    """Interface for assessment response repository operations."""
    
    @abstractmethod
    async def create(self, response: AssessmentResponse) -> AssessmentResponse:
        """Create a new assessment response.
        
        Args:
            response: Assessment response to create
            
        Returns:
            Created assessment response with ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, response_id: UUID) -> Optional[AssessmentResponse]:
        """Get assessment response by ID.
        
        Args:
            response_id: Assessment response ID
            
        Returns:
            Assessment response if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_session_id(self, session_id: UUID) -> List[AssessmentResponse]:
        """Get all responses for an assessment session.
        
        Args:
            session_id: Assessment session ID
            
        Returns:
            List of assessment responses
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[AssessmentResponse]:
        """Get all responses for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of assessment responses
        """
        pass
    
    @abstractmethod
    async def update(self, response: AssessmentResponse) -> AssessmentResponse:
        """Update an existing assessment response.
        
        Args:
            response: Assessment response to update
            
        Returns:
            Updated assessment response
        """
        pass
    
    @abstractmethod
    async def delete(self, response_id: UUID) -> bool:
        """Delete an assessment response.
        
        Args:
            response_id: Assessment response ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_latest_by_session(self, session_id: UUID) -> Optional[AssessmentResponse]:
        """Get the latest response for an assessment session.
        
        Args:
            session_id: Assessment session ID
            
        Returns:
            Latest assessment response if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def count_by_session(self, session_id: UUID) -> int:
        """Count responses for an assessment session.
        
        Args:
            session_id: Assessment session ID
            
        Returns:
            Number of responses for the session
        """
        pass