"""Assessment domain entities for level assessment system."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from ..exceptions import ValidationError


@dataclass
class AssessmentQuestion:
    """Assessment question entity for level assessment."""
    
    id: str
    content: str
    expected_level: str
    category: str
    assessment_focus: Optional[str] = None
    follow_up: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate assessment question after initialization."""
        self._validate_id()
        self._validate_content()
        self._validate_expected_level()
        self._validate_category()
        self._validate_optional_fields()
    
    def _validate_id(self) -> None:
        """Validate question ID."""
        if not self.id:
            raise ValidationError("Question ID cannot be empty")
        
        if not isinstance(self.id, str):
            raise ValidationError("Question ID must be a string")
        
        if len(self.id.strip()) == 0:
            raise ValidationError("Question ID cannot be empty string")
        
        if len(self.id) > 100:
            raise ValidationError("Question ID cannot exceed 100 characters")
        
        self.id = self.id.strip()
    
    def _validate_content(self) -> None:
        """Validate question content."""
        if not isinstance(self.content, str):
            raise ValidationError("Question content must be a string")
        
        if len(self.content.strip()) == 0:
            raise ValidationError("Question content cannot be empty")
        
        if len(self.content) > 1000:
            raise ValidationError("Question content cannot exceed 1000 characters")
        
        self.content = self.content.strip()
    
    def _validate_expected_level(self) -> None:
        """Validate expected proficiency level."""
        valid_levels = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
        
        if not isinstance(self.expected_level, str):
            raise ValidationError("Expected level must be a string")
        
        if self.expected_level not in valid_levels:
            raise ValidationError(f"Invalid expected level: {self.expected_level}")
    
    def _validate_category(self) -> None:
        """Validate question category."""
        if not isinstance(self.category, str):
            raise ValidationError("Category must be a string")
        
        if len(self.category.strip()) == 0:
            raise ValidationError("Category cannot be empty")
        
        if len(self.category) > 100:
            raise ValidationError("Category cannot exceed 100 characters")
        
        self.category = self.category.strip()
    
    def _validate_optional_fields(self) -> None:
        """Validate optional fields."""
        if self.assessment_focus is not None:
            if not isinstance(self.assessment_focus, str):
                raise ValidationError("Assessment focus must be a string or None")
            
            if len(self.assessment_focus) > 500:
                raise ValidationError("Assessment focus cannot exceed 500 characters")
            
            self.assessment_focus = self.assessment_focus.strip() if self.assessment_focus else None
        
        if self.follow_up is not None:
            if not isinstance(self.follow_up, str):
                raise ValidationError("Follow up must be a string or None")
            
            if len(self.follow_up) > 500:
                raise ValidationError("Follow up cannot exceed 500 characters")
            
            self.follow_up = self.follow_up.strip() if self.follow_up else None
    
    def to_dict(self) -> dict:
        """Convert assessment question to dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'expected_level': self.expected_level,
            'category': self.category,
            'assessment_focus': self.assessment_focus,
            'follow_up': self.follow_up
        }


class AssessmentStatus(str, Enum):
    """Assessment session status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class LanguagePair:
    """Language pair for assessment."""
    native_language: str
    target_language: str
    
    def __post_init__(self) -> None:
        """Validate language pair after initialization."""
        self._validate_languages()
    
    def _validate_languages(self) -> None:
        """Validate language codes."""
        # Valid language codes (ISO 639-1)
        valid_languages = {
            'EN', 'ES', 'FR', 'DE', 'IT', 'PT', 'RU', 'ZH', 'JA', 'KO',
            'AR', 'HI', 'TR', 'PL', 'NL', 'SV', 'DA', 'NO', 'FI', 'HE'
        }
        
        if not self.native_language or self.native_language.upper() not in valid_languages:
            raise ValidationError(f"Invalid native language: {self.native_language}")
        
        if not self.target_language or self.target_language.upper() not in valid_languages:
            raise ValidationError(f"Invalid target language: {self.target_language}")
        
        if self.native_language.upper() == self.target_language.upper():
            raise ValidationError("Native and target languages must be different")
        
        # Normalize to uppercase
        self.native_language = self.native_language.upper()
        self.target_language = self.target_language.upper()


@dataclass
class AssessmentResponse:
    """Assessment response entity for storing evaluation data."""
    
    question_id: str
    user_response: str
    ai_evaluation: str
    complexity_score: float
    accuracy_score: float
    fluency_score: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate assessment response after initialization."""
        self._validate_question_id()
        self._validate_user_response()
        self._validate_ai_evaluation()
        self._validate_scores()
        self._validate_created_at()
    
    def _validate_question_id(self) -> None:
        """Validate question ID."""
        if not self.question_id:
            raise ValidationError("Question ID cannot be empty")
        
        if not isinstance(self.question_id, str):
            raise ValidationError("Question ID must be a string")
        
        if len(self.question_id.strip()) == 0:
            raise ValidationError("Question ID cannot be empty string")
        
        if len(self.question_id) > 100:
            raise ValidationError("Question ID cannot exceed 100 characters")
        
        self.question_id = self.question_id.strip()
    
    def _validate_user_response(self) -> None:
        """Validate user response."""
        if not isinstance(self.user_response, str):
            raise ValidationError("User response must be a string")
        
        if len(self.user_response.strip()) == 0:
            raise ValidationError("User response cannot be empty")
        
        if len(self.user_response) > 2000:
            raise ValidationError("User response cannot exceed 2000 characters")
        
        self.user_response = self.user_response.strip()
    
    def _validate_ai_evaluation(self) -> None:
        """Validate AI evaluation."""
        if not isinstance(self.ai_evaluation, str):
            raise ValidationError("AI evaluation must be a string")
        
        if len(self.ai_evaluation.strip()) == 0:
            raise ValidationError("AI evaluation cannot be empty")
        
        if len(self.ai_evaluation) > 5000:
            raise ValidationError("AI evaluation cannot exceed 5000 characters")
        
        self.ai_evaluation = self.ai_evaluation.strip()
    
    def _validate_scores(self) -> None:
        """Validate assessment scores."""
        scores = [
            ("complexity_score", self.complexity_score),
            ("accuracy_score", self.accuracy_score),
            ("fluency_score", self.fluency_score)
        ]
        
        for score_name, score_value in scores:
            if not isinstance(score_value, (int, float)):
                raise ValidationError(f"{score_name} must be a number")
            
            if score_value < 0.0 or score_value > 1.0:
                raise ValidationError(f"{score_name} must be between 0.0 and 1.0")
    
    def _validate_created_at(self) -> None:
        """Validate created_at timestamp."""
        if not isinstance(self.created_at, datetime):
            raise ValidationError("Created at must be a datetime object")
        
        if self.created_at > datetime.utcnow():
            raise ValidationError("Created at cannot be in the future")
    
    def get_overall_score(self) -> float:
        """Calculate overall assessment score."""
        return (self.complexity_score + self.accuracy_score + self.fluency_score) / 3.0
    
    def to_dict(self) -> dict:
        """Convert assessment response to dictionary."""
        return {
            'question_id': self.question_id,
            'user_response': self.user_response,
            'ai_evaluation': self.ai_evaluation,
            'complexity_score': self.complexity_score,
            'accuracy_score': self.accuracy_score,
            'fluency_score': self.fluency_score,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class AssessmentSession:
    """Assessment session entity with validation."""
    
    id: uuid.UUID
    user_id: uuid.UUID
    language_pair: LanguagePair
    current_question: int = 0
    responses: List[AssessmentResponse] = field(default_factory=list)
    estimated_level: Optional[str] = None
    status: AssessmentStatus = AssessmentStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Validate assessment session after initialization."""
        self._validate_ids()
        self._validate_language_pair()
        self._validate_current_question()
        self._validate_responses()
        self._validate_estimated_level()
        self._validate_status()
        self._validate_timestamps()
    
    def _validate_ids(self) -> None:
        """Validate UUID fields."""
        if not isinstance(self.id, uuid.UUID):
            raise ValidationError("Assessment session ID must be a valid UUID")
        
        if not isinstance(self.user_id, uuid.UUID):
            raise ValidationError("User ID must be a valid UUID")
    
    def _validate_language_pair(self) -> None:
        """Validate language pair."""
        if not isinstance(self.language_pair, LanguagePair):
            raise ValidationError("Language pair must be a LanguagePair instance")
    
    def _validate_current_question(self) -> None:
        """Validate current question number."""
        if not isinstance(self.current_question, int):
            raise ValidationError("Current question must be an integer")
        
        if self.current_question < 0:
            raise ValidationError("Current question cannot be negative")
        
        if self.current_question > 50:  # Reasonable upper limit
            raise ValidationError("Current question cannot exceed 50")
    
    def _validate_responses(self) -> None:
        """Validate assessment responses."""
        if not isinstance(self.responses, list):
            raise ValidationError("Responses must be a list")
        
        for i, response in enumerate(self.responses):
            if not isinstance(response, AssessmentResponse):
                raise ValidationError(f"Response {i} must be an AssessmentResponse instance")
    
    def _validate_estimated_level(self) -> None:
        """Validate estimated proficiency level."""
        if self.estimated_level is not None:
            valid_levels = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
            
            if not isinstance(self.estimated_level, str):
                raise ValidationError("Estimated level must be a string")
            
            if self.estimated_level not in valid_levels:
                raise ValidationError(f"Invalid estimated level: {self.estimated_level}")
    
    def _validate_status(self) -> None:
        """Validate assessment status."""
        if not isinstance(self.status, AssessmentStatus):
            raise ValidationError("Status must be an AssessmentStatus enum")
    
    def _validate_timestamps(self) -> None:
        """Validate timestamp fields."""
        if not isinstance(self.created_at, datetime):
            raise ValidationError("Created at must be a datetime object")
        
        if self.created_at > datetime.utcnow():
            raise ValidationError("Created at cannot be in the future")
        
        if self.completed_at is not None:
            if not isinstance(self.completed_at, datetime):
                raise ValidationError("Completed at must be a datetime object or None")
            
            if self.completed_at < self.created_at:
                raise ValidationError("Completed at cannot be before created at")
            
            if self.completed_at > datetime.utcnow():
                raise ValidationError("Completed at cannot be in the future")
    
    def add_response(self, response: AssessmentResponse) -> None:
        """Add a response to the assessment session."""
        if not isinstance(response, AssessmentResponse):
            raise ValidationError("Response must be an AssessmentResponse instance")
        
        if self.status != AssessmentStatus.ACTIVE:
            raise ValidationError("Cannot add response to inactive assessment session")
        
        self.responses.append(response)
        self.current_question += 1
    
    def complete_assessment(self, final_level: str) -> None:
        """Complete the assessment session."""
        if self.status != AssessmentStatus.ACTIVE:
            raise ValidationError("Cannot complete inactive assessment session")
        
        valid_levels = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
        if final_level not in valid_levels:
            raise ValidationError(f"Invalid final level: {final_level}")
        
        self.estimated_level = final_level
        self.status = AssessmentStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def cancel_assessment(self) -> None:
        """Cancel the assessment session."""
        if self.status != AssessmentStatus.ACTIVE:
            raise ValidationError("Cannot cancel inactive assessment session")
        
        self.status = AssessmentStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    def expire_assessment(self) -> None:
        """Mark the assessment session as expired."""
        if self.status != AssessmentStatus.ACTIVE:
            raise ValidationError("Cannot expire inactive assessment session")
        
        self.status = AssessmentStatus.EXPIRED
        self.completed_at = datetime.utcnow()
    
    def update_estimated_level(self, level: str) -> None:
        """Update the estimated proficiency level."""
        valid_levels = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
        if level not in valid_levels:
            raise ValidationError(f"Invalid level: {level}")
        
        self.estimated_level = level
    
    def get_response_count(self) -> int:
        """Get the number of responses in this session."""
        return len(self.responses)
    
    def get_average_scores(self) -> dict:
        """Calculate average scores across all responses."""
        if not self.responses:
            return {
                'complexity': 0.0,
                'accuracy': 0.0,
                'fluency': 0.0,
                'overall': 0.0
            }
        
        total_complexity = sum(r.complexity_score for r in self.responses)
        total_accuracy = sum(r.accuracy_score for r in self.responses)
        total_fluency = sum(r.fluency_score for r in self.responses)
        
        count = len(self.responses)
        avg_complexity = total_complexity / count
        avg_accuracy = total_accuracy / count
        avg_fluency = total_fluency / count
        avg_overall = (avg_complexity + avg_accuracy + avg_fluency) / 3.0
        
        return {
            'complexity': round(avg_complexity, 3),
            'accuracy': round(avg_accuracy, 3),
            'fluency': round(avg_fluency, 3),
            'overall': round(avg_overall, 3)
        }
    
    def is_active(self) -> bool:
        """Check if the assessment session is active."""
        return self.status == AssessmentStatus.ACTIVE
    
    def is_completed(self) -> bool:
        """Check if the assessment session is completed."""
        return self.status == AssessmentStatus.COMPLETED
    
    def get_duration_minutes(self) -> Optional[float]:
        """Get assessment duration in minutes."""
        if self.completed_at is None:
            return None
        
        duration = self.completed_at - self.created_at
        return duration.total_seconds() / 60.0
    
    def to_dict(self) -> dict:
        """Convert assessment session to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'language_pair': {
                'native_language': self.language_pair.native_language,
                'target_language': self.language_pair.target_language
            },
            'current_question': self.current_question,
            'responses': [response.to_dict() for response in self.responses],
            'estimated_level': self.estimated_level,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }