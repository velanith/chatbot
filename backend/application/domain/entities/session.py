"""Session domain entity for Polyglot language learning application."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class SessionMode(str, Enum):
    """Session learning modes."""
    TUTOR = "tutor"
    BUDDY = "buddy"


class ProficiencyLevel(str, Enum):
    """Language proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    NATIVE = "native"
    
    # Legacy CEFR values for backward compatibility
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


@dataclass
class Session:
    """Session domain entity."""
    
    id: uuid.UUID
    user_id: uuid.UUID
    mode: SessionMode
    level: ProficiencyLevel
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    summary: Optional[str] = None
    
    # New fields for advanced language learning features
    current_topic: Optional[str] = None
    topic_history: List[str] = field(default_factory=list)
    feedback_count: int = 0
    last_feedback_message: Optional[int] = None
    
    def __post_init__(self):
        """Validate session data after initialization."""
        if not isinstance(self.id, uuid.UUID):
            raise ValueError("Session ID must be a valid UUID")
        if not isinstance(self.user_id, uuid.UUID):
            raise ValueError("User ID must be a valid UUID")
        # Temporarily disable strict type checking for enum
        # if not isinstance(self.mode, SessionMode):
        #     raise ValueError(f"Invalid session mode: {self.mode}")
        if self.mode not in [SessionMode.TUTOR, SessionMode.BUDDY]:
            raise ValueError(f"Invalid session mode: {self.mode}")
        # Temporarily disable strict type checking for enum
        # if not isinstance(self.level, ProficiencyLevel):
        #     raise ValueError(f"Invalid proficiency level: {self.level}")
        # Allow all proficiency levels (both enum instances and string values)
        valid_level_values = [
            'beginner', 'intermediate', 'advanced', 'native',
            'A1', 'A2', 'B1', 'B2', 'C1', 'C2'
        ]
        valid_level_enums = [
            ProficiencyLevel.BEGINNER, ProficiencyLevel.INTERMEDIATE, 
            ProficiencyLevel.ADVANCED, ProficiencyLevel.NATIVE,
            ProficiencyLevel.A1, ProficiencyLevel.A2, ProficiencyLevel.B1,
            ProficiencyLevel.B2, ProficiencyLevel.C1, ProficiencyLevel.C2
        ]
        
        # Check if level is valid (either string value or enum instance)
        level_value = str(self.level)
        if self.level not in valid_level_enums and level_value not in valid_level_values:
            raise ValueError(f"Invalid proficiency level: {self.level}")
        if not isinstance(self.created_at, datetime):
            raise ValueError("Created at must be a datetime object")
        if not isinstance(self.updated_at, datetime):
            raise ValueError("Updated at must be a datetime object")
        if self.summary is not None and not isinstance(self.summary, str):
            raise ValueError("Summary must be a string or None")
        
        # Validate new fields
        self._validate_topic_fields()
        self._validate_feedback_fields()
    
    def deactivate(self) -> None:
        """Deactivate the session."""
        if not self.is_active:
            raise ValueError("Session is already inactive")
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the session."""
        if self.is_active:
            raise ValueError("Session is already active")
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def update_summary(self, summary: str) -> None:
        """Update session summary."""
        if not isinstance(summary, str):
            raise ValueError("Summary must be a string")
        if len(summary.strip()) == 0:
            raise ValueError("Summary cannot be empty")
        if len(summary) > 1000:
            raise ValueError("Summary cannot exceed 1000 characters")
        self.summary = summary.strip()
        self.updated_at = datetime.utcnow()
    
    def _validate_topic_fields(self) -> None:
        """Validate topic-related fields."""
        # Validate current_topic
        if self.current_topic is not None:
            if not isinstance(self.current_topic, str):
                raise ValueError("Current topic must be a string or None")
            if len(self.current_topic.strip()) == 0:
                raise ValueError("Current topic cannot be empty string")
            if len(self.current_topic) > 200:
                raise ValueError("Current topic cannot exceed 200 characters")
            # Normalize the topic
            self.current_topic = self.current_topic.strip()
        
        # Validate topic_history
        if self.topic_history is not None:
            if not isinstance(self.topic_history, list):
                raise ValueError("Topic history must be a list")
            
            for topic in self.topic_history:
                if not isinstance(topic, str):
                    raise ValueError("Each topic in history must be a string")
                if len(topic.strip()) == 0:
                    raise ValueError("Topics in history cannot be empty strings")
                if len(topic) > 200:
                    raise ValueError("Each topic in history cannot exceed 200 characters")
            
            # Clean up topic history
            self.topic_history = [topic.strip() for topic in self.topic_history if topic.strip()]
    
    def _validate_feedback_fields(self) -> None:
        """Validate feedback-related fields."""
        # Validate feedback_count
        if not isinstance(self.feedback_count, int):
            raise ValueError("Feedback count must be an integer")
        if self.feedback_count < 0:
            raise ValueError("Feedback count cannot be negative")
        
        # Validate last_feedback_message
        if self.last_feedback_message is not None:
            if not isinstance(self.last_feedback_message, int):
                raise ValueError("Last feedback message must be an integer or None")
            if self.last_feedback_message < 0:
                raise ValueError("Last feedback message cannot be negative")
    
    def is_tutor_mode(self) -> bool:
        """Check if session is in tutor mode."""
        return self.mode == SessionMode.TUTOR
    
    def is_buddy_mode(self) -> bool:
        """Check if session is in buddy mode."""
        return self.mode == SessionMode.BUDDY
    
    def get_age_in_minutes(self) -> int:
        """Get session age in minutes."""
        return int((datetime.utcnow() - self.created_at).total_seconds() / 60)
    
    def get_age_in_hours(self) -> float:
        """Get session age in hours."""
        return (datetime.utcnow() - self.created_at).total_seconds() / 3600
    
    def should_provide_corrections(self) -> bool:
        """Determine if corrections should be provided based on mode."""
        return self.mode == SessionMode.TUTOR
    
    def set_current_topic(self, topic: str) -> None:
        """Set the current topic for the session."""
        if not isinstance(topic, str):
            raise ValueError("Topic must be a string")
        if len(topic.strip()) == 0:
            raise ValueError("Topic cannot be empty")
        if len(topic) > 200:
            raise ValueError("Topic cannot exceed 200 characters")
        
        # Add current topic to history if it's different
        if self.current_topic and self.current_topic != topic.strip():
            if self.current_topic not in self.topic_history:
                self.topic_history.append(self.current_topic)
        
        self.current_topic = topic.strip()
        self.updated_at = datetime.utcnow()
    
    def clear_current_topic(self) -> None:
        """Clear the current topic."""
        if self.current_topic:
            if self.current_topic not in self.topic_history:
                self.topic_history.append(self.current_topic)
            self.current_topic = None
            self.updated_at = datetime.utcnow()
    
    def increment_feedback_count(self, message_number: int) -> None:
        """Increment feedback count and set last feedback message."""
        if not isinstance(message_number, int):
            raise ValueError("Message number must be an integer")
        if message_number < 0:
            raise ValueError("Message number cannot be negative")
        
        self.feedback_count += 1
        self.last_feedback_message = message_number
        self.updated_at = datetime.utcnow()
    
    def should_provide_feedback(self, current_message_count: int) -> bool:
        """Determine if feedback should be provided based on message count."""
        if not isinstance(current_message_count, int):
            raise ValueError("Current message count must be an integer")
        
        # Provide feedback every 3 messages
        if self.last_feedback_message is None:
            return current_message_count >= 3
        
        return current_message_count - self.last_feedback_message >= 3
    
    def get_topic_history(self) -> List[str]:
        """Get the topic history for this session."""
        return self.topic_history.copy() if self.topic_history else []
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'mode': str(self.mode),
            'level': str(self.level),
            'is_active': self.is_active,
            'summary': self.summary,
            'current_topic': self.current_topic,
            'topic_history': self.topic_history,
            'feedback_count': self.feedback_count,
            'last_feedback_message': self.last_feedback_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }