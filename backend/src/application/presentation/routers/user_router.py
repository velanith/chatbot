"""User router for user management endpoints."""

from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from src.presentation.schemas.user_schemas import (
    UserResponse,
    UserUpdateRequest,
    UserPreferencesSchema,
    AccountDeletionRequest,
    UserSearchRequest,
    UserListItem,
    BulkUserOperation
)
from src.presentation.schemas.user_flow_schemas import (
    UserFlowStateResponse,
    LanguagePreferencesRequest,
    LanguagePreferencesResponse,
    LevelSelectionOptionsResponse
)
from src.presentation.schemas.chat_schemas import ProficiencyLevel
from src.presentation.schemas.common_schemas import (
    ErrorResponse,
    SuccessResponse,
    PaginationResponse
)
from src.presentation.dependencies import get_current_user_info, get_admin_user, get_user_flow_use_case
from src.application.use_cases.user_flow_use_case import UserFlowUseCase

router = APIRouter()


@router.get(
    "/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile",
    description="Get current user's complete profile information",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def get_user_profile(
    current_user: dict = Depends(get_current_user_info)
) -> UserResponse:
    """
    Get current user's complete profile information.
    
    Returns user profile with preferences, statistics, and achievements.
    """
    # TODO: Implement full profile retrieval
    return UserResponse(
        data=current_user,
        message="Profile retrieved successfully"
    )


@router.put(
    "/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    description="Update user profile information",
    responses={
        200: {"description": "Profile updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid profile data"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        409: {"model": ErrorResponse, "description": "Email or username already in use"}
    }
)
async def update_user_profile(
    request: UserUpdateRequest,
    current_user: dict = Depends(get_current_user_info)
) -> UserResponse:
    """
    Update user profile information.
    
    - **first_name**: Optional first name
    - **last_name**: Optional last name
    - **email**: Optional new email address
    - **username**: Optional new username
    - **profile_picture_url**: Optional profile picture URL
    - **bio**: Optional user bio
    - **preferences**: Optional user preferences
    
    Returns updated user profile.
    """
    # TODO: Implement profile update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Profile update not implemented yet"
    )


@router.get(
    "/preferences",
    response_model=UserPreferencesSchema,
    status_code=status.HTTP_200_OK,
    summary="Get user preferences",
    description="Get user's learning preferences and settings",
    responses={
        200: {"description": "Preferences retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def get_user_preferences(
    current_user: dict = Depends(get_current_user_info)
) -> UserPreferencesSchema:
    """
    Get user's learning preferences and settings.
    
    Returns complete user preferences including learning goals and UI settings.
    """
    # TODO: Implement preferences retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Preferences retrieval not implemented yet"
    )


@router.put(
    "/preferences",
    response_model=UserPreferencesSchema,
    status_code=status.HTTP_200_OK,
    summary="Update user preferences",
    description="Update user's learning preferences and settings",
    responses={
        200: {"description": "Preferences updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid preferences data"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def update_user_preferences(
    request: UserPreferencesSchema,
    current_user: dict = Depends(get_current_user_info)
) -> UserPreferencesSchema:
    """
    Update user's learning preferences and settings.
    
    - **proficiency_level**: Current proficiency level
    - **learning_goals**: Learning goals (max 5)
    - **notification_preferences**: Notification preferences
    - **interface_language**: Interface language
    - **theme**: UI theme preference
    - **daily_goal_minutes**: Daily learning goal in minutes
    - **correction_level**: Correction intensity level (1-5)
    - **auto_exercises**: Automatically generate exercises
    - **voice_enabled**: Enable voice features
    - **timezone**: User timezone
    
    Returns updated preferences.
    """
    # TODO: Implement preferences update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Preferences update not implemented yet"
    )


@router.get(
    "/language-preferences",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get language preferences",
    description="Get user's language learning preferences",
    responses={
        200: {"description": "Language preferences retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def get_language_preferences(
    current_user: dict = Depends(get_current_user_info)
) -> dict:
    """
    Get user's language learning preferences.
    
    Returns native language, target language, and proficiency level.
    """
    # TODO: Implement language preferences retrieval
    return {
        "native_language": "TR",
        "target_language": "EN", 
        "proficiency_level": "A2"
    }


@router.put(
    "/language-preferences",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update language preferences",
    description="Update user's language learning preferences",
    responses={
        200: {"description": "Language preferences updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid language preferences"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def update_language_preferences(
    native_language: str,
    target_language: str,
    proficiency_level: ProficiencyLevel,
    current_user: dict = Depends(get_current_user_info)
) -> dict:
    """
    Update user's language learning preferences.
    
    - **native_language**: User's native language (ISO 639-1 code)
    - **target_language**: Language user wants to learn (ISO 639-1 code)
    - **proficiency_level**: Current proficiency level (A1, A2, B1, B2, C1, C2)
    
    Returns updated language preferences.
    """
    # TODO: Implement language preferences update
    return {
        "native_language": native_language.upper(),
        "target_language": target_language.upper(),
        "proficiency_level": proficiency_level.value,
        "message": "Language preferences updated successfully"
    }


@router.get(
    "/stats",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get user statistics",
    description="Get user's learning statistics and progress",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def get_user_stats(
    current_user: dict = Depends(get_current_user_info)
) -> dict:
    """
    Get user's learning statistics and progress.
    
    Returns comprehensive learning statistics including sessions, corrections, and achievements.
    """
    # TODO: Implement user statistics
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User statistics not implemented yet"
    )


@router.get(
    "/achievements",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get user achievements",
    description="Get user's earned achievements",
    responses={
        200: {"description": "Achievements retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def get_user_achievements(
    current_user: dict = Depends(get_current_user_info)
) -> List[dict]:
    """
    Get user's earned achievements.
    
    Returns list of achievements with earn dates and descriptions.
    """
    # TODO: Implement achievements retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Achievements retrieval not implemented yet"
    )


@router.post(
    "/deactivate",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate account",
    description="Temporarily deactivate user account",
    responses={
        200: {"description": "Account deactivated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid password"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def deactivate_account(
    password: str,
    current_user: dict = Depends(get_current_user_info)
) -> SuccessResponse:
    """
    Temporarily deactivate user account.
    
    - **password**: Current password for verification
    
    Deactivates account but preserves data for potential reactivation.
    """
    # TODO: Implement account deactivation
    return SuccessResponse(
        message="Account deactivated successfully. You can reactivate by logging in."
    )


@router.post(
    "/delete",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete account",
    description="Permanently delete user account",
    responses={
        200: {"description": "Account deletion initiated"},
        400: {"model": ErrorResponse, "description": "Invalid confirmation or password"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def delete_account(
    request: AccountDeletionRequest,
    current_user: dict = Depends(get_current_user_info)
) -> SuccessResponse:
    """
    Permanently delete user account.
    
    - **password**: Current password for verification
    - **confirmation**: Must be "delete my account"
    - **reason**: Optional reason for deletion
    
    Initiates account deletion process. Account will be deleted after grace period.
    """
    # TODO: Implement account deletion
    return SuccessResponse(
        message="Account deletion initiated. Your account will be permanently deleted in 30 days."
    )


@router.post(
    "/export",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Export user data",
    description="Export all user data for download",
    responses={
        200: {"description": "Data export initiated"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        429: {"model": ErrorResponse, "description": "Too many export requests"}
    }
)
async def export_user_data(
    format: str = Query("json", description="Export format (json, csv)"),
    include_sessions: bool = Query(True, description="Include session data"),
    include_messages: bool = Query(True, description="Include message data"),
    current_user: dict = Depends(get_current_user_info)
) -> dict:
    """
    Export all user data for download.
    
    - **format**: Export format (json, csv)
    - **include_sessions**: Include session data in export
    - **include_messages**: Include message data in export
    
    Returns download link for exported data.
    """
    # TODO: Implement data export
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Data export not implemented yet"
    )


# User flow management endpoints
@router.get(
    "/flow-state",
    response_model=UserFlowStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user flow state",
    description="Get current user's onboarding and flow state",
    responses={
        200: {"description": "Flow state retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_user_flow_state(
    current_user: dict = Depends(get_current_user_info),
    user_flow_use_case: UserFlowUseCase = Depends(get_user_flow_use_case)
) -> UserFlowStateResponse:
    """
    Get current user's onboarding and flow state.
    
    Returns the user's current position in the onboarding flow, including:
    - Current flow state (language_selection, level_selection, etc.)
    - Completion status of each onboarding step
    - Next required action
    - Additional metadata about user preferences
    """
    try:
        import uuid
        user_id = uuid.UUID(current_user["user_id"])
        
        flow_state = await user_flow_use_case.handle_post_login(user_id)
        
        return UserFlowStateResponse(
            message="User flow state retrieved successfully",
            data={
                "user_id": str(flow_state.user_id),
                "current_state": flow_state.current_state,
                "has_language_preferences": flow_state.has_language_preferences,
                "has_level_assessment": flow_state.has_level_assessment,
                "has_topic_preferences": flow_state.has_topic_preferences,
                "onboarding_completed": flow_state.onboarding_completed,
                "next_action": flow_state.next_action,
                "metadata": flow_state.metadata
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user flow state: {str(e)}"
        )


@router.post(
    "/language-preferences",
    response_model=LanguagePreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Set language preferences",
    description="Set user's native and target language preferences",
    responses={
        200: {"description": "Language preferences updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid language preferences"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def set_language_preferences(
    request: LanguagePreferencesRequest,
    current_user: dict = Depends(get_current_user_info),
    user_flow_use_case: UserFlowUseCase = Depends(get_user_flow_use_case)
) -> LanguagePreferencesResponse:
    """
    Set user's native and target language preferences.
    
    - **native_language**: User's native language code (e.g., "TR", "EN")
    - **target_language**: Language user wants to learn (e.g., "EN", "ES")
    
    Updates the user's language preferences and returns the updated flow state.
    This typically moves the user from language_selection to level_selection state.
    """
    try:
        import uuid
        user_id = uuid.UUID(current_user["user_id"])
        
        flow_state = await user_flow_use_case.set_language_preferences(
            user_id=user_id,
            native_language=request.native_language,
            target_language=request.target_language
        )
        
        return LanguagePreferencesResponse(
            message="Language preferences updated successfully",
            data={
                "user_id": str(flow_state.user_id),
                "current_state": flow_state.current_state,
                "has_language_preferences": flow_state.has_language_preferences,
                "has_level_assessment": flow_state.has_level_assessment,
                "has_topic_preferences": flow_state.has_topic_preferences,
                "onboarding_completed": flow_state.onboarding_completed,
                "next_action": flow_state.next_action,
                "metadata": flow_state.metadata
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language preferences: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update language preferences: {str(e)}"
        )


@router.get(
    "/level-options",
    response_model=LevelSelectionOptionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get level selection options",
    description="Get available level selection options for the user",
    responses={
        200: {"description": "Level options retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_level_selection_options(
    current_user: dict = Depends(get_current_user_info),
    user_flow_use_case: UserFlowUseCase = Depends(get_user_flow_use_case)
) -> LevelSelectionOptionsResponse:
    """
    Get available level selection options for the user.
    
    Returns information about:
    - Whether level assessment is available
    - Whether manual level selection is available
    - List of available proficiency levels with descriptions
    - Current user's level information (if any)
    - Previous assessment information (if any)
    """
    try:
        import uuid
        user_id = uuid.UUID(current_user["user_id"])
        
        options = await user_flow_use_case.initiate_level_selection(user_id)
        
        # Convert level options to the expected format
        available_levels = [
            {
                "code": level["code"],
                "name": level["name"],
                "description": level["description"]
            }
            for level in options.get_available_levels()
        ]
        
        return LevelSelectionOptionsResponse(
            message="Level selection options retrieved successfully",
            data={
                "assessment_available": options.assessment_available,
                "manual_selection_available": options.manual_selection_available,
                "available_levels": available_levels,
                "current_level": options.current_level,
                "assessed_level": options.assessed_level,
                "assessment_date": options.assessment_date
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve level selection options: {str(e)}"
        )


# Admin endpoints
@router.get(
    "/admin/users",
    response_model=PaginationResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin)",
    description="Get paginated list of all users",
    responses={
        200: {"description": "Users retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"}
    }
)
async def list_users_admin(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    admin_user: dict = Depends(get_admin_user)
) -> PaginationResponse:
    """
    Get paginated list of all users (Admin only).
    
    - **page**: Page number (default 1)
    - **per_page**: Items per page (1-100, default 20)
    - **search**: Optional search query
    - **is_active**: Optional filter by active status
    - **is_verified**: Optional filter by verified status
    
    Returns paginated list of users with basic information.
    """
    # TODO: Implement admin user listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin user listing not implemented yet"
    )


@router.get(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user details (Admin)",
    description="Get detailed information about a specific user",
    responses={
        200: {"description": "User retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "User not found"}
    }
)
async def get_user_admin(
    user_id: str,
    admin_user: dict = Depends(get_admin_user)
) -> UserResponse:
    """
    Get detailed information about a specific user (Admin only).
    
    - **user_id**: User ID
    
    Returns complete user information including sensitive data.
    """
    # TODO: Implement admin user retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin user retrieval not implemented yet"
    )


@router.post(
    "/admin/users/bulk",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk user operations (Admin)",
    description="Perform bulk operations on multiple users",
    responses={
        200: {"description": "Bulk operation completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid operation parameters"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"}
    }
)
async def bulk_user_operations(
    request: BulkUserOperation,
    admin_user: dict = Depends(get_admin_user)
) -> SuccessResponse:
    """
    Perform bulk operations on multiple users (Admin only).
    
    - **user_ids**: List of user IDs (max 100)
    - **operation**: Operation to perform (activate, deactivate, verify, unverify, delete)
    - **parameters**: Optional operation parameters
    
    Performs the specified operation on all selected users.
    """
    # TODO: Implement bulk user operations
    return SuccessResponse(
        message=f"Bulk {request.operation} operation completed for {len(request.user_ids)} users"
    )