"""Topic repository interface for dependency inversion."""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..entities.topic import Topic, TopicCategory
from ..entities.session import ProficiencyLevel


class TopicRepositoryInterface(ABC):
    """Abstract interface for topic repository operations.
    
    This interface defines the contract for topic data operations,
    following the dependency inversion principle.
    """
    
    @abstractmethod
    async def create(self, topic: Topic) -> Topic:
        """Create a new topic in the repository.
        
        Args:
            topic: Topic entity to create
            
        Returns:
            Topic: Created topic
            
        Raises:
            TopicAlreadyExistsException: If topic ID already exists
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, topic_id: str) -> Optional[Topic]:
        """Retrieve a topic by its ID.
        
        Args:
            topic_id: ID of the topic to retrieve
            
        Returns:
            Topic if found, None otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Topic]:
        """Retrieve all topics with optional pagination.
        
        Args:
            limit: Maximum number of topics to return
            offset: Number of topics to skip
            
        Returns:
            List of topic entities
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_category(self, category: TopicCategory, limit: Optional[int] = None) -> List[Topic]:
        """Get topics by category.
        
        Args:
            category: Topic category to filter by
            limit: Maximum number of topics to return
            
        Returns:
            List of topics in the specified category
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_difficulty_level(
        self, 
        difficulty_level: ProficiencyLevel, 
        limit: Optional[int] = None
    ) -> List[Topic]:
        """Get topics by difficulty level.
        
        Args:
            difficulty_level: Proficiency level to filter by
            limit: Maximum number of topics to return
            
        Returns:
            List of topics at the specified difficulty level
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_suitable_for_level(
        self, 
        user_level: ProficiencyLevel, 
        limit: Optional[int] = None
    ) -> List[Topic]:
        """Get topics suitable for a user's proficiency level.
        
        Args:
            user_level: User's proficiency level
            limit: Maximum number of topics to return
            
        Returns:
            List of topics suitable for the user's level
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def search_by_keyword(self, keyword: str, limit: Optional[int] = None) -> List[Topic]:
        """Search topics by keyword.
        
        Args:
            keyword: Keyword to search for in topic keywords, name, or description
            limit: Maximum number of topics to return
            
        Returns:
            List of topics matching the keyword
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_categories_and_level(
        self, 
        categories: List[TopicCategory], 
        user_level: ProficiencyLevel,
        limit: Optional[int] = None
    ) -> List[Topic]:
        """Get topics by categories and suitable for user level.
        
        Args:
            categories: List of topic categories to filter by
            user_level: User's proficiency level
            limit: Maximum number of topics to return
            
        Returns:
            List of topics matching categories and suitable for level
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_related_topics(self, topic_id: str, limit: Optional[int] = None) -> List[Topic]:
        """Get topics related to a specific topic.
        
        Args:
            topic_id: ID of the topic to find related topics for
            limit: Maximum number of related topics to return
            
        Returns:
            List of related topics
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def update(self, topic: Topic) -> Topic:
        """Update an existing topic in the repository.
        
        Args:
            topic: Topic entity with updated data
            
        Returns:
            Updated topic entity
            
        Raises:
            TopicNotFoundException: If topic doesn't exist
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, topic_id: str) -> bool:
        """Delete a topic from the repository.
        
        Args:
            topic_id: ID of the topic to delete
            
        Returns:
            True if topic was deleted, False if not found
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def exists(self, topic_id: str) -> bool:
        """Check if a topic exists with the given ID.
        
        Args:
            topic_id: Topic ID to check
            
        Returns:
            True if topic exists, False otherwise
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get the total count of topics in the repository.
        
        Returns:
            Total number of topics
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def count_by_category(self, category: TopicCategory) -> int:
        """Count topics in a specific category.
        
        Args:
            category: Topic category to count
            
        Returns:
            Number of topics in the category
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_random_topics(
        self, 
        count: int, 
        category: Optional[TopicCategory] = None,
        difficulty_level: Optional[ProficiencyLevel] = None
    ) -> List[Topic]:
        """Get random topics with optional filtering.
        
        Args:
            count: Number of random topics to return
            category: Optional category filter
            difficulty_level: Optional difficulty level filter
            
        Returns:
            List of random topics
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass
    
    @abstractmethod
    async def get_popular_topics(
        self, 
        limit: int = 10,
        user_level: Optional[ProficiencyLevel] = None
    ) -> List[Topic]:
        """Get popular topics based on usage statistics.
        
        Args:
            limit: Maximum number of topics to return
            user_level: Optional user level filter
            
        Returns:
            List of popular topics
            
        Raises:
            RepositoryException: If database operation fails
        """
        pass