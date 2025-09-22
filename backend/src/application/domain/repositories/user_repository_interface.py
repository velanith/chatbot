"""User repository interface for dependency inversion."""

from abc import ABC, abstractmethod
from typing import Optional, List
import uuid

from ..entities.user import User
from ..entities.language_preferences import LanguagePreferences
from ..entities.topic import TopicCategory
from ..entities.session import ProficiencyLevel


class UserRepositoryInterface(ABC):
    """Abstract interface for user repository operations.
    
    This interface defines the contract for user data operations,
    following the dependency inversion principle. Concrete implementations
    will handle the actual data persistence logic.
    """
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user in the repository.
        
        Args:
            user: User entity to create
            
        Returns:
            User: Created user with assigned ID
            
        Raises:
            UserAlreadyExistsException: If username or email already exists
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Retrieve a user by their ID.
        
        Args:
            user_id: UUID of the user to retrieve
            
        Returns:
            User if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by their username.
        
        Args:
            username: Username to search for
            
        Returns:
            User if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user in the repository.
        
        Args:
            user: User entity with updated data
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user doesn't exist
            UserAlreadyExistsException: If username/email conflicts with another user
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: uuid.UUID) -> bool:
        """Delete a user from the repository.
        
        Args:
            user_id: UUID of the user to delete
            
        Returns:
            True if user was deleted, False if user didn't exist
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if a user exists with the given username.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if a user exists with the given email.
        
        Args:
            email: Email address to check
            
        Returns:
            True if user exists, False otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[User]:
        """Retrieve all users with optional pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of user entities
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get the total count of users in the repository.
        
        Returns:
            Total number of users
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_language_preferences(
        self, 
        user_id: uuid.UUID, 
        native_language: str, 
        target_language: str, 
        proficiency_level: str
    ) -> bool:
        """Update user's language preferences in Polyglot.
        
        Args:
            user_id: UUID of the user
            native_language: User's native language code
            target_language: User's target language code
            proficiency_level: User's proficiency level (A1, A2, B1)
            
        Returns:
            True if preferences were updated, False if user not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_language_preferences(self, user_id: uuid.UUID) -> Optional[dict]:
        """Get user's language preferences from Polyglot.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dictionary with native_language, target_language, proficiency_level
            or None if user not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_full_language_preferences(self, user_id: uuid.UUID) -> Optional[LanguagePreferences]:
        """Get user's complete language preferences.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            LanguagePreferences entity if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_language_preferences_entity(
        self, 
        preferences: LanguagePreferences
    ) -> LanguagePreferences:
        """Update user's complete language preferences.
        
        Args:
            preferences: LanguagePreferences entity with updated data
            
        Returns:
            Updated LanguagePreferences entity
            
        Raises:
            UserNotFoundException: If user doesn't exist
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_preferred_topics(
        self, 
        user_id: uuid.UUID, 
        preferred_topics: List[TopicCategory]
    ) -> bool:
        """Update user's preferred topic categories.
        
        Args:
            user_id: UUID of the user
            preferred_topics: List of preferred topic categories
            
        Returns:
            True if preferences were updated, False if user not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_learning_goals(
        self, 
        user_id: uuid.UUID, 
        learning_goals: List[str]
    ) -> bool:
        """Update user's learning goals.
        
        Args:
            user_id: UUID of the user
            learning_goals: List of learning goal descriptions
            
        Returns:
            True if goals were updated, False if user not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_assessment_status(
        self, 
        user_id: uuid.UUID, 
        assessed_level: Optional[str] = None,
        assessment_completed: bool = False
    ) -> bool:
        """Update user's assessment status and level.
        
        Args:
            user_id: UUID of the user
            assessed_level: Assessed proficiency level (A1, A2, B1, B2, C1, C2)
            assessment_completed: Whether assessment has been completed
            
        Returns:
            True if status was updated, False if user not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update_onboarding_status(self, user_id: uuid.UUID, completed: bool = True) -> bool:
        """Update user's onboarding completion status.
        
        Args:
            user_id: UUID of the user
            completed: Whether onboarding has been completed
            
        Returns:
            True if status was updated, False if user not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_users_by_language_pair(
        self, 
        native_language: str, 
        target_language: str,
        limit: Optional[int] = None
    ) -> List[User]:
        """Get users learning a specific language pair.
        
        Args:
            native_language: Native language code
            target_language: Target language code
            limit: Maximum number of users to return
            
        Returns:
            List of users with the specified language pair
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_users_by_proficiency_level(
        self, 
        proficiency_level: ProficiencyLevel,
        limit: Optional[int] = None
    ) -> List[User]:
        """Get users by proficiency level.
        
        Args:
            proficiency_level: Proficiency level to filter by
            limit: Maximum number of users to return
            
        Returns:
            List of users at the specified proficiency level
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_users_needing_assessment(self, limit: Optional[int] = None) -> List[User]:
        """Get users who haven't completed level assessment.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of users who need to complete assessment
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass