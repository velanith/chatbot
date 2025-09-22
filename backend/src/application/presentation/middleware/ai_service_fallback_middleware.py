"""Middleware for handling AI service failures with graceful fallbacks."""

import logging
import asyncio
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    ServiceError,
    OpenAIServiceError,
    ExternalServiceError,
    TimeoutError,
    ServiceUnavailableError,
    AssessmentEvaluationError,
    FeedbackGenerationError,
    TopicSuggestionError,
    TranslationFeedbackError,
    AssessmentQuestionGenerationError,
    TopicStarterGenerationError
)


logger = logging.getLogger(__name__)


class AIServiceFallbackMiddleware:
    """Middleware that provides graceful fallbacks for AI service failures."""
    
    def __init__(self, app):
        self.app = app
        self.fallback_responses = self._initialize_fallback_responses()
        self.retry_config = {
            "max_retries": 2,
            "retry_delay": 1.0,
            "backoff_multiplier": 2.0
        }
    
    def _initialize_fallback_responses(self) -> Dict[str, Dict[str, Any]]:
        """Initialize fallback responses for different AI service failures."""
        return {
            "assessment_evaluation": {
                "complexity_score": 0.5,
                "accuracy_score": 0.5,
                "fluency_score": 0.5,
                "estimated_level": "A2",
                "feedback": "Unable to provide detailed evaluation at this time. Please continue with the assessment."
            },
            "assessment_question": {
                "id": "fallback_question",
                "content": "Please describe your daily routine in the target language.",
                "instructions": "Write 2-3 sentences about what you do in a typical day.",
                "category": "general",
                "expected_level": "A2"
            },
            "topic_suggestions": [
                {
                    "id": "daily_life",
                    "name": "Daily Life",
                    "description": "Talk about everyday activities and routines",
                    "category": "lifestyle",
                    "difficulty_level": "A2",
                    "keywords": ["daily", "routine", "activities"],
                    "conversation_starters": ["Tell me about your typical day"],
                    "related_topics": ["hobbies", "work"]
                },
                {
                    "id": "hobbies",
                    "name": "Hobbies and Interests",
                    "description": "Discuss your hobbies and interests",
                    "category": "personal",
                    "difficulty_level": "A2",
                    "keywords": ["hobbies", "interests", "free time"],
                    "conversation_starters": ["What do you like to do in your free time?"],
                    "related_topics": ["daily_life", "sports"]
                }
            ],
            "topic_starter": "Let's talk about this topic. What would you like to share?",
            "structured_feedback": {
                "conversation_continuation": "Please continue the conversation.",
                "grammar_feedback": {
                    "overall_score": 0.7,
                    "main_issues": ["Basic grammar review recommended"],
                    "suggestions": ["Keep practicing!"]
                },
                "error_corrections": [],
                "alternative_expressions": [],
                "native_translation": None,
                "message_count": 3
            },
            "translation": "Translation service temporarily unavailable."
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with AI service fallback handling."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            return await self._handle_ai_service_error(request, e)
    
    async def _handle_ai_service_error(self, request: Request, error: Exception) -> Response:
        """Handle AI service errors with appropriate fallbacks."""
        
        # Log the error
        logger.error(f"AI service error on {request.url.path}: {error}")
        
        # Determine if this is an AI service error that needs fallback
        if not self._is_ai_service_error(error):
            # Re-raise non-AI service errors
            if isinstance(error, HTTPException):
                return JSONResponse(
                    status_code=error.status_code,
                    content={"detail": error.detail}
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Internal server error"}
                )
        
        # Try to provide a fallback response
        fallback_response = await self._get_fallback_response(request, error)
        
        if fallback_response:
            # Add warning header to indicate fallback was used
            headers = {"X-Fallback-Used": "true", "X-Fallback-Reason": str(error)}
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=fallback_response,
                headers=headers
            )
        else:
            # No fallback available, return appropriate error
            return await self._create_error_response(error)
    
    def _is_ai_service_error(self, error: Exception) -> bool:
        """Check if the error is related to AI services."""
        ai_service_errors = (
            OpenAIServiceError,
            ExternalServiceError,
            TimeoutError,
            ServiceUnavailableError,
            AssessmentEvaluationError,
            FeedbackGenerationError,
            TopicSuggestionError,
            TranslationFeedbackError,
            AssessmentQuestionGenerationError,
            TopicStarterGenerationError
        )
        
        return isinstance(error, ai_service_errors)
    
    async def _get_fallback_response(self, request: Request, error: Exception) -> Optional[Dict[str, Any]]:
        """Get appropriate fallback response based on the request and error type."""
        
        path = request.url.path
        method = request.method
        
        # Assessment endpoints
        if "/assessment/" in path:
            if "start" in path and method == "POST":
                return {
                    "session_id": "fallback_session",
                    "question": self.fallback_responses["assessment_question"]
                }
            elif "respond" in path and method == "POST":
                return {
                    "evaluation": self.fallback_responses["assessment_evaluation"],
                    "next_question": self.fallback_responses["assessment_question"],
                    "is_complete": False
                }
            elif "complete" in path and method == "POST":
                return {
                    "session_id": "fallback_session",
                    "final_level": "A2",
                    "total_responses": 5,
                    "final_scores": self.fallback_responses["assessment_evaluation"],
                    "assessment_summary": {
                        "duration_minutes": 15,
                        "strengths": ["Participation"],
                        "improvement_areas": ["Continue practicing"],
                        "recommended_topics": ["daily_life"]
                    }
                }
        
        # Topic endpoints
        elif "/topics/" in path:
            if "suggestions" in path and method == "GET":
                return {
                    "suggestions": self.fallback_responses["topic_suggestions"],
                    "total_available": 10
                }
            elif "select" in path and method == "POST":
                return {
                    "selected_topic": self.fallback_responses["topic_suggestions"][0],
                    "conversation_starter": self.fallback_responses["topic_starter"],
                    "related_topics": self.fallback_responses["topic_suggestions"][1:]
                }
        
        # Chat endpoints
        elif "/chat/" in path and method == "POST":
            return {
                "response": "I'm having trouble processing your message right now. Please try again.",
                "corrections": [],
                "exercises": [],
                "structured_feedback": self.fallback_responses["structured_feedback"],
                "translation": None
            }
        
        # User flow endpoints
        elif "/user/flow-state" in path and method == "GET":
            return {
                "message": "User flow state retrieved successfully",
                "data": {
                    "user_id": "fallback_user",
                    "current_state": "chat_ready",
                    "has_language_preferences": True,
                    "has_level_assessment": False,
                    "has_topic_preferences": False,
                    "onboarding_completed": True,
                    "next_action": "start_chat",
                    "metadata": {}
                }
            }
        
        return None
    
    async def _create_error_response(self, error: Exception) -> JSONResponse:
        """Create appropriate error response when no fallback is available."""
        
        if isinstance(error, OpenAIServiceError):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "AI service temporarily unavailable. Please try again later.",
                    "error_code": "AI_SERVICE_UNAVAILABLE",
                    "retry_after": 60
                }
            )
        elif isinstance(error, TimeoutError):
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "detail": "AI service request timed out. Please try again.",
                    "error_code": "AI_SERVICE_TIMEOUT"
                }
            )
        elif isinstance(error, ServiceUnavailableError):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "AI service is currently unavailable. Please try again later.",
                    "error_code": "AI_SERVICE_UNAVAILABLE",
                    "retry_after": getattr(error, 'retry_after', 300)
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "AI service error occurred. Please try again.",
                    "error_code": "AI_SERVICE_ERROR"
                }
            )
    
    async def _retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Retry function with exponential backoff."""
        
        last_exception = None
        delay = self.retry_config["retry_delay"]
        
        for attempt in range(self.retry_config["max_retries"] + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.retry_config["max_retries"]:
                    logger.warning(f"AI service call failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    delay *= self.retry_config["backoff_multiplier"]
                else:
                    logger.error(f"AI service call failed after {attempt + 1} attempts: {e}")
        
        raise last_exception


def create_ai_service_fallback_middleware():
    """Factory function to create AI service fallback middleware."""
    return AIServiceFallbackMiddleware