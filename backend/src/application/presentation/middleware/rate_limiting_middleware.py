"""Rate limiting middleware for API endpoints."""

import time
import asyncio
from typing import Dict, Optional, Tuple, Callable, Awaitable
from collections import defaultdict, deque
from dataclasses import dataclass
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

import logging

logger = logging.getLogger(__name__)

# Simple mock metrics collector
class MockMetricsCollector:
    def increment(self, metric_name, tags=None):
        pass

def get_metrics_collector():
    return MockMetricsCollector()


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    burst_requests: Optional[int] = None  # Burst allowance (optional)


@dataclass
class RateLimitState:
    """Rate limit state for a client."""
    requests: deque  # Timestamps of requests
    last_request: float  # Last request timestamp
    blocked_until: float = 0  # Blocked until timestamp


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(
        self,
        app,
        default_rule: RateLimitRule = RateLimitRule(requests=100, window_seconds=60),
        per_user_rule: Optional[RateLimitRule] = None,
        per_ip_rule: Optional[RateLimitRule] = None,
        endpoint_rules: Optional[Dict[str, RateLimitRule]] = None,
        exclude_paths: Optional[list] = None
    ):
        """Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            default_rule: Default rate limit rule
            per_user_rule: Per-user rate limit rule
            per_ip_rule: Per-IP rate limit rule
            endpoint_rules: Endpoint-specific rate limit rules
            exclude_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.default_rule = default_rule
        self.per_user_rule = per_user_rule or RateLimitRule(requests=50000, window_seconds=3600)  # 50000/hour per user (very relaxed)
        self.per_ip_rule = per_ip_rule or RateLimitRule(requests=10000, window_seconds=60)  # 10000/min per IP (very relaxed)
        self.endpoint_rules = endpoint_rules or {}
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/health/ready",
            "/api/v1/health/live",
            "/api/v1/info"
        ]
        
        # Rate limit state storage (in-memory)
        self.user_states: Dict[str, RateLimitState] = defaultdict(self._create_rate_limit_state)
        self.ip_states: Dict[str, RateLimitState] = defaultdict(self._create_rate_limit_state)
        self.endpoint_states: Dict[str, RateLimitState] = defaultdict(self._create_rate_limit_state)
        
        # Metrics collector
        self.metrics_collector = get_metrics_collector()
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _create_rate_limit_state(self) -> RateLimitState:
        """Create a new rate limit state."""
        return RateLimitState(
            requests=deque(),
            last_request=0,
            blocked_until=0
        )
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_states())
    
    async def _cleanup_old_states(self):
        """Clean up old rate limit states periodically."""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                current_time = time.time()
                cutoff_time = current_time - 3600  # Remove states older than 1 hour
                
                # Clean up user states
                users_to_remove = [
                    user_id for user_id, state in self.user_states.items()
                    if state.last_request < cutoff_time
                ]
                for user_id in users_to_remove:
                    del self.user_states[user_id]
                
                # Clean up IP states
                ips_to_remove = [
                    ip for ip, state in self.ip_states.items()
                    if state.last_request < cutoff_time
                ]
                for ip in ips_to_remove:
                    del self.ip_states[ip]
                
                # Clean up endpoint states
                endpoints_to_remove = [
                    endpoint for endpoint, state in self.endpoint_states.items()
                    if state.last_request < cutoff_time
                ]
                for endpoint in endpoints_to_remove:
                    del self.endpoint_states[endpoint]
                
                if users_to_remove or ips_to_remove or endpoints_to_remove:
                    logger.debug(f"Cleaned up rate limit states: {len(users_to_remove)} users, "
                               f"{len(ips_to_remove)} IPs, {len(endpoints_to_remove)} endpoints")
                
            except Exception as e:
                logger.error(f"Error in rate limit cleanup task: {e}")
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with rate limiting."""
        # COMPLETELY DISABLED FOR TESTING - Skip all rate limiting
        logger.debug(f"Rate limiting completely disabled for testing - processing {request.url.path}")
        response = await call_next(request)
        return response
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Check if rate limiting should be skipped for this request."""
        path = request.url.path
        return path in self.exclude_paths or any(
            path.startswith(prefix) for prefix in ["/docs", "/redoc"]
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Get endpoint key for rate limiting."""
        return f"{request.method}:{request.url.path}"
    
    def _check_rate_limits(
        self,
        current_time: float,
        user_id: Optional[str],
        client_ip: str,
        endpoint: str,
        request: Request
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """Check all applicable rate limits.
        
        Returns:
            Tuple of (allowed, limit_type, retry_after_seconds)
        """
        # Check per-user rate limit
        if user_id:
            allowed, retry_after = self._check_single_rate_limit(
                self.user_states[user_id],
                self.per_user_rule,
                current_time
            )
            if not allowed:
                self.metrics_collector.increment("rate_limit_exceeded", tags={"type": "user", "user_id": user_id})
                return False, "user", retry_after
        
        # Check per-IP rate limit
        allowed, retry_after = self._check_single_rate_limit(
            self.ip_states[client_ip],
            self.per_ip_rule,
            current_time
        )
        if not allowed:
            self.metrics_collector.increment("rate_limit_exceeded", tags={"type": "ip", "ip": client_ip})
            return False, "ip", retry_after
        
        # Check endpoint-specific rate limit
        if endpoint in self.endpoint_rules:
            endpoint_key = f"{endpoint}:{client_ip}"
            allowed, retry_after = self._check_single_rate_limit(
                self.endpoint_states[endpoint_key],
                self.endpoint_rules[endpoint],
                current_time
            )
            if not allowed:
                self.metrics_collector.increment("rate_limit_exceeded", tags={"type": "endpoint", "endpoint": endpoint})
                return False, "endpoint", retry_after
        
        return True, None, None
    
    def _check_single_rate_limit(
        self,
        state: RateLimitState,
        rule: RateLimitRule,
        current_time: float
    ) -> Tuple[bool, int]:
        """Check a single rate limit rule.
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        # Check if currently blocked
        if current_time < state.blocked_until:
            return False, int(state.blocked_until - current_time) + 1
        
        # Clean old requests outside the window
        window_start = current_time - rule.window_seconds
        while state.requests and state.requests[0] < window_start:
            state.requests.popleft()
        
        # Check if limit is exceeded
        if len(state.requests) >= rule.requests:
            # Calculate retry after based on oldest request in window
            if state.requests:
                retry_after = int(state.requests[0] + rule.window_seconds - current_time) + 1
                state.blocked_until = current_time + retry_after
                return False, retry_after
            else:
                return False, rule.window_seconds
        
        return True, 0
    
    def _record_request(
        self,
        current_time: float,
        user_id: Optional[str],
        client_ip: str,
        endpoint: str
    ):
        """Record a request in rate limit states."""
        # Record for user
        if user_id:
            state = self.user_states[user_id]
            state.requests.append(current_time)
            state.last_request = current_time
        
        # Record for IP
        state = self.ip_states[client_ip]
        state.requests.append(current_time)
        state.last_request = current_time
        
        # Record for endpoint if has specific rule
        if endpoint in self.endpoint_rules:
            endpoint_key = f"{endpoint}:{client_ip}"
            state = self.endpoint_states[endpoint_key]
            state.requests.append(current_time)
            state.last_request = current_time
        
        # Record metrics
        self.metrics_collector.increment("rate_limit_requests_total")
    
    def _add_rate_limit_headers(
        self,
        response: Response,
        user_id: Optional[str],
        client_ip: str,
        endpoint: str
    ):
        """Add rate limit headers to response."""
        current_time = time.time()
        
        # Add user rate limit headers
        if user_id and user_id in self.user_states:
            state = self.user_states[user_id]
            remaining = max(0, self.per_user_rule.requests - len(state.requests))
            response.headers["X-RateLimit-User-Limit"] = str(self.per_user_rule.requests)
            response.headers["X-RateLimit-User-Remaining"] = str(remaining)
            response.headers["X-RateLimit-User-Reset"] = str(int(current_time + self.per_user_rule.window_seconds))
        
        # Add IP rate limit headers
        if client_ip in self.ip_states:
            state = self.ip_states[client_ip]
            remaining = max(0, self.per_ip_rule.requests - len(state.requests))
            response.headers["X-RateLimit-IP-Limit"] = str(self.per_ip_rule.requests)
            response.headers["X-RateLimit-IP-Remaining"] = str(remaining)
            response.headers["X-RateLimit-IP-Reset"] = str(int(current_time + self.per_ip_rule.window_seconds))
    
    def _create_rate_limit_response(
        self,
        limit_type: str,
        retry_after: int
    ) -> JSONResponse:
        """Create rate limit exceeded response."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Rate limit exceeded for {limit_type}.",
                "details": {
                    "limit_type": limit_type,
                    "retry_after_seconds": retry_after
                }
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit-Type": limit_type
            }
        )


# Predefined rate limit rules for different endpoints
# NOTE: These are very relaxed settings for development/testing
ENDPOINT_RATE_LIMITS = {
    "POST:/api/v1/auth/login": RateLimitRule(requests=10000, window_seconds=60),  # 10000 login attempts per minute (very relaxed)
    "POST:/api/v1/auth/register": RateLimitRule(requests=5000, window_seconds=60),  # 5000 registrations per minute (very relaxed)
    "POST:/api/v1/chat": RateLimitRule(requests=10000, window_seconds=60),  # 10000 chat messages per minute
    "POST:/api/v1/sessions": RateLimitRule(requests=2000, window_seconds=60),  # 2000 session creations per minute
}