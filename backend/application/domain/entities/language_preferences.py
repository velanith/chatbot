"""Language preferences domain entity for user preferences."""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from .validators import validate_language_code
from .topic import TopicCategory
from .session import ProficiencyLevel


@dataclass
class LanguagePreferences:
    """Domain entity representing user's language learning preferences."""
    
    user_id: UUID
    native_language: str
    target_language: str
    proficiency_level: Optional[ProficiencyLevel] = None
    preferred_topics: List[TopicCategory] = field(default_factory=list)
    learning_goals: List[str] = field(default_factory=list)
    assessment_completed: bool = False
    
    def __post_init__(self):
        """Validate language preferences after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate language preferences fields."""
        # Validate user ID
        if not isinstance(self.user_id, UUID):
            raise ValueError("User ID must be a valid UUID")
        
        # Validate language codes
        validate_language_code(self.native_language, "Native language")
        validate_language_code(self.target_language, "Target language")
        
        # Ensure native and target languages are different
        if self.native_language == self.target_language:
            raise ValueError("Native and target languages must be different")
        
        # Validate proficiency level if provided
        if self.proficiency_level is not None:
            if not isinstance(self.proficiency_level, ProficiencyLevel):
                raise ValueError("Proficiency level must be a valid ProficiencyLevel enum")
        
        # Validate preferred topics
        if not isinstance(self.preferred_topics, list):
            raise ValueError("Preferred topics must be a list")
        
        for topic in self.preferred_topics:
            if not isinstance(topic, TopicCategory):
                raise ValueError("All preferred topics must be TopicCategory enum values")
        
        # Validate learning goals
        if not isinstance(self.learning_goals, list):
            raise ValueError("Learning goals must be a list")
        
        for goal in self.learning_goals:
            if not isinstance(goal, str) or not goal.strip():
                raise ValueError("All learning goals must be non-empty strings")
        
        # Validate assessment completed flag
        if not isinstance(self.assessment_completed, bool):
            raise ValueError("Assessment completed must be a boolean")
    
    def add_preferred_topic(self, topic_category: TopicCategory) -> None:
        """Add a preferred topic category."""
        if not isinstance(topic_category, TopicCategory):
            raise ValueError("Topic category must be a TopicCategory enum")
        
        if topic_category not in self.preferred_topics:
            self.preferred_topics.append(topic_category)
    
    def remove_preferred_topic(self, topic_category: TopicCategory) -> None:
        """Remove a preferred topic category."""
        if topic_category in self.preferred_topics:
            self.preferred_topics.remove(topic_category)
    
    def add_learning_goal(self, goal: str) -> None:
        """Add a learning goal."""
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Learning goal must be a non-empty string")
        
        goal = goal.strip()
        if goal not in self.learning_goals:
            self.learning_goals.append(goal)
    
    def remove_learning_goal(self, goal: str) -> None:
        """Remove a learning goal."""
        if goal in self.learning_goals:
            self.learning_goals.remove(goal)
    
    def set_proficiency_level(self, level: ProficiencyLevel) -> None:
        """Set the proficiency level."""
        if not isinstance(level, ProficiencyLevel):
            raise ValueError("Level must be a valid ProficiencyLevel enum")
        
        self.proficiency_level = level
    
    def mark_assessment_completed(self) -> None:
        """Mark the assessment as completed."""
        self.assessment_completed = True
    
    def has_preferences_set(self) -> bool:
        """Check if basic preferences are set."""
        return (
            self.native_language is not None and
            self.target_language is not None and
            self.proficiency_level is not None
        )
    
    def get_language_pair(self) -> tuple[str, str]:
        """Get the language pair as a tuple."""
        return (self.native_language, self.target_language)