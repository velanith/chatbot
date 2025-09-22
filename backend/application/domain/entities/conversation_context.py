"""Conversation context value objects for Polyglot language learning application."""

from dataclasses import dataclass
from typing import List, Optional

from .message import Message
from .session import SessionMode, ProficiencyLevel


@dataclass
class UserPreferences:
    """User preferences for personalized language learning in Polyglot."""
    
    native_language: str
    target_language: str
    proficiency_level: ProficiencyLevel
    
    def __post_init__(self):
        """Validate user preferences after initialization."""
        if not isinstance(self.native_language, str) or len(self.native_language.strip()) < 2:
            raise ValueError("Native language must be at least 2 characters")
        if not isinstance(self.target_language, str) or len(self.target_language.strip()) < 2:
            raise ValueError("Target language must be at least 2 characters")
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
        level_value = str(self.proficiency_level)
        if self.proficiency_level not in valid_level_enums and level_value not in valid_level_values:
            raise ValueError(f"Invalid proficiency level: {self.proficiency_level}")
        if self.native_language.strip().upper() == self.target_language.strip().upper():
            raise ValueError("Native and target languages cannot be the same")
        
        # Normalize language codes
        self.native_language = self.native_language.strip().upper()
        self.target_language = self.target_language.strip().upper()
    
    def is_beginner(self) -> bool:
        """Check if user is at beginner level."""
        return self.proficiency_level == ProficiencyLevel.A1
    
    def is_intermediate(self) -> bool:
        """Check if user is at intermediate level."""
        return self.proficiency_level in [ProficiencyLevel.A2, ProficiencyLevel.B1]
    
    def should_use_simple_vocabulary(self) -> bool:
        """Determine if simple vocabulary should be used."""
        return self.proficiency_level in [ProficiencyLevel.A1, ProficiencyLevel.A2]
    
    def to_dict(self) -> dict:
        """Convert preferences to dictionary."""
        return {
            'native_language': self.native_language,
            'target_language': self.target_language,
            'proficiency_level': str(self.proficiency_level),
        }


@dataclass
class ConversationContext:
    """Complete conversation context for Polyglot language learning sessions."""
    
    recent_messages: List[Message]
    summary: Optional[str]
    user_preferences: UserPreferences
    session_mode: SessionMode
    
    def __post_init__(self):
        """Validate conversation context after initialization."""
        # Temporarily disable strict type checking for enum
        if self.session_mode not in [SessionMode.TUTOR, SessionMode.BUDDY]:
            raise ValueError(f"Invalid session mode: {self.session_mode}")
        if not isinstance(self.user_preferences, UserPreferences):
            raise ValueError("User preferences must be a UserPreferences instance")
        if self.recent_messages is None:
            self.recent_messages = []
        if not isinstance(self.recent_messages, list):
            raise ValueError("Recent messages must be a list")
        if self.summary is not None and not isinstance(self.summary, str):
            raise ValueError("Summary must be a string or None")
        
        # Validate all messages in the list
        for msg in self.recent_messages:
            if not isinstance(msg, Message):
                raise ValueError("All recent messages must be Message instances")
    
    def get_message_count(self) -> int:
        """Get total number of recent messages."""
        return len(self.recent_messages)
    
    def get_user_messages(self) -> List[Message]:
        """Get only user messages from recent messages."""
        from .message import MessageRole
        return [msg for msg in self.recent_messages if msg.role == MessageRole.USER]
    
    def get_assistant_messages(self) -> List[Message]:
        """Get only assistant messages from recent messages."""
        from .message import MessageRole
        return [msg for msg in self.recent_messages if msg.role == MessageRole.ASSISTANT]
    
    def get_last_message(self) -> Optional[Message]:
        """Get the most recent message."""
        return self.recent_messages[-1] if self.recent_messages else None
    
    def get_last_user_message(self) -> Optional[Message]:
        """Get the most recent user message."""
        user_messages = self.get_user_messages()
        return user_messages[-1] if user_messages else None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """Get the most recent assistant message."""
        assistant_messages = self.get_assistant_messages()
        return assistant_messages[-1] if assistant_messages else None
    
    def add_message(self, message: Message) -> None:
        """Add a message to the context."""
        if not isinstance(message, Message):
            raise ValueError("Message must be a Message instance")
        self.recent_messages.append(message)
    
    def has_conversation_history(self) -> bool:
        """Check if there's any conversation history."""
        return len(self.recent_messages) > 0
    
    def should_provide_corrections(self) -> bool:
        """Determine if corrections should be provided based on mode."""
        return self.session_mode == SessionMode.TUTOR
    
    def get_conversation_length(self) -> int:
        """Get the total number of exchanges (user + assistant pairs)."""
        return min(len(self.get_user_messages()), len(self.get_assistant_messages()))
    
    def to_dict(self) -> dict:
        """Convert context to dictionary."""
        return {
            'recent_messages': [msg.to_dict() for msg in self.recent_messages],
            'summary': self.summary,
            'user_preferences': self.user_preferences.to_dict(),
            'session_mode': str(self.session_mode),
            'message_count': self.get_message_count(),
        }