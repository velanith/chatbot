"""Topic domain entities for language learning application."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from uuid import UUID

from .validators import validate_required_string, validate_enum_value
from .session import ProficiencyLevel


class TopicCategory(Enum):
    """Categories for conversation topics."""
    DAILY_LIFE = "daily_life"
    TRAVEL = "travel"
    FOOD = "food"
    WORK = "work"
    HOBBIES = "hobbies"
    CULTURE = "culture"
    TECHNOLOGY = "technology"
    HEALTH = "health"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    FAMILY = "family"
    SHOPPING = "shopping"
    WEATHER = "weather"
    NEWS = "news"


@dataclass
class Topic:
    """Domain entity representing a conversation topic."""
    
    id: str
    name: str
    description: str
    category: TopicCategory
    difficulty_level: ProficiencyLevel
    keywords: List[str] = field(default_factory=list)
    conversation_starters: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate topic data after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate topic fields."""
        # Validate required string fields
        validate_required_string(self.id, "Topic ID")
        validate_required_string(self.name, "Topic name")
        validate_required_string(self.description, "Topic description")
        
        # Validate enums
        validate_enum_value(self.category, TopicCategory, "Topic category")
        validate_enum_value(self.difficulty_level, ProficiencyLevel, "Difficulty level")
        
        # Validate lists
        if not isinstance(self.keywords, list):
            raise ValueError("Keywords must be a list")
        
        if not isinstance(self.conversation_starters, list):
            raise ValueError("Conversation starters must be a list")
            
        if not isinstance(self.related_topics, list):
            raise ValueError("Related topics must be a list")
        
        # Validate keyword content
        for keyword in self.keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                raise ValueError("All keywords must be non-empty strings")
        
        # Validate conversation starter content
        for starter in self.conversation_starters:
            if not isinstance(starter, str) or not starter.strip():
                raise ValueError("All conversation starters must be non-empty strings")
        
        # Validate related topic IDs
        for topic_id in self.related_topics:
            if not isinstance(topic_id, str) or not topic_id.strip():
                raise ValueError("All related topic IDs must be non-empty strings")
    
    def add_keyword(self, keyword: str) -> None:
        """Add a keyword to the topic."""
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("Keyword must be a non-empty string")
        
        keyword = keyword.strip().lower()
        if keyword not in [k.lower() for k in self.keywords]:
            self.keywords.append(keyword)
    
    def add_conversation_starter(self, starter: str) -> None:
        """Add a conversation starter to the topic."""
        if not isinstance(starter, str) or not starter.strip():
            raise ValueError("Conversation starter must be a non-empty string")
        
        starter = starter.strip()
        if starter not in self.conversation_starters:
            self.conversation_starters.append(starter)
    
    def add_related_topic(self, topic_id: str) -> None:
        """Add a related topic ID."""
        if not isinstance(topic_id, str) or not topic_id.strip():
            raise ValueError("Topic ID must be a non-empty string")
        
        topic_id = topic_id.strip()
        if topic_id != self.id and topic_id not in self.related_topics:
            self.related_topics.append(topic_id)
    
    def is_suitable_for_level(self, user_level: ProficiencyLevel) -> bool:
        """Check if topic is suitable for user's proficiency level."""
        level_order = {
            ProficiencyLevel.A1: 1,
            ProficiencyLevel.A2: 2,
            ProficiencyLevel.B1: 3,
            ProficiencyLevel.B2: 4,
            ProficiencyLevel.C1: 5,
            ProficiencyLevel.C2: 6
        }
        
        topic_level = level_order[self.difficulty_level]
        user_level_num = level_order[user_level]
        
        # Topic is suitable if it's at or slightly above user's level
        return topic_level <= user_level_num + 1