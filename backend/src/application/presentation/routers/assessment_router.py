"""Assessment router for level assessment endpoints."""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from src.application.use_cases.level_assessment_use_case import (
    LevelAssessmentUseCase,
    LevelAssessmentError,
    AssessmentSessionNotFoundError,
    AssessmentAlreadyCompletedError,
    AssessmentExpiredError
)
from src.domain.entities.assessment import LanguagePair
from src.domain.exceptions import (
    AssessmentError,
    AssessmentNotFoundError,
    AssessmentCreationError,
    AssessmentStateError,
    AssessmentResponseError,
    AssessmentEvaluationError,
    AssessmentCompletionError,
    AssessmentValidationError,
    AssessmentTimeoutError,
    AssessmentLimitError,
    InvalidLanguagePairError,
    AssessmentAlreadyCompletedError as DomainAssessmentAlreadyCompletedError,
    ValidationError
)
from src.presentation.schemas.assessment_schemas import (
    AssessmentStartRequest,
    AssessmentStartResponse,
    AssessmentResponseRequest,
    AssessmentResponseResponse,
    AssessmentStatusResponse,
    AssessmentCompleteRequest,
    AssessmentCompleteResponse,
    AssessmentErrorResponse,
    AssessmentQuestion,
    AssessmentEvaluation
)
from src.presentation.schemas.common_schemas import ErrorResponse
from src.presentation.dependencies import get_current_user_id, get_level_assessment_use_case


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/start",
    response_model=AssessmentStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start level assessment",
    description="Start a new AI-powered level assessment session",
    responses={
        201: {"description": "Assessment started successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        409: {"model": ErrorResponse, "description": "Active assessment already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def start_assessment(
    request: AssessmentStartRequest,
    current_user_id: str = Depends(get_current_user_id),
    assessment_use_case: LevelAssessmentUseCase = Depends(get_level_assessment_use_case)
) -> AssessmentStartResponse:
    """
    Start a new level assessment session.
    
    - **language_pair**: Native and target language codes for assessment
    
    Creates a new assessment session and returns the first question.
    Only one active assessment per user is allowed at a time.
    """
    try:
        # Validate user ID format
        try:
            user_id = uuid.UUID(current_user_id)
        except ValueError:
            logger.error(f"Invalid user ID format: {current_user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Validate language pair
        if not request.language_pair.native_language or not request.language_pair.target_language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both native and target languages are required"
            )
        
        if request.language_pair.native_language == request.language_pair.target_language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Native and target languages must be different"
            )
        
        # Validate language codes (basic validation)
        valid_languages = ["EN", "TR", "ES", "FR", "DE", "IT", "PT", "RU", "ZH", "JA", "KO", "AR"]
        if (request.language_pair.native_language.upper() not in valid_languages or 
            request.language_pair.target_language.upper() not in valid_languages):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language pair. Supported languages: {', '.join(valid_languages)}"
            )
        
        # Create language pair entity
        language_pair = LanguagePair(
            native_language=request.language_pair.native_language.upper(),
            target_language=request.language_pair.target_language.upper()
        )
        
        # Start assessment
        session, first_question = await assessment_use_case.start_assessment(
            user_id=user_id,
            language_pair=language_pair
        )
        
        # Convert to response format
        question_response = AssessmentQuestion(
            id=first_question.id,
            content=first_question.content,
            instructions=first_question.instructions,
            category=first_question.category,
            expected_level=first_question.expected_level
        )
        
        logger.info(f"Started assessment session {session.id} for user {user_id}")
        
        return AssessmentStartResponse(
            session_id=session.id,
            question=question_response
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except InvalidLanguagePairError as e:
        logger.error(f"Invalid language pair: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language pair: {e.message}"
        )
    except AssessmentCreationError as e:
        logger.error(f"Assessment creation error: {e}")
        if "already has an active assessment" in e.message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has an active assessment session"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message
            )
    except AssessmentValidationError as e:
        logger.error(f"Assessment validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except AssessmentLimitError as e:
        logger.error(f"Assessment limit error: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Assessment limit exceeded: {e.message}"
        )
    except AssessmentError as e:
        logger.error(f"Assessment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Failed to start assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start assessment"
        )


@router.post(
    "/respond",
    response_model=AssessmentResponseResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit assessment response",
    description="Submit a response to an assessment question and get evaluation",
    responses={
        200: {"description": "Response processed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Assessment session not found"},
        410: {"model": ErrorResponse, "description": "Assessment session expired"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def submit_response(
    request: AssessmentResponseRequest,
    current_user_id: str = Depends(get_current_user_id),
    assessment_use_case: LevelAssessmentUseCase = Depends(get_level_assessment_use_case)
) -> AssessmentResponseResponse:
    """
    Submit a response to an assessment question.
    
    - **session_id**: ID of the assessment session
    - **response**: User's response to the current question
    
    Processes the response using AI evaluation and returns the next question if assessment continues.
    """
    try:
        # Validate session ID format
        if not request.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required"
            )
        
        # Validate response content
        if not request.response or not request.response.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Response content is required"
            )
        
        # Validate response length
        if len(request.response.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Response must be at least 2 characters long"
            )
        
        if len(request.response) > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Response must not exceed 2000 characters"
            )
        
        # Process the response
        evaluation_result, next_question = await assessment_use_case.process_assessment_response(
            session_id=request.session_id,
            user_response=request.response.strip()
        )
        
        # Convert evaluation to response format
        evaluation_response = AssessmentEvaluation(
            complexity_score=evaluation_result.complexity_score,
            accuracy_score=evaluation_result.accuracy_score,
            fluency_score=evaluation_result.fluency_score,
            estimated_level=evaluation_result.estimated_level,
            feedback=evaluation_result.feedback
        )
        
        # Convert next question if exists
        next_question_response = None
        if next_question:
            next_question_response = AssessmentQuestion(
                id=next_question.id,
                content=next_question.content,
                instructions=next_question.instructions,
                category=next_question.category,
                expected_level=next_question.expected_level
            )
        
        is_complete = next_question is None
        
        logger.info(f"Processed response for session {request.session_id}, complete: {is_complete}")
        
        return AssessmentResponseResponse(
            evaluation=evaluation_response,
            next_question=next_question_response,
            is_complete=is_complete
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except AssessmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    except DomainAssessmentAlreadyCompletedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment session is not active"
        )
    except AssessmentTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Assessment session has expired"
        )
    except AssessmentStateError as e:
        logger.error(f"Assessment state error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid assessment state: {e.message}"
        )
    except AssessmentResponseError as e:
        logger.error(f"Assessment response error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Response processing error: {e.message}"
        )
    except AssessmentEvaluationError as e:
        logger.error(f"Assessment evaluation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate response"
        )
    except AssessmentValidationError as e:
        logger.error(f"Assessment validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except AssessmentError as e:
        logger.error(f"Assessment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to process assessment response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process response"
        )


@router.get(
    "/status/{session_id}",
    response_model=AssessmentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get assessment status",
    description="Get current status and progress of an assessment session",
    responses={
        200: {"description": "Assessment status retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Assessment session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_assessment_status(
    session_id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id),
    assessment_use_case: LevelAssessmentUseCase = Depends(get_level_assessment_use_case)
) -> AssessmentStatusResponse:
    """
    Get current status of an assessment session.
    
    - **session_id**: ID of the assessment session
    
    Returns detailed information about the assessment progress and current state.
    """
    try:
        # Get assessment status
        status_info = await assessment_use_case.get_assessment_status(session_id)
        
        logger.info(f"Retrieved status for assessment session {session_id}")
        
        return AssessmentStatusResponse(
            session_id=uuid.UUID(status_info['session_id']),
            assessment_status=status_info['status'],
            current_question=status_info['current_question'],
            total_responses=status_info['total_responses'],
            estimated_level=status_info['estimated_level'],
            progress_percentage=status_info['progress_percentage'],
            average_scores=status_info['average_scores'],
            created_at=status_info['created_at'],
            is_expired=status_info['is_expired'],
            language_pair=status_info['language_pair']
        )
        
    except AssessmentSessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    except LevelAssessmentError as e:
        logger.error(f"Assessment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get assessment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get assessment status"
        )


@router.post(
    "/complete",
    response_model=AssessmentCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete assessment",
    description="Complete an assessment session and get final level",
    responses={
        200: {"description": "Assessment completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request or assessment not active"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Assessment session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def complete_assessment(
    request: AssessmentCompleteRequest,
    current_user_id: str = Depends(get_current_user_id),
    assessment_use_case: LevelAssessmentUseCase = Depends(get_level_assessment_use_case)
) -> AssessmentCompleteResponse:
    """
    Complete an assessment session and get final proficiency level.
    
    - **session_id**: ID of the assessment session to complete
    
    Finalizes the assessment and returns the determined proficiency level.
    """
    try:
        # Complete the assessment
        final_level = await assessment_use_case.complete_assessment(request.session_id)
        
        # Get final status for additional information
        status_info = await assessment_use_case.get_assessment_status(request.session_id)
        
        # Create assessment summary
        assessment_summary = {
            "duration_minutes": 15,  # This would be calculated from actual session data
            "strengths": ["vocabulary", "sentence_structure"],  # This would come from AI analysis
            "improvement_areas": ["grammar", "article_usage"],  # This would come from AI analysis
            "recommended_topics": ["daily_life", "opinions"]  # This would be based on level and performance
        }
        
        logger.info(f"Completed assessment session {request.session_id} with final level: {final_level}")
        
        return AssessmentCompleteResponse(
            session_id=request.session_id,
            final_level=final_level,
            total_responses=status_info['total_responses'],
            final_scores=status_info['average_scores'],
            assessment_summary=assessment_summary
        )
        
    except AssessmentSessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    except AssessmentAlreadyCompletedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment session is not active"
        )
    except LevelAssessmentError as e:
        logger.error(f"Assessment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to complete assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete assessment"
        )