"""Session router for session management endpoints."""

import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException, Query

from src.presentation.schemas.session_schemas import (
    SessionRequest,
    SessionResponse,
    SessionHistoryResponse,
    SessionListResponse,
    ConversationExportResponse
)
from src.presentation.schemas.common_schemas import (
    ErrorResponse
)
from src.presentation.dependencies import get_current_user_info, get_session_use_case
from src.presentation.dependencies import get_current_user_id
from src.application.use_cases.session_use_case import (
    SessionUseCase,
    SessionRequest as UseCaseSessionRequest
)
from src.domain.entities.session import SessionMode, ProficiencyLevel
from src.domain.exceptions import DomainError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new session",
    description="Create a new conversation session",
    responses={
        201: {"description": "Session created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid session parameters"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def create_session(
    request: SessionRequest,
    current_user: dict = Depends(get_current_user_info),
    session_use_case: SessionUseCase = Depends(get_session_use_case)
) -> SessionResponse:
    """
    Create a new conversation session.
    
    - **mode**: Learning mode (tutor/buddy, optional, defaults to buddy)
    - **level**: Proficiency level (A1/A2/B1, optional, defaults to A2)
    
    Returns session ID and configuration.
    """
    try:
        # Convert mode and level
        mode = SessionMode(request.mode) if request.mode else SessionMode.BUDDY
        level = ProficiencyLevel(request.level) if request.level else ProficiencyLevel.A2
        
        # Create use case request
        user_uuid = uuid.UUID(current_user["user_id"])
        use_case_request = UseCaseSessionRequest(
            user_id=user_uuid,
            mode=mode,
            level=level
        )
        
        # Create session
        response = await session_use_case.create_session(use_case_request)
        
        # Create API response
        api_response = SessionResponse(
            message="Session created successfully",
            session_id=str(response.session_id),
            mode=response.mode.value,
            level=response.level.value
        )
        
        logger.info(f"Session created for user {current_user['user_id']}: {response.session_id}")
        return api_response
        
    except DomainError as e:
        logger.error(f"Domain error in session creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in session creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating session"
        )

@router.get(
    "/history/{session_id}",
    response_model=SessionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get session history",
    description="Get conversation history for a specific session with pagination",
    responses={
        200: {"description": "Session history retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Access denied to this session"}
    }
)
async def get_session_history(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of messages per page"),
    session_use_case: SessionUseCase = Depends(get_session_use_case)
) -> SessionHistoryResponse:
    """
    Get conversation history for a specific session.
    
    - **session_id**: Session UUID
    - **page**: Page number (default: 1)
    - **page_size**: Messages per page (default: 20, max: 100)
    
    Returns paginated conversation history with messages and metadata.
    """
    try:
        # Convert session_id to UUID
        session_uuid = uuid.UUID(session_id)
        user_uuid = uuid.UUID(current_user_id)
        
        # Get session history
        history = await session_use_case.get_session_history(
            session_id=session_uuid,
            user_id=user_uuid,
            page=page,
            page_size=page_size
        )
        
        logger.info(f"Retrieved history for session {session_id}, page {page}")
        return history
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except DomainError as e:
        logger.error(f"Domain error in history retrieval: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        elif "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Unexpected error in history retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving history"
        )


@router.get(
    "/",
    response_model=SessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List user sessions",
    description="Get list of user's sessions with filtering and pagination",
    responses={
        200: {"description": "Sessions retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def list_user_sessions(
    current_user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=50, description="Number of sessions per page"),
    mode: Optional[str] = Query(None, description="Filter by session mode (tutor/buddy)"),
    level: Optional[str] = Query(None, description="Filter by proficiency level (A1/A2/B1/B2/C1/C2)"),
    active_only: bool = Query(False, description="Show only active sessions"),
    session_use_case: SessionUseCase = Depends(get_session_use_case)
) -> SessionListResponse:
    """
    Get list of user's sessions with filtering options.
    
    - **page**: Page number (default: 1)
    - **page_size**: Sessions per page (default: 10, max: 50)
    - **mode**: Filter by session mode (optional)
    - **level**: Filter by proficiency level (optional)
    - **active_only**: Show only active sessions (default: false)
    
    Returns paginated list of sessions with metadata.
    """
    try:
        user_uuid = uuid.UUID(current_user_id)
        
        # Convert filter parameters
        mode_filter = SessionMode(mode) if mode else None
        level_filter = ProficiencyLevel(level) if level else None
        
        # Get user sessions
        sessions = await session_use_case.list_user_sessions_paginated(
            user_id=user_uuid,
            page=page,
            page_size=page_size,
            mode_filter=mode_filter,
            level_filter=level_filter,
            active_only=active_only
        )
        
        logger.info(f"Retrieved {len(sessions.sessions)} sessions for user {current_user_id}")
        return sessions
        
    except ValueError as e:
        logger.error(f"Invalid parameter format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parameter format"
        )
    except Exception as e:
        logger.error(f"Unexpected error in session listing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving sessions"
        )


@router.post(
    "/{session_id}/end",
    status_code=status.HTTP_200_OK,
    summary="End session",
    description="End/terminate a conversation session",
    responses={
        200: {"description": "Session ended successfully"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Access denied to this session"}
    }
)
async def end_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session_use_case: SessionUseCase = Depends(get_session_use_case)
) -> dict:
    """
    End/terminate a conversation session.
    
    - **session_id**: Session UUID to terminate
    
    Marks the session as ended and performs cleanup.
    """
    try:
        # Convert session_id to UUID
        session_uuid = uuid.UUID(session_id)
        user_uuid = uuid.UUID(current_user_id)
        
        # End session
        await session_use_case.end_session(
            session_id=session_uuid,
            user_id=user_uuid
        )
        
        logger.info(f"Session {session_id} ended by user {current_user_id}")
        return {
            "message": "Session ended successfully",
            "session_id": session_id
        }
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except DomainError as e:
        logger.error(f"Domain error in session termination: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        elif "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Unexpected error in session termination: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while ending session"
        )


@router.get(
    "/{session_id}/export",
    response_model=ConversationExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export conversation",
    description="Export conversation data for a session",
    responses={
        200: {"description": "Conversation exported successfully"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Access denied to this session"}
    }
)
async def export_conversation(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    format: str = Query("json", description="Export format (json/csv/txt)"),
    session_use_case: SessionUseCase = Depends(get_session_use_case)
) -> ConversationExportResponse:
    """
    Export conversation data for a session.
    
    - **session_id**: Session UUID to export
    - **format**: Export format (json, csv, txt)
    
    Returns conversation data in the requested format.
    """
    try:
        # Validate format
        if format not in ["json", "csv", "txt"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export format. Supported formats: json, csv, txt"
            )
        
        # Convert session_id to UUID
        session_uuid = uuid.UUID(session_id)
        user_uuid = uuid.UUID(current_user_id)
        
        # Export conversation
        export_data = await session_use_case.export_conversation(
            session_id=session_uuid,
            user_id=user_uuid,
            format=format
        )
        
        logger.info(f"Conversation exported for session {session_id} in {format} format")
        return export_data
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except DomainError as e:
        logger.error(f"Domain error in conversation export: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        elif "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Unexpected error in conversation export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while exporting conversation"
        )