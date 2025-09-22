"""Logging middleware for request/response logging."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests."""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        """Initialize logging middleware.
        
        Args:
            app: FastAPI application
            log_requests: Whether to log incoming requests
            log_responses: Whether to log outgoing responses
        """
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with logging and metrics."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract or generate trace ID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        # Extract user ID if available
        user_id = getattr(request.state, 'user_id', None)
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        if self.log_requests:
            await self._log_request(request, request_id, user_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            if self.log_responses:
                await self._log_response(request, response, request_id, duration)
            
            # Add request ID and trace ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request {request_id} failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "url": str(request.url),
                    "duration": duration,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            raise
    

    
    async def _log_request(self, request: Request, request_id: str, user_id: str = None) -> None:
        """Log incoming request."""
        trace_id = getattr(request.state, 'trace_id', None)
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "user_id": user_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else None
            }
        )
    
    async def _log_response(self, request: Request, response: Response, request_id: str, duration: float) -> None:
        """Log outgoing response."""
        trace_id = getattr(request.state, 'trace_id', None)
        logger.info(
            f"Response {request_id}: {response.status_code} in {duration:.3f}s",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration": duration,
                "response_headers": dict(response.headers)
            }
        )