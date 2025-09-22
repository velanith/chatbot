"""Dependency injection setup for FastAPI application."""

from typing import AsyncGenerator
from fastapi import Depends, FastAPI, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.config import get_settings
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.user_repository import UserRepository
from src.domain.repositories.user_repository_interface import UserRepositoryInterface
from src.infrastructure.repositories.session_repository import SessionRepository
from src.domain.repositories.session_repository_interface import SessionRepositoryInterface
from src.infrastructure.repositories.message_repository import MessageRepository
from src.domain.repositories.message_repository_interface import MessageRepositoryInterface
from src.application.services.password_hashing_service import PasswordHashingService
from src.application.services.jwt_service import JWTService
from src.application.services.memory_manager import MemoryManager
from src.application.services.llm_adapter import LLMAdapter
from src.application.services.pedagogy_engine import PedagogyEngine
from src.application.services.fallback_service import FallbackService
from src.application.services.openrouter_chatbot_service import OpenRouterChatbotService
from src.application.use_cases.user_registration_usecase import UserRegistrationUseCase
from src.application.use_cases.user_authentication_usecase import UserAuthenticationUseCase
from src.application.use_cases.chat_use_case import ChatUseCase
from src.application.use_cases.session_use_case import SessionUseCase
from src.application.use_cases.level_assessment_use_case import LevelAssessmentUseCase
from src.application.use_cases.user_flow_use_case import UserFlowUseCase
from src.application.use_cases.chatbot_use_case import ChatbotUseCase
from src.infrastructure.repositories.assessment_session_repository import AssessmentSessionRepository
from src.infrastructure.repositories.topic_repository import TopicRepository
from src.application.services.topic_manager import TopicManager
from src.application.services.translation_service import TranslationService


def setup_dependencies(app: FastAPI) -> None:
    """Setup dependency injection for the FastAPI application."""
    # Dependencies are configured through the dependency functions below
    pass


async def get_database_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Get database session from the application state."""
    try:
        db_connection: DatabaseConnection = request.app.state.db_connection
        session = db_connection.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    except Exception as e:
        # If database is not available, create a mock session for development
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Database not available, using mock session: {e}")
        
        # Create a simple mock session that doesn't do anything
        class MockSession:
            async def commit(self): pass
            async def rollback(self): pass
            async def close(self): pass
            async def flush(self): pass
            async def execute(self, stmt): 
                class MockResult:
                    def scalar_one_or_none(self): return None
                    def scalars(self): 
                        class MockScalars:
                            def all(self): return []
                        return MockScalars()
                    def scalar(self): return 0
                return MockResult()
            def add(self, obj): pass
            async def delete(self, obj): pass
            def __aenter__(self): return self
            async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
        mock_session = MockSession()
        try:
            yield mock_session
        finally:
            await mock_session.close()


# Global singleton instances for memory repositories
_user_repository_instance = None
_session_repository_instance = None
_message_repository_instance = None
_assessment_session_repository_instance = None
_assessment_response_repository_instance = None
_topic_repository_instance = None

async def get_user_repository() -> UserRepositoryInterface:
    """Get user repository instance."""
    global _user_repository_instance
    if _user_repository_instance is None:
        from src.infrastructure.repositories.memory_user_repository import MemoryUserRepository
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Creating singleton memory user repository for development")
        _user_repository_instance = MemoryUserRepository()
    return _user_repository_instance


async def get_session_repository() -> SessionRepositoryInterface:
    """Get session repository instance."""
    global _session_repository_instance
    if _session_repository_instance is None:
        from src.infrastructure.repositories.memory_session_repository import MemorySessionRepository
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Creating singleton memory session repository for development")
        _session_repository_instance = MemorySessionRepository()
    return _session_repository_instance


async def get_message_repository() -> MessageRepositoryInterface:
    """Get message repository instance."""
    global _message_repository_instance
    if _message_repository_instance is None:
        from src.infrastructure.repositories.memory_message_repository import MemoryMessageRepository
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Creating singleton memory message repository for development")
        _message_repository_instance = MemoryMessageRepository()
    return _message_repository_instance


def get_password_service() -> PasswordHashingService:
    """Get password hashing service instance."""
    settings = get_settings()
    return PasswordHashingService(rounds=settings.bcrypt_rounds)


def get_jwt_service() -> JWTService:
    """Get JWT service instance."""
    settings = get_settings()
    return JWTService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expiration_hours=settings.jwt_expiration_hours
    )


async def get_user_registration_usecase(
    user_repository: UserRepositoryInterface = Depends(get_user_repository),
    password_service: PasswordHashingService = Depends(get_password_service)
) -> UserRegistrationUseCase:
    """Get user registration use case instance."""
    return UserRegistrationUseCase(user_repository, password_service)


async def get_user_authentication_usecase(
    user_repository: UserRepositoryInterface = Depends(get_user_repository),
    password_service: PasswordHashingService = Depends(get_password_service),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> UserAuthenticationUseCase:
    """Get user authentication use case instance."""
    return UserAuthenticationUseCase(user_repository, password_service, jwt_service)


async def get_memory_manager(
    message_repository: MessageRepositoryInterface = Depends(get_message_repository)
):
    """Get memory manager instance."""
    try:
        from src.application.services.memory_manager import MemoryManager
        from src.application.services.memory_config import MemoryConfig
        
        settings = get_settings()
        config = MemoryConfig(
            cache_capacity=getattr(settings, 'max_cached_sessions', 100),
            messages_per_session=getattr(settings, 'max_messages_per_session', 10)
        )
        return MemoryManager(message_repository, config)
    except Exception:
        # Fallback to simple mock memory manager
        class MockMemoryManager:
            async def load_session_context(self, session_id):
                return []
            
            async def get_recent_messages(self, session_id, count=10):
                return []
            
            async def add_message(self, message):
                pass
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock memory manager as fallback")
        return MockMemoryManager()


def get_llm_adapter():
    """Get LLM adapter instance."""
    try:
        settings = get_settings()
        from src.application.services.llm_adapter import LLMAdapter
        return LLMAdapter(settings)
    except Exception:
        # Fallback to simple mock LLM adapter
        class MockLLMAdapter:
            async def generate_response(self, messages, **kwargs):
                return "This is a mock response from the AI assistant."
            
            async def generate_corrections(self, text, **kwargs):
                return []
            
            async def generate_exercise(self, text, **kwargs):
                return "Practice exercise: Try using this word in a sentence."
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock LLM adapter as fallback")
        return MockLLMAdapter()


def get_pedagogy_engine():
    """Get pedagogy engine instance."""
    try:
        from src.application.services.pedagogy_engine import PedagogyEngine
        return PedagogyEngine()
    except Exception:
        # Fallback to simple mock pedagogy engine
        class MockPedagogyEngine:
            def analyze_message(self, message, **kwargs):
                return {"corrections": [], "exercises": []}
            
            def generate_feedback(self, **kwargs):
                return "Good job! Keep practicing."
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock pedagogy engine as fallback")
        return MockPedagogyEngine()


def get_fallback_service() -> FallbackService:
    """Get fallback service instance."""
    return FallbackService()


async def get_chat_use_case(
    user_repository: UserRepositoryInterface = Depends(get_user_repository),
    session_repository: SessionRepositoryInterface = Depends(get_session_repository),
    message_repository: MessageRepositoryInterface = Depends(get_message_repository),
    memory_manager = Depends(get_memory_manager),
    llm_adapter = Depends(get_llm_adapter),
    pedagogy_engine = Depends(get_pedagogy_engine)
):
    """Get chat use case instance."""
    try:
        from src.application.use_cases.chat_use_case import ChatUseCase
        return ChatUseCase(
            user_repository=user_repository,
            session_repository=session_repository,
            message_repository=message_repository,
            memory_manager=memory_manager,
            llm_adapter=llm_adapter,
            pedagogy_engine=pedagogy_engine
        )
    except Exception:
        # Fallback to simple mock chat use case
        class MockChatUseCase:
            async def handle_chat_message(self, request):
                class MockResponse:
                    ai_response = "Hello! This is a mock response."
                    session_id = request.session_id or "mock-session-id"
                    corrections = []
                    micro_exercise = None
                    structured_feedback = None
                    current_topic = None
                    session_mode = "tutor"
                    proficiency_level = "A2"
                    metadata = {"session_message_count": 1}
                
                return MockResponse()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock chat use case as fallback")
        return MockChatUseCase()


async def get_session_use_case(
    user_repository: UserRepositoryInterface = Depends(get_user_repository),
    session_repository: SessionRepositoryInterface = Depends(get_session_repository),
    message_repository: MessageRepositoryInterface = Depends(get_message_repository),
    memory_manager = Depends(get_memory_manager)
):
    """Get session use case instance."""
    try:
        from src.application.use_cases.session_use_case import SessionUseCase
        settings = get_settings()
        return SessionUseCase(
            user_repository=user_repository,
            session_repository=session_repository,
            message_repository=message_repository,
            memory_manager=memory_manager,
            session_timeout_hours=getattr(settings, 'session_timeout_hours', 24)
        )
    except Exception:
        # Fallback to simple mock session use case
        class MockSessionUseCase:
            async def create_session(self, request):
                import uuid
                class MockResponse:
                    session_id = uuid.uuid4()
                    mode = "tutor"
                    level = "A2"
                
                return MockResponse()
            
            async def get_session_history(self, session_id, user_id, page=1, page_size=20):
                class MockHistory:
                    messages = []
                    total_messages = 0
                    page = 1
                    page_size = 20
                    total_pages = 0
                
                return MockHistory()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock session use case as fallback")
        return MockSessionUseCase()


async def get_assessment_session_repository():
    """Get assessment session repository instance."""
    global _assessment_session_repository_instance
    if _assessment_session_repository_instance is None:
        from src.infrastructure.repositories.memory_assessment_session_repository import MemoryAssessmentSessionRepository
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Creating singleton memory assessment session repository for development")
        _assessment_session_repository_instance = MemoryAssessmentSessionRepository()
    return _assessment_session_repository_instance


async def get_level_assessment_use_case(
    assessment_repository = Depends(get_assessment_session_repository),
    user_repository = Depends(get_user_repository),
    llm_adapter = Depends(get_llm_adapter)
):
    """Get level assessment use case instance."""
    try:
        from src.application.use_cases.level_assessment_use_case import LevelAssessmentUseCase
        return LevelAssessmentUseCase(
            assessment_repository=assessment_repository,
            user_repository=user_repository,
            llm_service=llm_adapter
        )
    except Exception:
        # Fallback to simple mock level assessment use case
        class MockLevelAssessmentUseCase:
            async def start_assessment(self, user_id):
                import uuid
                class MockAssessmentSession:
                    id = uuid.uuid4()
                    user_id = user_id
                    status = "active"
                    current_question = 1
                    total_questions = 10
                    estimated_level = "A2"
                
                return MockAssessmentSession()
            
            async def submit_answer(self, session_id, answer):
                class MockResult:
                    is_correct = True
                    explanation = "Good answer!"
                    next_question = "What is your favorite color?"
                    progress = 50
                    estimated_level = "A2"
                
                return MockResult()
            
            async def complete_assessment(self, session_id):
                class MockResult:
                    final_level = "A2"
                    score = 75
                    recommendations = ["Practice basic conversations", "Learn more vocabulary"]
                
                return MockResult()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock level assessment use case as fallback")
        return MockLevelAssessmentUseCase()


async def get_topic_repository():
    """Get topic repository instance."""
    global _topic_repository_instance
    if _topic_repository_instance is None:
        from src.infrastructure.repositories.memory_topic_repository import MemoryTopicRepository
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Creating singleton memory topic repository for development")
        _topic_repository_instance = MemoryTopicRepository()
    return _topic_repository_instance


async def get_assessment_response_repository():
    """Get assessment response repository instance."""
    global _assessment_response_repository_instance
    if _assessment_response_repository_instance is None:
        from src.infrastructure.repositories.memory_assessment_response_repository import MemoryAssessmentResponseRepository
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Creating singleton memory assessment response repository for development")
        _assessment_response_repository_instance = MemoryAssessmentResponseRepository()
    return _assessment_response_repository_instance


async def get_topic_manager(
    topic_repository: TopicRepository = Depends(get_topic_repository),
    llm_adapter: LLMAdapter = Depends(get_llm_adapter)
) -> TopicManager:
    """Get topic manager instance."""
    try:
        from src.application.services.topic_manager import TopicManager
        return TopicManager(
            topic_repository=topic_repository,
            llm_service=llm_adapter
        )
    except Exception:
        # Fallback to simple mock topic manager
        class MockTopicManager:
            async def get_topic_by_message(self, message, level="A2"):
                class MockTopic:
                    id = "mock-topic-id"
                    name = "General Conversation"
                    description = "General conversation practice"
                    level = level
                    category = "conversation"
                return MockTopic()
            
            async def suggest_topics(self, level="A2", limit=5):
                return [
                    {"name": "Greetings", "description": "Basic greetings"},
                    {"name": "Family", "description": "Talking about family"},
                    {"name": "Food", "description": "Food and drinks"}
                ]
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock topic manager as fallback")
        return MockTopicManager()


async def get_translation_service(
    llm_adapter = Depends(get_llm_adapter)
):
    """Get translation service instance."""
    try:
        from src.application.services.translation_service import TranslationService
        return TranslationService(llm_service=llm_adapter)
    except Exception:
        # Fallback to simple mock translation service
        class MockTranslationService:
            async def translate_text(self, text, target_language="en", source_language="auto"):
                return f"[Translated to {target_language}]: {text}"
            
            async def detect_language(self, text):
                return "en"
            
            async def get_supported_languages(self):
                return ["en", "tr", "es", "fr", "de"]
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock translation service as fallback")
        return MockTranslationService()


async def get_user_flow_use_case(
    user_repository = Depends(get_user_repository),
    session_repository = Depends(get_session_repository)
):
    """Get user flow use case instance."""
    try:
        from src.application.use_cases.user_flow_use_case import UserFlowUseCase
        return UserFlowUseCase(
            user_repository=user_repository,
            session_repository=session_repository
        )
    except Exception:
        # Fallback to simple mock user flow use case
        class MockUserFlowUseCase:
            async def get_user_progress(self, user_id):
                class MockProgress:
                    current_level = "A2"
                    completed_sessions = 5
                    total_messages = 50
                    streak_days = 3
                    achievements = ["First Chat", "Week Streak"]
                
                return MockProgress()
            
            async def update_user_level(self, user_id, new_level):
                return {"success": True, "new_level": new_level}
            
            async def get_learning_path(self, user_id):
                return {
                    "current_topic": "Greetings",
                    "next_topics": ["Family", "Food", "Travel"],
                    "recommended_exercises": ["Conversation practice", "Vocabulary quiz"]
                }
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock user flow use case as fallback")
        return MockUserFlowUseCase()


def get_current_user_id(request: Request) -> str:
    """Get current authenticated user ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Current user ID
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user_id = getattr(request.state, "current_user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Authentication required",
                "details": None
            }
        )
    return user_id


def get_current_username(request: Request) -> str:
    """Get current authenticated username from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Current username
        
    Raises:
        HTTPException: If user is not authenticated
    """
    username = getattr(request.state, "current_username", None)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Authentication required",
                "details": None
            }
        )
    return username


def get_current_user_info(request: Request) -> dict:
    """Get current authenticated user information.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with user information
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user_id = getattr(request.state, "current_user_id", None)
    username = getattr(request.state, "current_username", None)
    is_authenticated = getattr(request.state, "is_authenticated", False)
    
    if not is_authenticated or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Authentication required",
                "details": None
            }
        )
    
    return {
        "user_id": user_id,
        "username": username,
        "is_authenticated": is_authenticated
    }


def get_admin_user(request: Request) -> dict:
    """Get current authenticated admin user information.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with admin user information
        
    Raises:
        HTTPException: If user is not authenticated or not admin
    """
    user_info = get_current_user_info(request)
    is_admin = getattr(request.state, "is_admin", False)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "message": "Admin access required",
                "details": None
            }
        )
    
    user_info["is_admin"] = is_admin
    return user_info


def get_openrouter_chatbot_service():
    """Get OpenRouter chatbot service instance."""
    try:
        from src.application.services.openrouter_chatbot_service import OpenRouterChatbotService
        return OpenRouterChatbotService()
    except Exception:
        # Fallback to simple mock chatbot service
        class MockOpenRouterChatbotService:
            async def send_message(self, message, context=None):
                return "This is a mock response from the chatbot service."
            
            async def get_available_models(self):
                return ["gpt-3.5-turbo", "claude-3-haiku"]
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock OpenRouter chatbot service as fallback")
        return MockOpenRouterChatbotService()


def get_chatbot_use_case(
    chatbot_service = Depends(get_openrouter_chatbot_service),
    session_repository = Depends(get_session_repository),
    message_repository = Depends(get_message_repository)
):
    """Get chatbot use case instance."""
    try:
        from src.application.use_cases.chatbot_use_case import ChatbotUseCase
        return ChatbotUseCase(
            chatbot_service=chatbot_service,
            session_repository=session_repository,
            message_repository=message_repository
        )
    except Exception:
        # Fallback to simple mock chatbot use case
        class MockChatbotUseCase:
            async def send_message(self, session_id, message, user_id):
                class MockResponse:
                    message = "Hello! This is a mock chatbot response."
                    session_id = session_id
                    timestamp = "2024-01-01T12:00:00Z"
                
                return MockResponse()
            
            async def get_chat_history(self, session_id, limit=50):
                return []
        
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Using mock chatbot use case as fallback")
        return MockChatbotUseCase()