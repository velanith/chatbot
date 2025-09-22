"""Session management use case for session lifecycle operations."""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.domain.entities.session import Session, SessionMode, ProficiencyLevel
from src.domain.entities.user import User
from src.domain.entities.message import Message, MessageRole
from src.domain.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.repositories.session_repository_interface import SessionRepositoryInterface
from src.domain.repositories.message_repository_interface import MessageRepositoryInterface
from src.application.services.memory_manager import MemoryManager


logger = logging.getLogger(__name__)


@dataclass
class SessionCreationRequest:
    """Request data for session creation."""
    user_id: uuid.UUID
    mode: SessionMode
    level: ProficiencyLevel
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SessionInfo:
    """Session information with statistics."""
    session_id: uuid.UUID
    user_id: uuid.UUID
    mode: SessionMode
    level: ProficiencyLevel
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_activity: datetime
    duration_minutes: int
    is_active: bool
    conversation_summary: Optional[str]
    recent_topics: List[str]
    learning_progress: Dict[str, Any]


@dataclass
class SessionListItem:
    """Simplified session info for listing."""
    session_id: uuid.UUID
    mode: SessionMode
    level: ProficiencyLevel
    created_at: datetime
    last_activity: datetime
    message_count: int
    duration_minutes: int
    is_active: bool
    preview_text: Optional[str]


class SessionManagementError(Exception):
    """Exception raised by session management operations."""
    pass


class SessionManagementUseCase:
    """Use case for managing session lifecycle and operations."""
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        session_repository: SessionRepositoryInterface,
        message_repository: MessageRepositoryInterface,
        memory_manager: MemoryManager,
        session_timeout_minutes: int = 60
    ):
        """Initialize session management use case.
        
        Args:
            user_repository: Repository for user data
            session_repository: Repository for session data
            message_repository: Repository for message data
            memory_manager: Service for memory management
            session_timeout_minutes: Minutes after which session is considered inactive
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.message_repository = message_repository
        self.memory_manager = memory_manager
        self.session_timeout_minutes = session_timeout_minutes
        
        # Statistics tracking
        self.total_sessions_created = 0
        self.total_sessions_ended = 0
        self.total_sessions_cleaned = 0
    
    async def create_session(self, request: SessionCreationRequest) -> SessionInfo:
        """Create a new chat session.
        
        Args:
            request: Session creation request
            
        Returns:
            Created session information
            
        Raises:
            SessionManagementError: If session creation fails
        """
        try:
            logger.info(f"Creating new session for user {request.user_id}")
            
            # Verify user exists
            user = await self.user_repository.get_by_id(request.user_id)
            if not user:
                raise SessionManagementError(f"User {request.user_id} not found")
            
            # Create session entity
            session = Session(
                id=uuid.uuid4(),
                user_id=request.user_id,
                mode=request.mode,
                level=request.level,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store session in database
            created_session = await self.session_repository.create(session)
            
            # Initialize memory cache for session
            await self.memory_manager.initialize_session_cache(created_session.id)
            
            self.total_sessions_created += 1
            
            logger.info(f"Successfully created session {created_session.id}")
            
            # Return session info
            return await self._build_session_info(created_session)
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise SessionManagementError(f"Session creation failed: {str(e)}")
    
    async def get_session_info(self, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionInfo:
        """Get detailed session information.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            
        Returns:
            Detailed session information
            
        Raises:
            SessionManagementError: If session not found or access denied
        """
        session = await self._get_authorized_session(session_id, user_id)
        return await self._build_session_info(session)
    
    async def list_user_sessions(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        include_inactive: bool = False
    ) -> List[SessionListItem]:
        """List user's sessions.
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            include_inactive: Whether to include inactive sessions
            
        Returns:
            List of session items
            
        Raises:
            SessionManagementError: If user not found
        """
        try:
            # Verify user exists
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise SessionManagementError(f"User {user_id} not found")
            
            # Get user's sessions
            sessions = await self.session_repository.get_by_user_id(user_id, limit=limit)
            
            session_items = []
            for session in sessions:
                # Check if session is active
                is_active = await self._is_session_active(session)
                
                if not include_inactive and not is_active:
                    continue
                
                # Get message count
                message_count = await self.message_repository.count_by_session(session.id)
                
                # Get preview text from last message
                preview_text = await self._get_session_preview(session.id)
                
                # Calculate duration
                duration_minutes = session.get_age_in_minutes()
                
                session_item = SessionListItem(
                    session_id=session.id,
                    mode=session.mode,
                    level=session.level,
                    created_at=session.created_at,
                    last_activity=session.updated_at,
                    message_count=message_count,
                    duration_minutes=duration_minutes,
                    is_active=is_active,
                    preview_text=preview_text
                )
                
                session_items.append(session_item)
            
            logger.info(f"Retrieved {len(session_items)} sessions for user {user_id}")
            return session_items
            
        except Exception as e:
            logger.error(f"Failed to list user sessions: {e}")
            raise SessionManagementError(f"Failed to list sessions: {str(e)}")
    
    async def _get_authorized_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> Session:
        """Get session with authorization check.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            
        Returns:
            Session object
            
        Raises:
            SessionManagementError: If session not found or access denied
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise SessionManagementError(f"Session {session_id} not found")
        
        if session.user_id != user_id:
            raise SessionManagementError("Access denied to session")
        
        return session
    
    async def _build_session_info(self, session: Session) -> SessionInfo:
        """Build detailed session information.
        
        Args:
            session: Session entity
            
        Returns:
            Detailed session information
        """
        # Get message count
        message_count = await self.message_repository.count_by_session(session.id)
        
        # Get conversation summary
        conversation_summary = await self.memory_manager.get_conversation_summary(session.id)
        
        # Calculate duration
        duration_minutes = session.get_age_in_minutes()
        
        # Check if active
        is_active = await self._is_session_active(session)
        
        # Get recent topics (simplified - could be enhanced)
        recent_topics = await self._extract_recent_topics(session.id)
        
        # Calculate learning progress (simplified)
        learning_progress = await self._calculate_learning_progress(session.id)
        
        return SessionInfo(
            session_id=session.id,
            user_id=session.user_id,
            mode=session.mode,
            level=session.level,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
            last_activity=session.updated_at,
            duration_minutes=duration_minutes,
            is_active=is_active,
            conversation_summary=conversation_summary,
            recent_topics=recent_topics,
            learning_progress=learning_progress
        )
    
    async def _is_session_active(self, session: Session) -> bool:
        """Check if session is considered active.
        
        Args:
            session: Session entity
            
        Returns:
            True if session is active
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.session_timeout_minutes)
        return session.updated_at > cutoff_time
    
    async def _get_session_preview(self, session_id: uuid.UUID) -> Optional[str]:
        """Get preview text from session's last message.
        
        Args:
            session_id: Session ID
            
        Returns:
            Preview text or None
        """
        try:
            recent_messages = await self.memory_manager.get_recent_messages(session_id, limit=1)
            if recent_messages:
                content = recent_messages[0].content
                # Truncate to reasonable preview length
                return content[:100] + "..." if len(content) > 100 else content
            return None
        except Exception:
            return None
    
    async def _extract_recent_topics(self, session_id: uuid.UUID) -> List[str]:
        """Extract recent conversation topics.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of recent topics
        """
        try:
            # Simplified topic extraction - could be enhanced with NLP
            recent_messages = await self.memory_manager.get_recent_messages(session_id, limit=10)
            
            # Basic keyword extraction (could be improved)
            topics = []
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            
            for message in recent_messages:
                if message.role == MessageRole.USER:
                    words = message.content.lower().split()
                    for word in words:
                        word = word.strip('.,!?;:')
                        if len(word) > 3 and word not in common_words:
                            if word not in topics:
                                topics.append(word)
                            if len(topics) >= 5:
                                break
                if len(topics) >= 5:
                    break
            
            return topics[:5]
            
        except Exception:
            return []
    
    async def _calculate_learning_progress(self, session_id: uuid.UUID) -> Dict[str, Any]:
        """Calculate learning progress metrics.
        
        Args:
            session_id: Session ID
            
        Returns:
            Learning progress metrics
        """
        try:
            # Get recent messages with corrections
            recent_messages = await self.memory_manager.get_recent_messages(session_id, limit=20)
            
            total_corrections = 0
            correction_categories = {}
            
            for message in recent_messages:
                if hasattr(message, 'corrections') and message.corrections:
                    total_corrections += len(message.corrections)
                    for correction in message.corrections:
                        category = correction.category.value
                        correction_categories[category] = correction_categories.get(category, 0) + 1
            
            return {
                'total_corrections': total_corrections,
                'correction_categories': correction_categories,
                'messages_analyzed': len(recent_messages),
                'correction_rate': round(total_corrections / len(recent_messages), 2) if recent_messages else 0
            }
            
        except Exception:
            return {
                'total_corrections': 0,
                'correction_categories': {},
                'messages_analyzed': 0,
                'correction_rate': 0
            }
    
    def get_use_case_stats(self) -> Dict[str, Any]:
        """Get use case performance statistics.
        
        Returns:
            Dictionary with use case statistics
        """
        return {
            'total_sessions_created': self.total_sessions_created,
            'total_sessions_ended': self.total_sessions_ended,
            'total_sessions_cleaned': self.total_sessions_cleaned,
            'session_timeout_minutes': self.session_timeout_minutes
        }