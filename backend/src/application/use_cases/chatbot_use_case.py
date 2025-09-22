"""Chatbot use case for handling AI conversations."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from src.application.services.openrouter_chatbot_service import OpenRouterChatbotService
from src.domain.repositories.session_repository_interface import SessionRepositoryInterface
from src.domain.repositories.message_repository_interface import MessageRepositoryInterface
from src.domain.entities.session import Session
from src.domain.entities.message import Message
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChatbotRequest:
    """Request for chatbot conversation."""
    user_id: str
    message: str
    session_id: Optional[str] = None
    include_history: bool = True
    max_history_messages: int = 20


@dataclass
class ChatbotResponse:
    """Response from chatbot conversation."""
    response: str
    session_id: str
    message_count: int
    timestamp: str
    model_used: str = "gpt-oss-20b"


class ChatbotUseCaseError(Exception):
    """Chatbot use case specific errors."""
    pass


class ChatbotUseCase:
    """Use case for handling chatbot conversations with session management."""
    
    def __init__(
        self,
        chatbot_service: OpenRouterChatbotService,
        session_repository: SessionRepositoryInterface,
        message_repository: MessageRepositoryInterface
    ):
        """Initialize chatbot use case."""
        self.chatbot_service = chatbot_service
        self.session_repository = session_repository
        self.message_repository = message_repository
    
    async def send_message(self, request: ChatbotRequest) -> ChatbotResponse:
        """Send message to chatbot and manage session."""
        try:
            logger.info(f"Processing chatbot request for user {request.user_id}")
            
            # Get or create session
            session = await self._get_or_create_session(request.user_id, request.session_id)
            
            # Get chat history if requested
            chat_history = []
            if request.include_history:
                chat_history = await self._get_chat_history(
                    session.id, 
                    request.max_history_messages
                )
            
            # Send message to chatbot
            bot_response = await self.chatbot_service.chat_completion(
                user_message=request.message,
                chat_history=chat_history,
                include_system_prompt=True
            )
            
            # Save user message
            user_message = Message(
                session_id=session.id,
                message_type="user",
                content=request.message
            )
            await self.message_repository.create(user_message)
            
            # Save bot response
            bot_message = Message(
                session_id=session.id,
                message_type="assistant", 
                content=bot_response
            )
            await self.message_repository.create(bot_message)
            
            # Update session message count
            session.message_count += 2  # User + bot message
            await self.session_repository.update(session)
            
            # Get total message count
            total_messages = await self.message_repository.count_by_session(session.id)
            
            logger.info(f"Chatbot conversation completed for session {session.id}")
            
            return ChatbotResponse(
                response=bot_response,
                session_id=session.id,
                message_count=total_messages,
                timestamp=datetime.now().isoformat(),
                model_used="gpt-oss-20b"
            )
            
        except Exception as e:
            logger.error(f"Chatbot use case error: {e}")
            raise ChatbotUseCaseError(f"Failed to process chatbot request: {str(e)}")
    
    async def _get_or_create_session(self, user_id: str, session_id: Optional[str]) -> Session:
        """Get existing session or create new one."""
        if session_id:
            # Try to get existing session
            session = await self.session_repository.get_by_id(session_id)
            if session and session.user_id == user_id:
                logger.info(f"Using existing session {session_id}")
                return session
            else:
                logger.warning(f"Session {session_id} not found or access denied")
        
        # Create new session
        session = Session(
            user_id=user_id,
            title="AI Chat Session",
            session_type="conversation",
            status="active",
            source_language="TR",
            target_language="EN"
        )
        
        created_session = await self.session_repository.create(session)
        logger.info(f"Created new session {created_session.id}")
        return created_session
    
    async def _get_chat_history(self, session_id: str, max_messages: int) -> List[Dict[str, str]]:
        """Get chat history for session."""
        messages = await self.message_repository.get_by_session_id(
            session_id, 
            limit=max_messages
        )
        
        chat_history = []
        for message in messages:
            chat_history.append({
                "role": message.message_type,
                "content": message.content
            })
        
        logger.info(f"Retrieved {len(chat_history)} messages for session {session_id}")
        return chat_history
    
    async def get_session_messages(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        # Verify session belongs to user
        session = await self.session_repository.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ChatbotUseCaseError("Session not found or access denied")
        
        messages = await self.message_repository.get_by_session_id(session_id)
        
        result = []
        for message in messages:
            result.append({
                "id": message.id,
                "role": message.message_type,
                "content": message.content,
                "timestamp": message.created_at.isoformat() if message.created_at else None
            })
        
        return result
    
    async def create_new_session(self, user_id: str, title: Optional[str] = None) -> str:
        """Create a new chat session."""
        session = Session(
            user_id=user_id,
            title=title or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            session_type="conversation",
            status="active",
            source_language="TR",
            target_language="EN"
        )
        
        created_session = await self.session_repository.create(session)
        logger.info(f"Created new chat session {created_session.id} for user {user_id}")
        return created_session.id
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session."""
        # Verify session belongs to user
        session = await self.session_repository.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ChatbotUseCaseError("Session not found or access denied")
        
        # Delete all messages first
        await self.message_repository.delete_by_session_id(session_id)
        
        # Delete session
        await self.session_repository.delete(session_id)
        
        logger.info(f"Deleted session {session_id} for user {user_id}")
        return True
    
    async def clear_session(self, session_id: str, user_id: str) -> bool:
        """Clear all messages from a session."""
        # Verify session belongs to user
        session = await self.session_repository.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ChatbotUseCaseError("Session not found or access denied")
        
        # Delete all messages
        await self.message_repository.delete_by_session_id(session_id)
        
        # Reset session message count
        session.message_count = 0
        await self.session_repository.update(session)
        
        logger.info(f"Cleared session {session_id} for user {user_id}")
        return True
    
    async def test_chatbot_connection(self) -> bool:
        """Test chatbot service connection."""
        return await self.chatbot_service.test_connection()