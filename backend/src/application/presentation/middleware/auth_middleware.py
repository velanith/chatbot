"""JWT Authentication middleware for FastAPI."""

from typing import Optional, Callable, Awaitable
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from src.application.services.jwt_service import JWTService
from src.domain.exceptions.base_exceptions import AuthenticationError


logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT token authentication.
    
    This middleware validates JWT tokens for protected endpoints and adds
    user information to the request state.
    """
    
    def __init__(
        self,
        app,
        jwt_service: Optional[JWTService] = None,
        exclude_paths: Optional[list] = None
    ):
        """Initialize JWT authentication middleware.
        
        Args:
            app: FastAPI application instance
            jwt_service: JWT service for token validation
            exclude_paths: List of paths to exclude from authentication
        """
        super().__init__(app)
        if jwt_service is None:
            from src.infrastructure.config import get_settings
            settings = get_settings()
            self.jwt_service = JWTService(
                secret_key=settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm,
                expiration_hours=settings.jwt_expiration_hours
            )
        else:
            self.jwt_service = jwt_service
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/health/ready",
            "/health/live",
            "/info",

            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/live",
            "/api/v1/info",

            "/api/v1/auth/register",
            "/api/v1/auth/login",
            
            # Chatbot endpoints (no auth required for demo)
            "/api/v1/chatbot/memory",
            "/api/v1/chatbot/sessions",
            "/api/v1/chatbot/sessions/new",
            "/api/v1/chatbot/simple",
            "/api/v1/chatbot/quick",
            "/api/v1/chatbot/status",
            
            "/"
        ]
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and validate JWT token if required.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response from the next handler or error response
        """
        # Skip authentication for excluded paths
        if self._should_skip_auth(request):
            return await call_next(request)
        
        # Extract and validate JWT token
        try:
            token = self._extract_token(request)
            if not token:
                return self._create_unauthorized_response("Missing authentication token")
            
            # Validate token and extract user info
            user_info = self.jwt_service.validate_token(token)
            
            # Add user info to request state
            request.state.current_user_id = user_info["user_id"]
            request.state.current_username = user_info["sub"]  # JWT uses 'sub' for username
            request.state.is_authenticated = True
            
            logger.debug(f"Authenticated user: {user_info['sub']}")
            
        except AuthenticationError as e:
            logger.warning(f"Authentication error: {str(e)}")
            if "expired" in str(e).lower():
                return self._create_unauthorized_response("Token has expired")
            else:
                return self._create_unauthorized_response("Invalid authentication token")
        
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return self._create_unauthorized_response("Authentication failed")
        
        # Continue to next middleware/endpoint
        return await call_next(request)
    
    def _should_skip_auth(self, request: Request) -> bool:
        """Check if authentication should be skipped for this request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if authentication should be skipped
        """
        path = request.url.path
        logger.info(f"Checking auth for path: {path}")
        logger.info(f"Exclude paths: {self.exclude_paths}")
        
        # Check exact matches
        if path in self.exclude_paths:
            logger.info(f"Skipping auth for path: {path}")
            return True
        
        # Check path prefixes for docs and chatbot
        skip_prefixes = ["/docs", "/redoc", "/api/v1/chatbot/"]
        for prefix in skip_prefixes:
            if path.startswith(prefix):
                logger.info(f"Skipping auth for prefix: {prefix}")
                return True
        
        logger.info(f"Auth required for path: {path}")
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers.
        
        Args:
            request: FastAPI request object
            
        Returns:
            JWT token string or None if not found
        """
        # Try Authorization header first
        authorization = request.headers.get("Authorization")
        if authorization:
            try:
                scheme, token = authorization.split(" ", 1)
                if scheme.lower() == "bearer":
                    return token
            except ValueError:
                pass
        
        # Try query parameter as fallback
        token = request.query_params.get("token")
        if token:
            return token
        
        return None
    
    def _create_unauthorized_response(self, message: str) -> JSONResponse:
        """Create a standardized unauthorized response.
        
        Args:
            message: Error message to include in response
            
        Returns:
            JSONResponse with 401 status code
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "Unauthorized",
                "message": message,
                "details": None
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Current user ID or None if not authenticated
    """
    return getattr(request.state, "current_user_id", None)


def get_current_username(request: Request) -> Optional[str]:
    """Get current username from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Current username or None if not authenticated
    """
    return getattr(request.state, "current_username", None)


def is_authenticated(request: Request) -> bool:
    """Check if current request is authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if request is authenticated
    """
    return getattr(request.state, "is_authenticated", False)


def require_authentication(request: Request) -> None:
    """Require authentication for the current request.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: If request is not authenticated
    """
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Authentication required",
                "details": None
            },
            headers={"WWW-Authenticate": "Bearer"}
        )