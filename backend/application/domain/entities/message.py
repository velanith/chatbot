"""Message domain entity for Polyglot language learning application."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"


class CorrectionCategory(str, Enum):
    """Categories of language corrections."""
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    STYLE = "style"


@dataclass
class Correction:
    """Language correction entity."""
    
    original: str
    correction: str
    explanation: str
    category: CorrectionCategory
    
    def __post_init__(self):
        """Validate correction data after initialization."""
        if not isinstance(self.original, str) or not self.original.strip():
            raise ValueError("Original text must be a non-empty string")
        if not isinstance(self.correction, str) or not self.correction.strip():
            raise ValueError("Correction text must be a non-empty string")
        if not isinstance(self.explanation, str) or not self.explanation.strip():
            raise ValueError("Explanation must be a non-empty string")
        if not isinstance(self.category, CorrectionCategory):
            raise ValueError(f"Invalid correction category: {self.category}")
        if len(self.original) > 500:
            raise ValueError("Original text cannot exceed 500 characters")
        if len(self.correction) > 500:
            raise ValueError("Correction text cannot exceed 500 characters")
        if len(self.explanation) > 1000:
            raise ValueError("Explanation cannot exceed 1000 characters")
    
    def to_dict(self) -> dict:
        """Convert correction to dictionary."""
        return {
            'original': self.original,
            'correction': self.correction,
            'explanation': self.explanation,
            'category': str(self.category),
        }


@dataclass
class Message:
    """Message domain entity."""
    
    id: uuid.UUID
    session_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime
    corrections: List[Correction] = None
    micro_exercise: Optional[str] = None
    
    def __post_init__(self):
        """Validate message data after initialization."""
        if self.corrections is None:
            self.corrections = []
        
        if not isinstance(self.id, uuid.UUID):
            raise ValueError("Message ID must be a valid UUID")
        if not isinstance(self.session_id, uuid.UUID):
            raise ValueError("Session ID must be a valid UUID")
        if not isinstance(self.role, MessageRole):
            raise ValueError(f"Invalid message role: {self.role}")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("Message content must be a non-empty string")
        if not isinstance(self.created_at, datetime):
            raise ValueError("Created at must be a datetime object")
        if len(self.content) > 5000:
            raise ValueError("Message content cannot exceed 5000 characters")
        if len(self.corrections) > 3:
            raise ValueError("Maximum 3 corrections allowed per message")
        if self.micro_exercise is not None and (not isinstance(self.micro_exercise, str) or not self.micro_exercise.strip()):
            raise ValueError("Micro exercise must be a non-empty string or None")
    
    def add_correction(self, correction: Correction) -> None:
        """Add a correction to the message."""
        if not isinstance(correction, Correction):
            raise ValueError("Correction must be a Correction instance")
        if len(self.corrections) >= 3:
            raise ValueError("Maximum 3 corrections allowed per message")
        self.corrections.append(correction)
    
    def set_micro_exercise(self, exercise: str) -> None:
        """Set micro exercise for the message."""
        if not isinstance(exercise, str) or not exercise.strip():
            raise ValueError("Micro exercise must be a non-empty string")
        if len(exercise) > 500:
            raise ValueError("Micro exercise cannot exceed 500 characters")
        self.micro_exercise = exercise.strip()
    
    def is_user_message(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER
    
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant."""
        return self.role == MessageRole.ASSISTANT
    
    def has_corrections(self) -> bool:
        """Check if message has corrections."""
        return len(self.corrections) > 0
    
    def has_micro_exercise(self) -> bool:
        """Check if message has a micro exercise."""
        return self.micro_exercise is not None
    
    def get_correction_count(self) -> int:
        """Get number of corrections."""
        return len(self.corrections)
    
    def get_corrections_by_category(self, category: CorrectionCategory) -> List[Correction]:
        """Get corrections filtered by category."""
        return [c for c in self.corrections if c.category == category]
    
    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'role': str(self.role),
            'content': self.content,
            'corrections': [c.to_dict() for c in self.corrections],
            'micro_exercise': self.micro_exercise,
            'created_at': self.created_at.isoformat(),
        }