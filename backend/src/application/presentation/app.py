"""FastAPI application setup and configuration."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from pydantic import ValidationError
import logging

from src.infrastructure.config import get_settings
from src.infrastructure.database.connection import DatabaseConnection
from src.presentation.middleware.error_handler import setup_error_handlers
from src.presentation.middleware.auth_middleware import JWTAuthenticationMiddleware
from src.presentation.middleware.logging_middleware import LoggingMiddleware
# from src.presentation.middleware.rate_limiting_middleware import RateLimitingMiddleware, ENDPOINT_RATE_LIMITS
from src.presentation.dependencies import setup_dependencies
from src.presentation.routers import (
    auth_router,
    chat_router,
    session_router,
    user_router,
    health_router,
    assessment_router,
    topic_router,
    chatbot_router
)
from src.presentation.routers.language_chat_router import router as language_chat_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up FastAPI application...")
    
    # Initialize database connection
    settings = get_settings()
    db_connection = DatabaseConnection(settings.database_url)
    await db_connection.connect()
    
    # Create database tables
    await db_connection.create_tables()
    
    # Store database connection in app state
    app.state.db_connection = db_connection
    
    logger.info("FastAPI application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    
    # Close database connection
    if hasattr(app.state, 'db_connection'):
        await app.state.db_connection.disconnect()
    
    logger.info("FastAPI application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Polyglot API",
        description="AI-powered polyglot language learning platform with personalized tutoring and conversation practice",
        version="1.0.0",
        docs_url="/docs" if settings.app_environment != "production" else None,
        redoc_url="/redoc" if settings.app_environment != "production" else None,
        lifespan=lifespan
    )
    
    # Configure CORS
    setup_cors(app, settings)
    
    # Add security headers middleware
    setup_security_headers(app, settings)
    
    # Setup logging middleware (should be first)
    app.add_middleware(
        LoggingMiddleware,
        log_requests=True,
        log_responses=settings.app_environment == "development"
    )
    
    # Setup rate limiting middleware (before auth) - Only in production
    if settings.app_environment == "production":
        from src.presentation.middleware.rate_limiting_middleware import RateLimitingMiddleware, ENDPOINT_RATE_LIMITS
        app.add_middleware(
            RateLimitingMiddleware,
            endpoint_rules=ENDPOINT_RATE_LIMITS
        )
    
    # Setup JWT authentication middleware
    app.add_middleware(JWTAuthenticationMiddleware)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup dependencies
    setup_dependencies(app)
    
    # Include routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(language_chat_router, prefix="/api/v1/language-chat", tags=["Language Learning Chat"])
    app.include_router(session_router, prefix="/api/v1", tags=["Sessions"])
    app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(assessment_router, prefix="/api/v1/assessment", tags=["Assessment"])
    app.include_router(topic_router, prefix="/api/v1/topics", tags=["Topics"])
    app.include_router(chatbot_router, prefix="/api/v1/chatbot", tags=["Chatbot"])
    
    # Add public monitoring endpoints (no auth required)
    app.include_router(health_router, prefix="", tags=["Monitoring"])
    
    # API root endpoint
    @app.get("/")
    async def read_root():
        """API root endpoint."""
        return {
            "message": "Polyglot Language Learning API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


def setup_cors(app: FastAPI, settings) -> None:
    """Configure CORS middleware."""
    # Define allowed origins based on environment
    if settings.app_environment == "development":
        allowed_origins = [
            "https://polygl0t.vercel.app",
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:8001",
        ]
        # Add any configured CORS origins
        if settings.parsed_cors_origins:
            allowed_origins.extend(settings.parsed_cors_origins)
    elif settings.app_environment == "testing":
        allowed_origins = ["*"]
    else:
        # Production - be more permissive for now to fix CORS issues
        allowed_origins = [
            "https://polygl0t.vercel.app",
            "https://polyglot-1.onrender.com",
        ]
        # Add configured origins
        if settings.parsed_cors_origins:
            allowed_origins.extend(settings.parsed_cors_origins)
        
        # Temporary: Allow all HTTPS origins for production debugging
        allowed_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    logger.info(f"CORS configured for environment: {settings.app_environment}")
    logger.info(f"CORS configured for origins: {allowed_origins}")
    logger.info(f"Raw CORS origins from settings: {settings.cors_origins}")
    logger.info(f"Parsed CORS origins: {settings.parsed_cors_origins}")


def setup_security_headers(app: FastAPI, settings) -> None:
    """Configure security headers middleware."""
    
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        
        # Security headers for production
        if settings.app_environment == "production":
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        return response
    
    logger.info("Security headers configured")


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.presentation.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_environment == "development",
        log_level="info"
    )