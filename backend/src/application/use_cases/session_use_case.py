"""Session management use case for session lifecycle operations."""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.domain.entities.session import Session, SessionMode, ProficiencyLevel
from src.domain.entities.user import User
from src.domain.entities.message import Message
from src.domain.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.repositories.session_repository_interface import SessionRepositoryInterface
from src.domain.repositories.message_repository_interface import MessageRepositoryInterface
from src.application.services.memory_manager import MemoryManager


logger = logging.getLogger(__name__)


@dataclass
class SessionRequest:
    """Request data for session creation."""
    user_id: uuid.UUID
    mode: SessionMode
    level: ProficiencyLevel
    summary: Optional[str] = None


@dataclass
class SessionResponse:
    """Response data from session operations."""
    session_id: uuid.UUID
    user_id: uuid.UUID
    mode: SessionMode
    level: ProficiencyLevel
    created_at: datetime
    updated_at: datetime
    summary: Optional[str]
    message_count: int
    is_active: bool
    metadata: Dict[str, Any]


@dataclass
class SessionListResponse:
    """Response data for session listing."""
    sessions: List[SessionResponse]
    total_count: int
    active_count: int
    metadata: Dict[str, Any]


class SessionUseCaseError(Exception):
    """Exception raised by session use case operations."""
    pass


class SessionUseCase:
    """Use case for managing chat session lifecycle."""
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        session_repository: SessionRepositoryInterface,
        message_repository: MessageRepositoryInterface,
        memory_manager: MemoryManager,
        session_timeout_hours: int = 24
    ):
        """Initialize session use case.
        
        Args:
            user_repository: Repository for user data
            session_repository: Repository for session data
            message_repository: Repository for message data
            memory_manager: Service for memory management
            session_timeout_hours: Hours after which inactive sessions are considered expired
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.message_repository = message_repository
        self.memory_manager = memory_manager
        self.session_timeout_hours = session_timeout_hours
        
        # Statistics tracking
        self.total_sessions_created = 0
        self.total_sessions_ended = 0
        self.total_sessions_cleaned = 0
    
    async def create_session(self, request: SessionRequest) -> SessionResponse:
        """Create a new chat session.
        
        Args:
            request: Session creation request
            
        Returns:
            Created session response
            
        Raises:
            SessionUseCaseError: If session creation fails
        """
        try:
            logger.info(f"Creating new session for user {request.user_id}")
            
            # Verify user exists
            user = await self.user_repository.get_by_id(request.user_id)
            if not user:
                raise SessionUseCaseError(f"User {request.user_id} not found")
            
            # Create session entity
            session = Session(
                id=uuid.uuid4(),
                user_id=request.user_id,
                mode=request.mode,
                level=request.level,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                summary=request.summary
            )
            
            # Store session in database
            created_session = await self.session_repository.create(session)
            
            # Initialize memory cache for session
            await self.memory_manager.initialize_session_cache(created_session.id)
            
            self.total_sessions_created += 1
            
            # Create response
            response = SessionResponse(
                session_id=created_session.id,
                user_id=created_session.user_id,
                mode=created_session.mode,
                level=created_session.level,
                created_at=created_session.created_at,
                updated_at=created_session.updated_at,
                summary=created_session.summary,
                message_count=0,
                is_active=True,
                metadata={
                    'creation_timestamp': datetime.utcnow().isoformat(),
                    'cache_initialized': True
                }
            )
            
            logger.info(f"Successfully created session {created_session.id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise SessionUseCaseError(f"Session creation failed: {str(e)}")
    
    async def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionResponse:
        """Get session information.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            
        Returns:
            Session response
            
        Raises:
            SessionUseCaseError: If session not found or access denied
        """
        try:
            # Get session from database
            session = await self.session_repository.get_by_id(session_id)
            if not session:
                raise SessionUseCaseError("Session not found")
            
            # Check authorization
            if session.user_id != user_id:
                raise SessionUseCaseError("Access denied to session")
            
            # Get message count
            message_count = await self.message_repository.count_by_session(session_id)
            
            # Check if session is active (not expired)
            is_active = self._is_session_active(session)
            
            # Get memory cache status
            cache_status = await self.memory_manager.get_session_cache_status(session_id)
            
            response = SessionResponse(
                session_id=session.id,
                user_id=session.user_id,
                mode=session.mode,
                level=session.level,
                created_at=session.created_at,
                updated_at=session.updated_at,
                summary=session.summary,
                message_count=message_count,
                is_active=is_active,
                metadata={
                    'age_hours': session.get_age_in_hours(),
                    'cache_status': cache_status,
                    'last_activity': session.updated_at.isoformat()
                }
            )
            
            return response
            
        except SessionUseCaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise SessionUseCaseError(f"Failed to retrieve session: {str(e)}")
    
    async def list_user_sessions(
        self,
        user_id: uuid.UUID,
        include_inactive: bool = False,
        limit: int = 50
    ) -> SessionListResponse:
        """List sessions for a user.
        
        Args:
            user_id: User ID
            include_inactive: Whether to include inactive/expired sessions
            limit: Maximum number of sessions to return
            
        Returns:
            Session list response
            
        Raises:
            SessionUseCaseError: If listing fails
        """
        try:
            logger.info(f"Listing sessions for user {user_id}")
            
            # Verify user exists
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise SessionUseCaseError(f"User {user_id} not found")
            
            # Get sessions from database
            sessions = await self.session_repository.get_by_user_id(user_id, limit=limit)
            
            # Convert to response format
            session_responses = []
            active_count = 0
            
            for session in sessions:
                message_count = await self.message_repository.count_by_session(session.id)
                is_active = self._is_session_active(session)
                
                if is_active:
                    active_count += 1
                
                # Skip inactive sessions if not requested
                if not include_inactive and not is_active:
                    continue
                
                cache_status = await self.memory_manager.get_session_cache_status(session.id)
                
                session_response = SessionResponse(
                    session_id=session.id,
                    user_id=session.user_id,
                    mode=session.mode,
                    level=session.level,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    summary=session.summary,
                    message_count=message_count,
                    is_active=is_active,
                    metadata={
                        'age_hours': session.get_age_in_hours(),
                        'cache_status': cache_status
                    }
                )
                
                session_responses.append(session_response)
            
            response = SessionListResponse(
                sessions=session_responses,
                total_count=len(sessions),
                active_count=active_count,
                metadata={
                    'user_id': str(user_id),
                    'include_inactive': include_inactive,
                    'limit': limit,
                    'query_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Found {len(session_responses)} sessions for user {user_id}")
            return response
            
        except SessionUseCaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to list sessions for user {user_id}: {e}")
            raise SessionUseCaseError(f"Failed to list sessions: {str(e)}")
    
    async def update_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        mode: Optional[SessionMode] = None,
        level: Optional[ProficiencyLevel] = None,
        summary: Optional[str] = None
    ) -> SessionResponse:
        """Update session settings.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            mode: New session mode (optional)
            level: New proficiency level (optional)
            summary: New session summary (optional)
            
        Returns:
            Updated session response
            
        Raises:
            SessionUseCaseError: If update fails
        """
        try:
            # Get and verify session
            session = await self.session_repository.get_by_id(session_id)
            if not session:
                raise SessionUseCaseError("Session not found")
            
            if session.user_id != user_id:
                raise SessionUseCaseError("Access denied to session")
            
            # Update fields if provided
            updated = False
            if mode is not None and mode != session.mode:
                session.mode = mode
                updated = True
            
            if level is not None and level != session.level:
                session.level = level
                updated = True
            
            if summary is not None and summary != session.summary:
                session.summary = summary
                updated = True
            
            if updated:
                session.updated_at = datetime.utcnow()
                await self.session_repository.update(session)
                logger.info(f"Updated session {session_id}")
            
            # Return updated session info
            return await self.get_session(session_id, user_id)
            
        except SessionUseCaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise SessionUseCaseError(f"Failed to update session: {str(e)}")
    
    async def end_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        """End a chat session and clean up resources.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            
        Returns:
            Session end summary
            
        Raises:
            SessionUseCaseError: If session ending fails
        """
        try:
            logger.info(f"Ending session {session_id}")
            
            # Get and verify session
            session = await self.session_repository.get_by_id(session_id)
            if not session:
                raise SessionUseCaseError("Session not found")
            
            if session.user_id != user_id:
                raise SessionUseCaseError("Access denied to session")
            
            # Get session statistics before cleanup
            message_count = await self.message_repository.count_by_session(session_id)
            session_duration = datetime.utcnow() - session.created_at
            
            # Flush memory cache to database
            flushed_messages = await self.memory_manager.flush_session_to_database(session_id)
            
            # Clear memory cache
            await self.memory_manager.clear_session_cache(session_id)
            
            # Update session end time (if we add this field in future)
            session.updated_at = datetime.utcnow()
            await self.session_repository.update(session)
            
            self.total_sessions_ended += 1
            
            summary = {
                'session_id': str(session_id),
                'duration_minutes': int(session_duration.total_seconds() / 60),
                'total_messages': message_count,
                'messages_flushed_from_cache': flushed_messages,
                'ended_at': datetime.utcnow().isoformat(),
                'session_mode': session.mode.value,
                'proficiency_level': session.level.value
            }
            
            logger.info(f"Successfully ended session {session_id}: {message_count} messages, {session_duration}")
            return summary
            
        except SessionUseCaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            raise SessionUseCaseError(f"Failed to end session: {str(e)}")
    
    async def cleanup_inactive_sessions(self, dry_run: bool = False) -> Dict[str, Any]:
        """Clean up inactive/expired sessions.
        
        Args:
            dry_run: If True, only report what would be cleaned without actually doing it
            
        Returns:
            Cleanup summary
        """
        try:
            logger.info(f"Starting session cleanup (dry_run={dry_run})")
            
            # Get all sessions
            all_sessions = await self.session_repository.get_all()
            
            inactive_sessions = []
            cleanup_stats = {
                'total_sessions_checked': len(all_sessions),
                'inactive_sessions_found': 0,
                'sessions_cleaned': 0,
                'cache_entries_cleared': 0,
                'messages_flushed': 0,
                'dry_run': dry_run,
                'cleanup_timestamp': datetime.utcnow().isoformat()
            }
            
            # Find inactive sessions
            for session in all_sessions:
                if not self._is_session_active(session):
                    inactive_sessions.append(session)
            
            cleanup_stats['inactive_sessions_found'] = len(inactive_sessions)
            
            if not dry_run:
                # Clean up inactive sessions
                for session in inactive_sessions:
                    try:
                        # Flush cache to database
                        flushed = await self.memory_manager.flush_session_to_database(session.id)
                        cleanup_stats['messages_flushed'] += flushed
                        
                        # Clear cache
                        await self.memory_manager.clear_session_cache(session.id)
                        cleanup_stats['cache_entries_cleared'] += 1
                        
                        cleanup_stats['sessions_cleaned'] += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to cleanup session {session.id}: {e}")
                
                self.total_sessions_cleaned += cleanup_stats['sessions_cleaned']
            
            logger.info(f"Session cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            raise SessionUseCaseError(f"Session cleanup failed: {str(e)}")
    
    def _is_session_active(self, session: Session) -> bool:
        """Check if a session is still active (not expired).
        
        Args:
            session: Session to check
            
        Returns:
            True if session is active
        """
        age_hours = session.get_age_in_hours()
        return age_hours < self.session_timeout_hours
    
    async def get_session_statistics(self, user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Get session statistics.
        
        Args:
            user_id: Optional user ID to filter statistics
            
        Returns:
            Statistics dictionary
        """
        try:
            if user_id:
                # User-specific statistics
                sessions = await self.session_repository.get_by_user_id(user_id)
                active_sessions = [s for s in sessions if self._is_session_active(s)]
                
                total_messages = 0
                for session in sessions:
                    count = await self.message_repository.count_by_session(session.id)
                    total_messages += count
                
                return {
                    'user_id': str(user_id),
                    'total_sessions': len(sessions),
                    'active_sessions': len(active_sessions),
                    'total_messages': total_messages,
                    'average_messages_per_session': total_messages / len(sessions) if sessions else 0
                }
            else:
                # Global statistics
                all_sessions = await self.session_repository.get_all()
                active_sessions = [s for s in all_sessions if self._is_session_active(s)]
                
                return {
                    'total_sessions_created': self.total_sessions_created,
                    'total_sessions_ended': self.total_sessions_ended,
                    'total_sessions_cleaned': self.total_sessions_cleaned,
                    'current_total_sessions': len(all_sessions),
                    'current_active_sessions': len(active_sessions),
                    'session_timeout_hours': self.session_timeout_hours
                }
                
        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            raise SessionUseCaseError(f"Failed to get statistics: {str(e)}")

    async def get_session_history(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get paginated session history.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            page: Page number (1-based)
            page_size: Number of messages per page
            
        Returns:
            Paginated history response
            
        Raises:
            SessionUseCaseError: If history retrieval fails
        """
        try:
            # Get and verify session
            session = await self.session_repository.get_by_id(session_id)
            if not session:
                raise SessionUseCaseError("Session not found")
            
            if session.user_id != user_id:
                raise SessionUseCaseError("Access denied to session")
            
            # Get total message count
            total_messages = await self.message_repository.count_by_session(session_id)
            
            # Calculate pagination
            total_pages = (total_messages + page_size - 1) // page_size
            offset = (page - 1) * page_size
            
            # Get messages for this page
            messages = await self.message_repository.get_by_session_paginated(
                session_id, offset=offset, limit=page_size
            )
            
            # Convert messages to response format
            message_items = []
            for message in messages:
                message_item = {
                    "message_id": message.id,
                    "role": message.role.value,
                    "content": message.content,
                    "timestamp": message.created_at,
                    "corrections": message.corrections or [],
                    "metadata": message.metadata or {}
                }
                message_items.append(message_item)
            
            # Get session info
            session_info = await self.get_session(session_id, user_id)
            
            return {
                "session_id": session_id,
                "messages": message_items,
                "total_messages": total_messages,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "session_info": session_info
            }
            
        except SessionUseCaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to get session history {session_id}: {e}")
            raise SessionUseCaseError(f"Failed to retrieve session history: {str(e)}")
    
    async def list_user_sessions_paginated(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        mode_filter: Optional[SessionMode] = None,
        level_filter: Optional[ProficiencyLevel] = None,
        active_only: bool = False
    ) -> Dict[str, Any]:
        """List user sessions with pagination and filtering.
        
        Args:
            user_id: User ID
            page: Page number (1-based)
            page_size: Number of sessions per page
            mode_filter: Filter by session mode
            level_filter: Filter by proficiency level
            active_only: Show only active sessions
            
        Returns:
            Paginated session list response
            
        Raises:
            SessionUseCaseError: If listing fails
        """
        try:
            # Verify user exists
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise SessionUseCaseError(f"User {user_id} not found")
            
            # Get all user sessions
            all_sessions = await self.session_repository.get_by_user_id(user_id)
            
            # Apply filters
            filtered_sessions = []
            active_count = 0
            
            for session in all_sessions:
                is_active = self._is_session_active(session)
                if is_active:
                    active_count += 1
                
                # Apply filters
                if active_only and not is_active:
                    continue
                
                if mode_filter and session.mode != mode_filter:
                    continue
                
                if level_filter and session.level != level_filter:
                    continue
                
                filtered_sessions.append(session)
            
            # Sort by last activity (most recent first)
            filtered_sessions.sort(key=lambda s: s.updated_at, reverse=True)
            
            # Apply pagination
            total_count = len(filtered_sessions)
            total_pages = (total_count + page_size - 1) // page_size
            offset = (page - 1) * page_size
            page_sessions = filtered_sessions[offset:offset + page_size]
            
            # Convert to response format
            session_items = []
            for session in page_sessions:
                message_count = await self.message_repository.count_by_session(session.id)
                is_active = self._is_session_active(session)
                
                # Get preview of last message
                last_messages = await self.message_repository.get_by_session_paginated(
                    session.id, offset=0, limit=1
                )
                preview_text = None
                if last_messages:
                    preview_text = last_messages[0].content[:100] + "..." if len(last_messages[0].content) > 100 else last_messages[0].content
                
                duration_minutes = int((session.updated_at - session.created_at).total_seconds() / 60)
                
                session_item = {
                    "session_id": session.id,
                    "mode": session.mode,
                    "level": session.level,
                    "created_at": session.created_at,
                    "last_activity": session.updated_at,
                    "message_count": message_count,
                    "duration_minutes": duration_minutes,
                    "is_active": is_active,
                    "preview_text": preview_text
                }
                session_items.append(session_item)
            
            return {
                "sessions": session_items,
                "total_count": total_count,
                "active_count": active_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
            
        except SessionUseCaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to list sessions for user {user_id}: {e}")
            raise SessionUseCaseError(f"Failed to list sessions: {str(e)}")
    
    async def export_conversation(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export conversation data.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            format: Export format (json, csv, txt)
            
        Returns:
            Export response with data
            
        Raises:
            SessionUseCaseError: If export fails
        """
        try:
            # Get and verify session
            session = await self.session_repository.get_by_id(session_id)
            if not session:
                raise SessionUseCaseError("Session not found")
            
            if session.user_id != user_id:
                raise SessionUseCaseError("Access denied to session")
            
            # Get all messages
            messages = await self.message_repository.get_by_session(session_id)
            
            # Generate export data based on format
            if format == "json":
                export_data = self._export_as_json(session, messages)
            elif format == "csv":
                export_data = self._export_as_csv(session, messages)
            elif format == "txt":
                export_data = self._export_as_txt(session, messages)
            else:
                raise SessionUseCaseError(f"Unsupported export format: {format}")
            
            # Calculate metadata
            total_messages = len(messages)
            export_size = len(export_data.encode('utf-8'))
            duration_minutes = int((session.updated_at - session.created_at).total_seconds() / 60)
            
            return {
                "session_id": session_id,
                "format": format,
                "data": export_data,
                "metadata": {
                    "total_messages": total_messages,
                    "export_size_bytes": export_size,
                    "session_duration_minutes": duration_minutes,
                    "mode": session.mode.value,
                    "level": session.level.value,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat()
                },
                "generated_at": datetime.utcnow()
            }
            
        except SessionUseCaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to export conversation {session_id}: {e}")
            raise SessionUseCaseError(f"Failed to export conversation: {str(e)}")
    
    def _export_as_json(self, session: Session, messages: List[Message]) -> str:
        """Export conversation as JSON."""
        import json
        
        data = {
            "session_id": str(session.id),
            "user_id": str(session.user_id),
            "mode": session.mode.value,
            "level": session.level.value,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "summary": session.summary,
            "messages": []
        }
        
        for message in messages:
            message_data = {
                "id": str(message.id),
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "corrections": message.corrections or [],
                "metadata": message.metadata or {}
            }
            data["messages"].append(message_data)
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _export_as_csv(self, session: Session, messages: List[Message]) -> str:
        """Export conversation as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Session ID", "Message ID", "Role", "Content", "Timestamp", 
            "Corrections Count", "Has Metadata"
        ])
        
        # Write messages
        for message in messages:
            corrections_count = len(message.corrections) if message.corrections else 0
            has_metadata = bool(message.metadata)
            
            writer.writerow([
                str(session.id),
                str(message.id),
                message.role.value,
                message.content,
                message.created_at.isoformat(),
                corrections_count,
                has_metadata
            ])
        
        return output.getvalue()
    
    def _export_as_txt(self, session: Session, messages: List[Message]) -> str:
        """Export conversation as plain text."""
        lines = []
        lines.append(f"Conversation Export")
        lines.append(f"Session ID: {session.id}")
        lines.append(f"Mode: {session.mode.value}")
        lines.append(f"Level: {session.level.value}")
        lines.append(f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Updated: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("=" * 50)
        lines.append("")
        
        for message in messages:
            timestamp = message.created_at.strftime('%H:%M:%S')
            role = "User" if message.role.value == "user" else "Assistant"
            lines.append(f"[{timestamp}] {role}: {message.content}")
            
            if message.corrections:
                lines.append(f"  Corrections: {len(message.corrections)} found")
            
            lines.append("")
        
        return "\n".join(lines)