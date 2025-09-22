"""Chat router for conversation endpoints."""

import uuid
import logging
from fastapi import APIRouter, Depends, status, HTTPException

from src.presentation.schemas.chat_schemas import (
    ChatRequest,
    ChatResponse
)
from src.presentation.schemas.common_schemas import (
    ErrorResponse
)
from src.presentation.dependencies import get_current_user_info, get_chat_use_case
from src.application.use_cases.chat_use_case import (
    ChatUseCase,
    ChatRequest as UseCaseChatRequest
)
from src.domain.entities.session import SessionMode, ProficiencyLevel
from src.domain.exceptions import DomainError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
    description="Send a message and receive AI response with corrections and exercises",
    responses={
        200: {"description": "Chat response generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid message content"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user_info),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
) -> ChatResponse:
    """
    Send a chat message and receive AI response.
    
    - **message**: User message content (1-2000 characters)
    - **session_id**: Optional session ID to continue conversation
    - **mode**: Learning mode (tutor/buddy, optional)
    - **level**: Proficiency level (A1/A2/B1, optional)
    
    Returns AI response with corrections and micro-exercises.
    """
    try:
        # Handle session_id (already UUID from schema)
        session_uuid = request.session_id
        
        # Convert mode and level if provided
        mode = SessionMode(request.mode) if request.mode else None
        level = ProficiencyLevel(request.level) if request.level else None
        
        # Create use case request - with better error handling
        try:
            user_id_value = current_user["user_id"]
            
            if isinstance(user_id_value, uuid.UUID):
                user_uuid = user_id_value
            else:
                user_uuid = uuid.UUID(str(user_id_value))
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Invalid user ID in current_user: {current_user}, error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication data"
            )
        use_case_request = UseCaseChatRequest(
            user_id=user_uuid,
            message_content=request.message,
            session_id=session_uuid,
            session_mode=mode,
            proficiency_level=level
        )
        
        # Process chat message
        response = await chat_use_case.handle_chat_message(use_case_request)
        
        # Convert corrections to API format
        api_corrections = []
        for correction in response.corrections:
            api_corrections.append({
                "original": correction.original,
                "correction": correction.correction,
                "explanation": correction.explanation,
                "category": correction.category
            })
        
        # Convert micro exercise to API format if present
        api_micro_exercise = None
        if response.micro_exercise:
            # For now, create a simple exercise format
            # In the future, this could be more sophisticated
            api_micro_exercise = {
                "type": "practice",
                "prompt": response.micro_exercise,
                "options": None,
                "correct_answer": None,
                "explanation": None
            }
        
        # Convert structured feedback to API format if present
        api_structured_feedback = None
        if response.structured_feedback:
            # Convert grammar feedback
            api_grammar_feedback = None
            if response.structured_feedback.grammar_feedback:
                api_grammar_feedback = {
                    "rule_name": response.structured_feedback.grammar_feedback.rule_name,
                    "explanation": response.structured_feedback.grammar_feedback.explanation,
                    "correct_usage": response.structured_feedback.grammar_feedback.correct_usage,
                    "incorrect_usage": response.structured_feedback.grammar_feedback.incorrect_usage,
                    "additional_examples": response.structured_feedback.grammar_feedback.additional_examples,
                    "difficulty_level": response.structured_feedback.grammar_feedback.difficulty_level
                }
            
            # Convert detailed corrections
            api_detailed_corrections = []
            for correction in response.structured_feedback.error_corrections:
                api_detailed_corrections.append({
                    "original": correction.original,
                    "correction": correction.correction,
                    "explanation": correction.explanation,
                    "category": correction.category.value,
                    "examples": correction.examples,
                    "rule_reference": correction.rule_reference
                })
            
            # Convert alternative expressions
            api_alternative_expressions = []
            for alternative in response.structured_feedback.alternative_expressions:
                api_alternative_expressions.append({
                    "original": alternative.original,
                    "alternative": alternative.alternative,
                    "context": alternative.context,
                    "formality_level": alternative.formality_level,
                    "usage_note": alternative.usage_note
                })
            
            api_structured_feedback = {
                "conversation_continuation": response.structured_feedback.conversation_continuation,
                "grammar_feedback": api_grammar_feedback,
                "error_corrections": api_detailed_corrections,
                "alternative_expressions": api_alternative_expressions,
                "native_translation": response.structured_feedback.native_translation,
                "message_count": response.structured_feedback.message_count,
                "overall_assessment": response.structured_feedback.overall_assessment
            }
        
        # Convert current topic to API format if present
        api_current_topic = None
        if response.current_topic:
            api_current_topic = {
                "id": response.current_topic.id,
                "name": response.current_topic.name,
                "description": response.current_topic.description,
                "category": response.current_topic.category.value,
                "difficulty_level": response.current_topic.difficulty_level.value,
                "keywords": response.current_topic.keywords,
                "conversation_starters": response.current_topic.conversation_starters,
                "related_topics": response.current_topic.related_topics
            }
        
        # Create API response
        api_response = ChatResponse(
            response=response.ai_response,
            session_id=str(response.session_id),
            corrections=api_corrections,
            translation=getattr(response, 'translation', None),
            micro_exercise=api_micro_exercise,
            mode=response.session_mode,
            level=response.proficiency_level,
            message_count=response.metadata.get('session_message_count', 1),
            response_time_ms=1000,  # Default value, could be calculated from metadata
            structured_feedback=api_structured_feedback,
            current_topic=api_current_topic,
            topic_transition_suggestion=getattr(response, 'topic_transition_suggestion', None)
        )
        
        logger.info(f"Chat message processed for user {current_user['user_id']}")
        return api_response
        
    except DomainError as e:
        logger.error(f"Domain error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing message"
        )


@router.get(
    "/history",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get chat history",
    description="Get user's chat sessions and conversation history",
    responses={
        200: {"description": "Chat history retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def get_chat_history(
    current_user: dict = Depends(get_current_user_info),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
) -> dict:
    """
    Get user's chat history including all sessions and recent messages.
    
    Returns list of chat sessions with metadata and recent messages.
    """
    try:
        user_uuid = uuid.UUID(current_user["user_id"])
        
        # Get user's sessions from session repository
        sessions = await chat_use_case.session_repository.get_by_user_id(user_uuid)
        
        chat_history = []
        for session in sessions:
            # Load session context first
            await chat_use_case.memory_manager.load_session_context(session.id)
            
            # Get recent messages for each session
            recent_messages = await chat_use_case.memory_manager.get_recent_messages(
                session.id, count=5
            )
            
            # Get message count
            message_count = await chat_use_case.message_repository.count_by_session(session.id)
            
            # Create session summary
            last_message = ""
            if recent_messages:
                # Get the last user message for preview
                user_messages = [msg for msg in recent_messages if msg.role.value == 'user']
                if user_messages:
                    last_message = user_messages[-1].content[:50] + "..." if len(user_messages[-1].content) > 50 else user_messages[-1].content
                else:
                    last_message = "New conversation"
            else:
                last_message = "New conversation"
            
            # Create title from first user message or default
            title = "New Conversation"
            if recent_messages:
                first_user_msg = next((msg for msg in reversed(recent_messages) if msg.role.value == 'user'), None)
                if first_user_msg:
                    title = first_user_msg.content[:30] + "..." if len(first_user_msg.content) > 30 else first_user_msg.content
            
            chat_history.append({
                "id": str(session.id),
                "title": title,
                "lastMessage": last_message,
                "createdAt": session.created_at.isoformat(),
                "updatedAt": session.updated_at.isoformat(),
                "messageCount": message_count,
                "mode": session.mode.value,
                "level": session.level.value,
                "messages": [
                    {
                        "type": "user" if msg.role.value == "user" else "ai",
                        "content": msg.content
                    }
                    for msg in recent_messages
                ]
            })
        
        # Sort by updated_at descending (most recent first)
        chat_history.sort(key=lambda x: x["updatedAt"], reverse=True)
        
        return {
            "status": "success",
            "data": {
                "sessions": chat_history,
                "total": len(chat_history)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )


@router.get(
    "/session/{session_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get session details",
    description="Get detailed information about a specific chat session",
    responses={
        200: {"description": "Session details retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Session not found"}
    }
)
async def get_session_details(
    session_id: str,
    current_user: dict = Depends(get_current_user_info),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
) -> dict:
    """
    Get detailed information about a specific chat session.
    
    Returns session metadata and all messages in the conversation.
    """
    try:
        user_uuid = uuid.UUID(current_user["user_id"])
        session_uuid = uuid.UUID(session_id)
        
        # Get session info (includes authorization check)
        session_info = await chat_use_case.get_session_info(session_uuid, user_uuid)
        
        # Load session context first
        await chat_use_case.memory_manager.load_session_context(session_uuid)
        
        # Get all messages for this session
        all_messages = await chat_use_case.memory_manager.get_recent_messages(
            session_uuid, count=1000  # Get all messages
        )
        
        messages = [
            {
                "type": "user" if msg.role.value == "user" else "ai",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if hasattr(msg, 'created_at') else None
            }
            for msg in all_messages
        ]
        
        return {
            "status": "success",
            "data": {
                "session": session_info,
                "messages": messages
            }
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except Exception as e:
        logger.error(f"Error getting session details: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session details"
        )