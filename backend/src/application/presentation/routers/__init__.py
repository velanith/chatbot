"""API routers for the presentation layer."""

from .auth_router import router as auth_router
from .chat_router import router as chat_router
from .session_router import router as session_router
from .user_router import router as user_router
from .health_router import router as health_router
from .assessment_router import router as assessment_router
from .topic_router import router as topic_router
from .chatbot_router import router as chatbot_router

__all__ = [
    "auth_router",
    "chat_router", 
    "session_router",
    "user_router",
    "health_router",
    "assessment_router",
    "topic_router",
    "chatbot_router"
]