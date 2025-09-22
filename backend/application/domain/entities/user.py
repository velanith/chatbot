"""User domain entity with validation logic."""

import re
import uuid
from datetime import datetime
from typing import Optional, Union, List
from dataclasses import dataclass, field

from ..exceptions import ValidationError


@dataclass
class User:
    """User domain entity representing a registered user."""
    
    id: Optional[Union[str, uuid.UUID]]
    username: str
    email: str
    password_hash: str
    is_active: bool = True
    native_language: str = 'TR'
    target_language: str = 'EN'
    proficiency_level: str = 'A2'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # New fields for advanced language learning features
    assessed_level: Optional[str] = None
    assessment_date: Optional[datetime] = None
    preferred_topics: List[str] = field(default_factory=list)
    learning_goals: List[str] = field(default_factory=list)
    onboarding_completed: bool = False
    
    def __post_init__(self) -> None:
        """Validate user data after initialization."""
        self._validate_username()
        self._validate_email()
        self._validate_password_hash()
        self._validate_language_preferences()
        self._validate_assessment_fields()
        self._validate_preference_fields()
        
        # Set timestamps if not provided
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def _validate_username(self) -> None:
        """Validate username according to business rules."""
        if not self.username:
            raise ValidationError("Username cannot be empty")
        
        if len(self.username) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if len(self.username) > 50:
            raise ValidationError("Username cannot be longer than 50 characters")
        
        # Username should contain only alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', self.username):
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores"
            )
    
    def _validate_email(self) -> None:
        """Validate email format according to business rules."""
        if not self.email:
            raise ValidationError("Email cannot be empty")
        
        if len(self.email) > 255:
            raise ValidationError("Email cannot be longer than 255 characters")
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValidationError("Invalid email format")
    
    def _validate_password_hash(self) -> None:
        """Validate password hash."""
        if not self.password_hash:
            raise ValidationError("Password hash cannot be empty")
        
        if len(self.password_hash) < 10:  # Minimum reasonable hash length
            raise ValidationError("Invalid password hash format")
    
    def _validate_language_preferences(self) -> None:
        """Validate user's language preferences for Polyglot learning."""
        # Valid language codes (ISO 639-1)
        valid_languages = {
            'EN', 'ES', 'FR', 'DE', 'IT', 'PT', 'RU', 'ZH', 'JA', 'KO',
            'AR', 'HI', 'TR', 'PL', 'NL', 'SV', 'DA', 'NO', 'FI', 'HE'
        }
        
        # Valid proficiency levels (both CEFR and descriptive, case-insensitive)
        valid_levels = {
            'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 
            'BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'NATIVE',
            'beginner', 'intermediate', 'advanced', 'native'
        }
        
        if not self.native_language or self.native_language.upper() not in valid_languages:
            raise ValidationError(f"Invalid native language: {self.native_language}")
        
        if not self.target_language or self.target_language.upper() not in valid_languages:
            raise ValidationError(f"Invalid target language: {self.target_language}")
        
        # Handle proficiency level - could be enum object or string
        proficiency_value = self.proficiency_level
        if hasattr(self.proficiency_level, 'value'):
            # It's an enum object, get the string value
            proficiency_value = self.proficiency_level.value
        
        if not proficiency_value or proficiency_value not in valid_levels:
            raise ValidationError(f"Invalid proficiency level: {self.proficiency_level}")
        
        if self.native_language.upper() == self.target_language.upper():
            raise ValidationError("Native and target languages must be different")
        
        # Normalize languages to uppercase, keep proficiency level as-is (preserve case)
        self.native_language = self.native_language.upper()
        self.target_language = self.target_language.upper()
        # Store the actual string value, not the enum object
        self.proficiency_level = proficiency_value
    
    def _validate_assessment_fields(self) -> None:
        """Validate assessment-related fields."""
        # Validate assessed_level if provided
        if self.assessed_level is not None:
            valid_levels = {
                'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 
                'BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'NATIVE',
                'beginner', 'intermediate', 'advanced', 'native'
            }
            if self.assessed_level not in valid_levels:
                raise ValidationError(f"Invalid assessed level: {self.assessed_level}")
        
        # Validate assessment_date if provided
        if self.assessment_date is not None:
            if not isinstance(self.assessment_date, datetime):
                raise ValidationError("Assessment date must be a datetime object")
            if self.assessment_date > datetime.utcnow():
                raise ValidationError("Assessment date cannot be in the future")
    
    def _validate_preference_fields(self) -> None:
        """Validate preference-related fields."""
        # Validate preferred_topics
        if self.preferred_topics is not None:
            if not isinstance(self.preferred_topics, list):
                raise ValidationError("Preferred topics must be a list")
            
            # First, filter out empty strings and validate remaining topics
            filtered_topics = []
            for topic in self.preferred_topics:
                if not isinstance(topic, str):
                    raise ValidationError("Each preferred topic must be a string")
                
                stripped_topic = topic.strip()
                if stripped_topic:  # Only process non-empty topics
                    if len(stripped_topic) > 100:
                        raise ValidationError("Each preferred topic cannot exceed 100 characters")
                    if stripped_topic not in filtered_topics:  # Avoid duplicates while preserving order
                        filtered_topics.append(stripped_topic)
            
            self.preferred_topics = filtered_topics
        
        # Validate learning_goals
        if self.learning_goals is not None:
            if not isinstance(self.learning_goals, list):
                raise ValidationError("Learning goals must be a list")
            
            # First, filter out empty strings and validate remaining goals
            filtered_goals = []
            for goal in self.learning_goals:
                if not isinstance(goal, str):
                    raise ValidationError("Each learning goal must be a string")
                
                stripped_goal = goal.strip()
                if stripped_goal:  # Only process non-empty goals
                    if len(stripped_goal) > 200:
                        raise ValidationError("Each learning goal cannot exceed 200 characters")
                    if stripped_goal not in filtered_goals:  # Avoid duplicates while preserving order
                        filtered_goals.append(stripped_goal)
            
            self.learning_goals = filtered_goals
        
        # Validate onboarding_completed
        if not isinstance(self.onboarding_completed, bool):
            raise ValidationError("Onboarding completed must be a boolean")
    
    def update_password_hash(self, new_password_hash: str) -> None:
        """Update the user's password hash."""
        if not new_password_hash:
            raise ValidationError("Password hash cannot be empty")
        
        self.password_hash = new_password_hash
        self.updated_at = datetime.utcnow()
    
    def update_email(self, new_email: str) -> None:
        """Update the user's email address."""
        old_email = self.email
        self.email = new_email
        
        try:
            self._validate_email()
            self.updated_at = datetime.utcnow()
        except ValidationError:
            # Rollback on validation failure
            self.email = old_email
            raise
    
    def update_language_preferences(
        self, 
        native_language: str, 
        target_language: str, 
        proficiency_level: str
    ) -> None:
        """Update the user's language preferences in Polyglot."""
        old_native = self.native_language
        old_target = self.target_language
        old_level = self.proficiency_level
        
        self.native_language = native_language
        self.target_language = target_language
        self.proficiency_level = proficiency_level
        
        try:
            self._validate_language_preferences()
            self.updated_at = datetime.utcnow()
        except ValidationError:
            # Rollback on validation failure
            self.native_language = old_native
            self.target_language = old_target
            self.proficiency_level = old_level
            raise
    
    def update_assessment_data(self, assessed_level: str, assessment_date: Optional[datetime] = None) -> None:
        """Update the user's assessment data."""
        old_level = self.assessed_level
        old_date = self.assessment_date
        
        self.assessed_level = assessed_level
        self.assessment_date = assessment_date or datetime.utcnow()
        
        try:
            self._validate_assessment_fields()
            self.updated_at = datetime.utcnow()
        except ValidationError:
            # Rollback on validation failure
            self.assessed_level = old_level
            self.assessment_date = old_date
            raise
    
    def update_preferences(self, preferred_topics: List[str], learning_goals: List[str]) -> None:
        """Update the user's learning preferences."""
        old_topics = self.preferred_topics.copy() if self.preferred_topics else []
        old_goals = self.learning_goals.copy() if self.learning_goals else []
        
        self.preferred_topics = preferred_topics
        self.learning_goals = learning_goals
        
        try:
            self._validate_preference_fields()
            self.updated_at = datetime.utcnow()
        except ValidationError:
            # Rollback on validation failure
            self.preferred_topics = old_topics
            self.learning_goals = old_goals
            raise
    
    def complete_onboarding(self) -> None:
        """Mark the user's onboarding as completed."""
        self.onboarding_completed = True
        self.updated_at = datetime.utcnow()
    
    def reset_onboarding(self) -> None:
        """Reset the user's onboarding status."""
        self.onboarding_completed = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert user entity to dictionary representation."""
        return {
            'id': str(self.id) if self.id else None,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_active': self.is_active,
            'native_language': self.native_language,
            'target_language': self.target_language,
            'proficiency_level': self.proficiency_level,
            'assessed_level': self.assessed_level,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None,
            'preferred_topics': self.preferred_topics,
            'learning_goals': self.learning_goals,
            'onboarding_completed': self.onboarding_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user entity from dictionary representation."""
        created_at = None
        updated_at = None
        assessment_date = None
        
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('assessment_date'):
            assessment_date = datetime.fromisoformat(data['assessment_date'])
        
        user_id = None
        if data.get('id'):
            user_id = uuid.UUID(data['id']) if isinstance(data['id'], str) else data['id']
        
        return cls(
            id=user_id,
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            is_active=data.get('is_active', True),
            native_language=data.get('native_language', 'TR'),
            target_language=data.get('target_language', 'EN'),
            proficiency_level=data.get('proficiency_level', 'A2'),
            assessed_level=data.get('assessed_level'),
            assessment_date=assessment_date,
            preferred_topics=data.get('preferred_topics', []),
            learning_goals=data.get('learning_goals', []),
            onboarding_completed=data.get('onboarding_completed', False),
            created_at=created_at,
            updated_at=updated_at,
        )
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on username and email."""
        if not isinstance(other, User):
            return False
        return self.username == other.username and self.email == other.email
    
    def __hash__(self) -> int:
        """Hash based on username and email."""
        return hash((self.username, self.email))
    
    def __str__(self) -> str:
        """String representation of the user."""
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the user."""
        return (
            f"User(id={self.id}, username='{self.username}', "
            f"email='{self.email}', created_at={self.created_at})"
        )