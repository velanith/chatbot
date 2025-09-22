"""Assessment API schemas for request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import uuid
from enum import Enum

from .common_schemas import BaseResponse, ResponseStatus, TimestampMixin


class AssessmentStatus(str, Enum):
    """Assessment session status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class LanguagePairRequest(BaseModel):
    """Language pair request schema."""
    native_language: str = Field(..., min_length=2, max_length=5, description="Native language code (ISO 639-1)")
    target_language: str = Field(..., min_length=2, max_length=5, description="Target language code (ISO 639-1)")
    
    @field_validator('native_language', 'target_language')
    @classmethod
    def validate_language_codes(cls, v):
        """Validate language codes."""
        # Common language codes - in production this should be more comprehensive
        valid_languages = {
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 
            'ar', 'hi', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi', 'he'
        }
        if v.lower() not in valid_languages:
            raise ValueError(f'Invalid language code: {v}')
        return v.lower()
    
    @model_validator(mode='after')
    def different_languages(self):
        """Validate that target language is different from native language."""
        if self.native_language and self.target_language and self.native_language.lower() == self.target_language.lower():
            raise ValueError('Target language must be different from native language')
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "native_language": "tr",
                "target_language": "en"
            }
        }


class AssessmentStartRequest(BaseModel):
    """Request schema for starting an assessment."""
    language_pair: LanguagePairRequest = Field(..., description="Language pair for assessment")
    
    class Config:
        schema_extra = {
            "example": {
                "language_pair": {
                    "native_language": "tr",
                    "target_language": "en"
                }
            }
        }


class AssessmentQuestion(BaseModel):
    """Assessment question schema."""
    id: str = Field(..., description="Question ID")
    content: str = Field(..., description="Question content")
    instructions: Optional[str] = Field(None, description="Additional instructions")
    category: str = Field(..., description="Question category")
    expected_level: str = Field(..., description="Expected proficiency level")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "A2_introduction_0",
                "content": "Please introduce yourself. Tell me your name and where you are from.",
                "instructions": "Please answer in English. Take your time and answer as completely as you can.",
                "category": "introduction",
                "expected_level": "A2"
            }
        }


class AssessmentStartResponse(BaseResponse):
    """Response schema for starting an assessment."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Assessment started successfully")
    session_id: uuid.UUID = Field(..., description="Assessment session ID")
    question: AssessmentQuestion = Field(..., description="First assessment question")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Assessment started successfully",
                "timestamp": "2024-01-01T12:00:00Z",
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "question": {
                    "id": "A2_introduction_0",
                    "content": "Please introduce yourself. Tell me your name and where you are from.",
                    "instructions": "Please answer in English. Take your time and answer as completely as you can.",
                    "category": "introduction",
                    "expected_level": "A2"
                }
            }
        }


class AssessmentResponseRequest(BaseModel):
    """Request schema for submitting an assessment response."""
    session_id: uuid.UUID = Field(..., description="Assessment session ID")
    response: str = Field(..., min_length=1, max_length=2000, description="User's response to the question")
    
    @field_validator('response')
    @classmethod
    def validate_response(cls, v):
        """Validate response is not empty."""
        if not v or not v.strip():
            raise ValueError('Response cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "response": "Hello! My name is John and I am from Turkey. I live in Istanbul and I work as a software engineer."
            }
        }


class AssessmentEvaluation(BaseModel):
    """Assessment evaluation result schema."""
    complexity_score: float = Field(..., ge=0.0, le=1.0, description="Complexity score (0.0-1.0)")
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Accuracy score (0.0-1.0)")
    fluency_score: float = Field(..., ge=0.0, le=1.0, description="Fluency score (0.0-1.0)")
    estimated_level: str = Field(..., description="Estimated proficiency level")
    feedback: Optional[str] = Field(None, description="Evaluation feedback")
    
    class Config:
        schema_extra = {
            "example": {
                "complexity_score": 0.65,
                "accuracy_score": 0.78,
                "fluency_score": 0.72,
                "estimated_level": "B1",
                "feedback": "Good use of present tense and vocabulary. Some minor grammar issues with articles."
            }
        }


class AssessmentResponseResponse(BaseResponse):
    """Response schema for assessment response submission."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Response processed successfully")
    evaluation: AssessmentEvaluation = Field(..., description="Response evaluation")
    next_question: Optional[AssessmentQuestion] = Field(None, description="Next question (if assessment continues)")
    is_complete: bool = Field(..., description="Whether assessment is complete")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Response processed successfully",
                "timestamp": "2024-01-01T12:05:00Z",
                "evaluation": {
                    "complexity_score": 0.65,
                    "accuracy_score": 0.78,
                    "fluency_score": 0.72,
                    "estimated_level": "B1",
                    "feedback": "Good use of present tense and vocabulary."
                },
                "next_question": {
                    "id": "B1_opinions_1",
                    "content": "What do you think about social media? Is it good or bad?",
                    "instructions": "Please answer in English. Express your opinion with reasons.",
                    "category": "opinions",
                    "expected_level": "B1"
                },
                "is_complete": False
            }
        }


class AssessmentStatusResponse(BaseResponse):
    """Response schema for assessment status."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Assessment status retrieved successfully")
    session_id: uuid.UUID = Field(..., description="Assessment session ID")
    assessment_status: AssessmentStatus = Field(..., description="Current assessment status")
    current_question: int = Field(..., description="Current question number")
    total_responses: int = Field(..., description="Total responses submitted")
    estimated_level: Optional[str] = Field(None, description="Current estimated level")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Assessment progress percentage")
    average_scores: Dict[str, float] = Field(..., description="Average scores across all responses")
    created_at: datetime = Field(..., description="Assessment creation timestamp")
    is_expired: bool = Field(..., description="Whether assessment has expired")
    language_pair: Dict[str, str] = Field(..., description="Language pair information")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Assessment status retrieved successfully",
                "timestamp": "2024-01-01T12:10:00Z",
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "assessment_status": "active",
                "current_question": 3,
                "total_responses": 2,
                "estimated_level": "B1",
                "progress_percentage": 40.0,
                "average_scores": {
                    "complexity": 0.65,
                    "accuracy": 0.78,
                    "fluency": 0.72
                },
                "created_at": "2024-01-01T12:00:00Z",
                "is_expired": False,
                "language_pair": {
                    "native_language": "tr",
                    "target_language": "en"
                }
            }
        }


class AssessmentCompleteRequest(BaseModel):
    """Request schema for completing an assessment."""
    session_id: uuid.UUID = Field(..., description="Assessment session ID")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class AssessmentCompleteResponse(BaseResponse):
    """Response schema for assessment completion."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Assessment completed successfully")
    session_id: uuid.UUID = Field(..., description="Assessment session ID")
    final_level: str = Field(..., description="Final assessed proficiency level")
    total_responses: int = Field(..., description="Total responses in assessment")
    final_scores: Dict[str, float] = Field(..., description="Final average scores")
    assessment_summary: Dict[str, Any] = Field(..., description="Assessment summary information")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Assessment completed successfully",
                "timestamp": "2024-01-01T12:15:00Z",
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "final_level": "B1",
                "total_responses": 5,
                "final_scores": {
                    "complexity": 0.68,
                    "accuracy": 0.75,
                    "fluency": 0.71
                },
                "assessment_summary": {
                    "duration_minutes": 15,
                    "strengths": ["vocabulary", "sentence_structure"],
                    "improvement_areas": ["grammar", "article_usage"],
                    "recommended_topics": ["daily_life", "opinions"]
                }
            }
        }


class AssessmentErrorResponse(BaseResponse):
    """Error response schema for assessment endpoints."""
    status: ResponseStatus = ResponseStatus.ERROR
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Specific error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "message": "Assessment session not found",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "ASSESSMENT_NOT_FOUND",
                "details": {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }