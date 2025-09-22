"""Topic management router for conversation topic endpoints."""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from src.application.services.topic_manager import (
    TopicManager,
    TopicManagerError,
    TopicSuggestionError,
    TopicCoherenceError,
    TopicTransitionError
)
from src.domain.entities.language_preferences import LanguagePreferences
from src.domain.entities.topic import TopicCategory
from src.domain.entities.session import ProficiencyLevel
from src.domain.entities.user import User
from src.domain.exceptions import (
    TopicError,
    TopicNotFoundError,
    TopicSelectionError,
    TopicSuggestionError as DomainTopicSuggestionError,
    TopicValidationError,
    TopicCoherenceError as DomainTopicCoherenceError,
    TopicTransitionError as DomainTopicTransitionError,
    TopicStarterGenerationError,
    InvalidTopicCategoryError,
    TopicDifficultyMismatchError,
    TopicLimitError,
    ValidationError,
    NotFoundError
)
from src.presentation.schemas.topic_schemas import (
    TopicSuggestionsRequest,
    TopicSuggestionsResponse,
    TopicSelectionRequest,
    TopicSelectionResponse,
    CurrentTopicResponse,
    TopicSchema,
    TopicCategoryEnum,
    ProficiencyLevelEnum
)
from src.presentation.schemas.common_schemas import ErrorResponse
from src.presentation.dependencies import (
    get_current_user_id,
    get_current_user_info,
    get_topic_manager,
    get_user_repository,
    get_session_repository
)
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.repositories.session_repository import SessionRepository


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/suggestions",
    response_model=TopicSuggestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get topic suggestions",
    description="Get AI-powered topic suggestions based on user preferences and level",
    responses={
        200: {"description": "Topic suggestions retrieved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_topic_suggestions(
    session_id: Optional[str] = None,
    exclude_recent: Optional[str] = None,
    limit: int = 5,
    category_filter: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    topic_manager: TopicManager = Depends(get_topic_manager),
    user_repository: UserRepository = Depends(get_user_repository)
) -> TopicSuggestionsResponse:
    """
    Get topic suggestions for the current user.
    
    - **session_id**: Optional session ID for context
    - **exclude_recent**: Comma-separated list of recent topic IDs to exclude
    - **limit**: Maximum number of suggestions (1-20, default: 5)
    - **category_filter**: Comma-separated list of categories to filter by
    
    Returns AI-powered topic suggestions based on user preferences and proficiency level.
    """
    try:
        # Validate user ID format
        try:
            user_uuid = uuid.UUID(current_user_id)
        except ValueError:
            logger.error(f"Invalid user ID format: {current_user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Validate limit parameter
        if limit < 1 or limit > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 20"
            )
        
        # Validate session_id if provided
        if session_id:
            try:
                uuid.UUID(session_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid session ID format"
                )
        
        # Get user information
        user = await user_repository.get_by_id(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Parse and validate exclude_recent parameter
        exclude_recent_list = []
        if exclude_recent:
            topic_ids = [topic_id.strip() for topic_id in exclude_recent.split(',') if topic_id.strip()]
            if len(topic_ids) > 50:  # Limit to prevent abuse
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many topics to exclude (maximum 50)"
                )
            exclude_recent_list = topic_ids
        
        # Parse and validate category filter
        category_filter_list = []
        if category_filter:
            category_names = [cat.strip() for cat in category_filter.split(',') if cat.strip()]
            valid_categories = [cat.value for cat in TopicCategory]
            
            for cat_name in category_names:
                if cat_name not in valid_categories:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid category '{cat_name}'. Valid categories: {', '.join(valid_categories)}"
                    )
                try:
                    category = TopicCategory(cat_name)
                    category_filter_list.append(category)
                except ValueError:
                    logger.warning(f"Invalid category filter: {cat_name}")
        
        # Create user preferences from user data
        user_preferences = LanguagePreferences(
            user_id=user_uuid,
            native_language=user.native_language,
            target_language=user.target_language,
            proficiency_level=ProficiencyLevel(user.proficiency_level) if user.proficiency_level else ProficiencyLevel.A2,
            preferred_topics=category_filter_list if category_filter_list else [],
            learning_goals=[],  # Could be enhanced to get from user profile
            assessment_completed=user.assessed_level is not None
        )
        
        # Get topic suggestions
        suggested_topics = await topic_manager.suggest_topics(
            user_preferences=user_preferences,
            limit=limit,
            exclude_recent=exclude_recent_list
        )
        
        # Convert to API format
        topic_schemas = []
        for topic in suggested_topics:
            topic_schema = TopicSchema(
                id=topic.id,
                name=topic.name,
                description=topic.description,
                category=TopicCategoryEnum(topic.category.value),
                difficulty_level=ProficiencyLevelEnum(topic.difficulty_level.value),
                keywords=topic.keywords,
                conversation_starters=topic.conversation_starters,
                related_topics=topic.related_topics
            )
            topic_schemas.append(topic_schema)
        
        # Get total available topics for user level
        all_suitable_topics = await topic_manager.topic_repository.get_suitable_for_level(
            user_preferences.proficiency_level
        )
        total_available = len(all_suitable_topics)
        
        logger.info(f"Retrieved {len(topic_schemas)} topic suggestions for user {user_uuid}")
        
        return TopicSuggestionsResponse(
            suggestions=topic_schemas,
            total_available=total_available
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except DomainTopicSuggestionError as e:
        logger.error(f"Topic suggestion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except TopicValidationError as e:
        logger.error(f"Topic validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except TopicLimitError as e:
        logger.error(f"Topic limit error: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Topic limit exceeded: {e.message}"
        )
    except TopicError as e:
        logger.error(f"Topic error: {e}")
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
        logger.error(f"Failed to get topic suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topic suggestions"
        )


@router.post(
    "/select",
    response_model=TopicSelectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Select a topic",
    description="Select a topic for conversation and get AI-generated starter",
    responses={
        200: {"description": "Topic selected successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Topic or session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def select_topic(
    request: TopicSelectionRequest,
    current_user_id: str = Depends(get_current_user_id),
    topic_manager: TopicManager = Depends(get_topic_manager),
    user_repository: UserRepository = Depends(get_user_repository),
    session_repository: SessionRepository = Depends(get_session_repository)
) -> TopicSelectionResponse:
    """
    Select a topic for conversation.
    
    - **topic_id**: ID of the topic to select
    - **session_id**: Session ID to associate with the topic
    
    Returns the selected topic details with AI-generated conversation starter.
    """
    try:
        user_uuid = uuid.UUID(current_user_id)
        
        # Verify session belongs to user
        session = await session_repository.get_by_id(request.session_id)
        if not session or session.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Get user information for language preferences
        user = await user_repository.get_by_id(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Select the topic
        selected_topic = await topic_manager.select_topic(
            topic_id=request.topic_id,
            session_id=request.session_id
        )
        
        # Generate conversation starter
        user_level = ProficiencyLevel(user.proficiency_level) if user.proficiency_level else ProficiencyLevel.A2
        conversation_starter = await topic_manager.generate_topic_starter(
            topic=selected_topic,
            user_level=user_level,
            target_language=user.target_language
        )
        
        # Get related topics
        related_topics_entities = await topic_manager.get_related_topics(
            current_topic=selected_topic,
            user_level=user_level,
            limit=3
        )
        
        # Convert to API format
        selected_topic_schema = TopicSchema(
            id=selected_topic.id,
            name=selected_topic.name,
            description=selected_topic.description,
            category=TopicCategoryEnum(selected_topic.category.value),
            difficulty_level=ProficiencyLevelEnum(selected_topic.difficulty_level.value),
            keywords=selected_topic.keywords,
            conversation_starters=selected_topic.conversation_starters,
            related_topics=selected_topic.related_topics
        )
        
        related_topic_schemas = []
        for topic in related_topics_entities:
            topic_schema = TopicSchema(
                id=topic.id,
                name=topic.name,
                description=topic.description,
                category=TopicCategoryEnum(topic.category.value),
                difficulty_level=ProficiencyLevelEnum(topic.difficulty_level.value),
                keywords=topic.keywords,
                conversation_starters=topic.conversation_starters,
                related_topics=topic.related_topics
            )
            related_topic_schemas.append(topic_schema)
        
        # Update session with selected topic (this would need to be implemented in session repository)
        # For now, we'll just log it
        logger.info(f"Selected topic {selected_topic.id} for session {request.session_id}")
        
        return TopicSelectionResponse(
            selected_topic=selected_topic_schema,
            conversation_starter=conversation_starter,
            related_topics=related_topic_schemas
        )
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    except TopicManagerError as e:
        logger.error(f"Topic manager error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Failed to select topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to select topic"
        )


@router.get(
    "/current/{session_id}",
    response_model=CurrentTopicResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current session topic",
    description="Get the current topic for a conversation session",
    responses={
        200: {"description": "Current topic retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_current_topic(
    session_id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id),
    topic_manager: TopicManager = Depends(get_topic_manager),
    user_repository: UserRepository = Depends(get_user_repository),
    session_repository: SessionRepository = Depends(get_session_repository)
) -> CurrentTopicResponse:
    """
    Get current topic for a conversation session.
    
    - **session_id**: ID of the session to get topic for
    
    Returns current topic information and suggested transitions.
    """
    try:
        user_uuid = uuid.UUID(current_user_id)
        
        # Verify session belongs to user
        session = await session_repository.get_by_id(session_id)
        if not session or session.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Get user information
        user = await user_repository.get_by_id(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get current topic from session (this would need to be implemented in session entity)
        # For now, we'll check if there's a current_topic field
        current_topic_entity = None
        current_topic_schema = None
        
        if hasattr(session, 'current_topic') and session.current_topic:
            current_topic_entity = await topic_manager.topic_repository.get_by_id(session.current_topic)
            if current_topic_entity:
                current_topic_schema = TopicSchema(
                    id=current_topic_entity.id,
                    name=current_topic_entity.name,
                    description=current_topic_entity.description,
                    category=TopicCategoryEnum(current_topic_entity.category.value),
                    difficulty_level=ProficiencyLevelEnum(current_topic_entity.difficulty_level.value),
                    keywords=current_topic_entity.keywords,
                    conversation_starters=current_topic_entity.conversation_starters,
                    related_topics=current_topic_entity.related_topics
                )
        
        # Get topic history from session (this would need to be implemented)
        topic_history = []
        if hasattr(session, 'topic_history') and session.topic_history:
            topic_history = session.topic_history
        
        # Get suggested transitions if there's a current topic
        suggested_transitions = []
        if current_topic_entity:
            user_level = ProficiencyLevel(user.proficiency_level) if user.proficiency_level else ProficiencyLevel.A2
            related_topics = await topic_manager.get_related_topics(
                current_topic=current_topic_entity,
                user_level=user_level,
                limit=3
            )
            
            for topic in related_topics:
                topic_schema = TopicSchema(
                    id=topic.id,
                    name=topic.name,
                    description=topic.description,
                    category=TopicCategoryEnum(topic.category.value),
                    difficulty_level=ProficiencyLevelEnum(topic.difficulty_level.value),
                    keywords=topic.keywords,
                    conversation_starters=topic.conversation_starters,
                    related_topics=topic.related_topics
                )
                suggested_transitions.append(topic_schema)
        
        logger.info(f"Retrieved current topic for session {session_id}")
        
        return CurrentTopicResponse(
            current_topic=current_topic_schema,
            session_id=session_id,
            topic_history=topic_history,
            suggested_transitions=suggested_transitions
        )
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except Exception as e:
        logger.error(f"Failed to get current topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current topic"
        )