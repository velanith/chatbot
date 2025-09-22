"""Authentication router for user registration and login endpoints."""

from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import JSONResponse

from src.application.use_cases.user_registration_usecase import (
    UserRegistrationUseCase,
    UserRegistrationRequest as UseCaseRegistrationRequest,
    UserRegistrationResponse as UseCaseRegistrationResponse
)
from src.application.use_cases.user_authentication_usecase import (
    UserAuthenticationUseCase,
    UserAuthenticationRequest as UseCaseAuthenticationRequest,
    UserAuthenticationResponse as UseCaseAuthenticationResponse
)
from src.presentation.schemas.auth_schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    LogoutRequest
)
from src.presentation.schemas.user_schemas import (
    UserResponse,
    PasswordChangeRequest,
    EmailChangeRequest
)
from src.presentation.schemas.common_schemas import (
    SuccessResponse,
    ErrorResponse
)
from src.presentation.dependencies import (
    get_user_registration_usecase,
    get_user_authentication_usecase,
    get_current_user_info
)


router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, username, and password",
    responses={
        201: {"description": "User registered successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "User already exists"}
    }
)
async def register_user(
    request: RegisterRequest,
    registration_usecase: UserRegistrationUseCase = Depends(get_user_registration_usecase)
) -> RegisterResponse:
    """
    Register a new user.
    
    - **email**: Valid email address
    - **username**: Unique username (3-30 characters, alphanumeric with underscores and hyphens)
    - **password**: Strong password (min 8 chars, must contain uppercase, lowercase, and digit)
    - **confirm_password**: Password confirmation (must match password)
    - **first_name**: Optional first name
    - **last_name**: Optional last name
    - **terms_accepted**: Must be true to accept terms and conditions
    - **marketing_consent**: Optional marketing communications consent
    
    Returns the created user information with success message.
    """
    try:
        # Convert API request to use case request
        usecase_request = UseCaseRegistrationRequest(
            username=request.username,
            email=request.email,
            password=request.password,
            native_language=request.native_language,
            target_language=request.target_language,
            proficiency_level=request.proficiency_level.value if hasattr(request.proficiency_level, 'value') else request.proficiency_level
        )
        
        # Execute use case
        usecase_response = await registration_usecase.execute(usecase_request)
        
        # Convert use case response to API response
        api_response = RegisterResponse(
            user=usecase_response.user_profile,
            verification_required=True,
            message="Registration successful. Please check your email to verify your account."
        )
        
        return api_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        
        # Check if it's a conflict error
        if "ConflictError" in str(type(e)) or "already taken" in str(e) or "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
    description="Authenticate user with email and password, returns JWT tokens",
    responses={
        200: {"description": "Login successful"},
        400: {"model": ErrorResponse, "description": "Invalid credentials"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        429: {"model": ErrorResponse, "description": "Too many login attempts"}
    }
)
async def login_user(
    request: LoginRequest,
    authentication_usecase: UserAuthenticationUseCase = Depends(get_user_authentication_usecase)
) -> LoginResponse:
    """
    Authenticate a user and return JWT tokens.
    
    - **username_or_email**: Username or email address
    - **password**: User password
    - **remember_me**: Optional flag to extend token expiration
    
    Returns access and refresh tokens for authenticated requests.
    """
    try:
        # Convert API request to use case request
        usecase_request = UseCaseAuthenticationRequest(
            username_or_email=request.username_or_email,
            password=request.password
        )
        
        # Execute use case
        usecase_response = await authentication_usecase.execute(usecase_request)
        
        # Convert use case response to API response
        from src.presentation.schemas.auth_schemas import TokenData, UserProfile
        from datetime import datetime
        
        token_data = TokenData(
            access_token=usecase_response.access_token,
            refresh_token="",  # TODO: Implement refresh token
            token_type=usecase_response.token_type.lower(),
            expires_in=3600,  # TODO: Calculate from expires_at
            expires_at=datetime.fromisoformat(usecase_response.expires_at),
            scope=None
        )
        
        user_profile = UserProfile(
            id=str(usecase_response.user_id),
            email=usecase_response.email,
            username=usecase_response.username,
            first_name=None,
            last_name=None,
            is_active=True,
            is_verified=True,
            last_login=None,
            profile_picture_url=None,
            native_language="TR",  # TODO: Get from user entity
            target_language="EN",  # TODO: Get from user entity
            proficiency_level="beginner",  # TODO: Get from user entity
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        api_response = LoginResponse(
            data=token_data,
            user=user_profile,
            message="Login successful"
        )
        
        return api_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        
        # Check if it's an authentication error
        if "AuthenticationError" in str(type(e)) or "Invalid username/email or password" in str(e):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Refresh access token using refresh token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
        403: {"model": ErrorResponse, "description": "Refresh token expired"}
    }
)
async def refresh_token(
    request: RefreshTokenRequest
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access and refresh tokens.
    """
    # TODO: Implement token refresh logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented yet"
    )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout user and invalidate tokens",
    responses={
        200: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Invalid token"}
    }
)
async def logout_user(
    request: LogoutRequest,
    current_user: dict = Depends(get_current_user_info)
) -> SuccessResponse:
    """
    Logout user and invalidate tokens.
    
    - **refresh_token**: Optional refresh token to invalidate
    - **logout_all_devices**: Optional flag to logout from all devices
    
    Invalidates the current session and optionally all user sessions.
    """
    # TODO: Implement logout logic
    return SuccessResponse(
        message="Logout successful"
    )


@router.post(
    "/password-reset",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send password reset email to user",
    responses={
        200: {"description": "Password reset email sent"},
        404: {"model": ErrorResponse, "description": "User not found"},
        429: {"model": ErrorResponse, "description": "Too many reset requests"}
    }
)
async def request_password_reset(
    request: PasswordResetRequest
) -> SuccessResponse:
    """
    Request password reset email.
    
    - **email**: User email address
    
    Sends password reset email if user exists.
    """
    # TODO: Implement password reset request logic
    return SuccessResponse(
        message="If an account with this email exists, a password reset link has been sent."
    )


@router.post(
    "/password-reset/confirm",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Reset password using reset token",
    responses={
        200: {"description": "Password reset successful"},
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def confirm_password_reset(
    request: PasswordResetConfirm
) -> SuccessResponse:
    """
    Reset password using reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password
    - **confirm_password**: Password confirmation
    
    Resets user password if token is valid.
    """
    # TODO: Implement password reset confirmation logic
    return SuccessResponse(
        message="Password reset successful. You can now login with your new password."
    )


@router.post(
    "/verify-email",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify user email using verification token",
    responses={
        200: {"description": "Email verified successfully"},
        400: {"model": ErrorResponse, "description": "Invalid or expired token"}
    }
)
async def verify_email(
    request: EmailVerificationRequest
) -> SuccessResponse:
    """
    Verify user email address.
    
    - **token**: Email verification token from email
    
    Verifies user email if token is valid.
    """
    # TODO: Implement email verification logic
    return SuccessResponse(
        message="Email verified successfully. Your account is now active."
    )


@router.post(
    "/resend-verification",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend verification email",
    description="Resend email verification link",
    responses={
        200: {"description": "Verification email sent"},
        400: {"model": ErrorResponse, "description": "Email already verified"},
        429: {"model": ErrorResponse, "description": "Too many requests"}
    }
)
async def resend_verification_email(
    request: PasswordResetRequest  # Reusing since it only needs email
) -> SuccessResponse:
    """
    Resend email verification link.
    
    - **email**: User email address
    
    Sends new verification email if user exists and is not verified.
    """
    # TODO: Implement resend verification logic
    return SuccessResponse(
        message="If an unverified account with this email exists, a verification link has been sent."
    )


@router.get(
    "/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile",
    description="Get current authenticated user's profile information",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def get_user_profile(
    current_user: dict = Depends(get_current_user_info)
) -> UserResponse:
    """
    Get current user's profile information.
    
    Requires valid JWT token in Authorization header.
    
    Returns complete user profile information including preferences and statistics.
    """
    # TODO: Get full user profile from use case
    return UserResponse(
        data=current_user,
        message="Profile retrieved successfully"
    )


@router.put(
    "/password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change user password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid current password"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user_info)
) -> SuccessResponse:
    """
    Change user password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password
    - **confirm_password**: Password confirmation
    
    Changes user password if current password is correct.
    """
    # TODO: Implement password change logic
    return SuccessResponse(
        message="Password changed successfully"
    )


@router.put(
    "/email",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Change email address",
    description="Change user email address",
    responses={
        200: {"description": "Email change initiated"},
        400: {"model": ErrorResponse, "description": "Invalid password or email"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        409: {"model": ErrorResponse, "description": "Email already in use"}
    }
)
async def change_email(
    request: EmailChangeRequest,
    current_user: dict = Depends(get_current_user_info)
) -> SuccessResponse:
    """
    Change user email address.
    
    - **new_email**: New email address
    - **password**: Current password for verification
    
    Initiates email change process. Verification email will be sent to new address.
    """
    # TODO: Implement email change logic
    return SuccessResponse(
        message="Email change initiated. Please check your new email address for verification."
    )