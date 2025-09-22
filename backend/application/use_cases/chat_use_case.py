"""Chat use case for conversation flow orchestration."""

import logging
import uuid
from typing import List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from src.domain.entities.message import Message, MessageRole, Correction, CorrectionCategory
from src.domain.entities.session import Session, SessionMode, ProficiencyLevel
from src.domain.entities.conversation_context import ConversationContext, UserPreferences
from src.domain.entities.user import User
from src.domain.entities.structured_feedback import StructuredFeedback
from src.domain.entities.topic import Topic
from src.domain.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.repositories.session_repository_interface import SessionRepositoryInterface
from src.domain.repositories.message_repository_interface import MessageRepositoryInterface
from src.domain.repositories.topic_repository_interface import TopicRepositoryInterface
from src.application.services.memory_manager import MemoryManager
from src.application.services.llm_adapter import LLMAdapter
from src.application.services.pedagogy_engine import PedagogyEngine, PedagogicalResponse
from src.application.services.topic_manager import TopicManager
from src.application.services.translation_service import TranslationService


logger = logging.getLogger(__name__)


@dataclass
class ChatRequest:
    """Request data for chat interaction."""
    user_id: uuid.UUID
    message_content: str
    session_id: Optional[uuid.UUID] = None
    session_mode: Optional[SessionMode] = None
    proficiency_level: Optional[ProficiencyLevel] = None


@dataclass
class ChatResponse:
    """Response data from chat interaction."""
    session_id: uuid.UUID
    ai_response: str
    corrections: List[Correction]
    translation: Optional[str]
    micro_exercise: Optional[str]
    message_id: uuid.UUID
    session_mode: SessionMode
    proficiency_level: ProficiencyLevel
    metadata: dict
    # New fields for enhanced features
    structured_feedback: Optional[StructuredFeedback] = None
    current_topic: Optional[Topic] = None
    topic_transition_suggestion: Optional[str] = None


class ChatUseCaseError(Exception):
    """Exception raised by chat use case operations."""
    pass


class ChatUseCase:
    """Use case for handling chat conversations with language learning features."""
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        session_repository: SessionRepositoryInterface,
        message_repository: MessageRepositoryInterface,
        memory_manager: MemoryManager,
        llm_adapter: LLMAdapter,
        pedagogy_engine: PedagogyEngine,
        topic_repository: Optional[TopicRepositoryInterface] = None,
        topic_manager: Optional[TopicManager] = None,
        translation_service: Optional[TranslationService] = None
    ):
        """Initialize chat use case.
        
        Args:
            user_repository: Repository for user data
            session_repository: Repository for session data
            message_repository: Repository for message data
            topic_repository: Repository for topic data
            memory_manager: Service for memory management
            llm_adapter: Adapter for LLM service interactions
            pedagogy_engine: Engine for pedagogical optimization
            topic_manager: Service for topic management
            translation_service: Service for translation
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.message_repository = message_repository
        self.topic_repository = topic_repository
        self.memory_manager = memory_manager
        self.llm_adapter = llm_adapter
        self.pedagogy_engine = pedagogy_engine
        self.topic_manager = topic_manager
        self.translation_service = translation_service
        
        # Statistics tracking
        self.total_conversations = 0
        self.total_messages_processed = 0
        self.total_corrections_made = 0
        self.total_exercises_generated = 0
        self.total_structured_feedback_provided = 0
    
    async def handle_chat_message(self, request: ChatRequest) -> ChatResponse:
        """Handle a chat message and generate AI response with enhanced features.
        
        Args:
            request: Chat request with user message and context
            
        Returns:
            Chat response with AI reply and learning features
            
        Raises:
            ChatUseCaseError: If chat processing fails
        """
        try:
            logger.info(f"Processing chat message for user {request.user_id}")
            self.total_messages_processed += 1
            
            # Get or create session
            logger.info("Step 1: Getting or creating session")
            session = await self._get_or_create_session(request)
            logger.info(f"Session created/retrieved: {session.id}")
            
            # Get user preferences with level assessment integration
            logger.info("Step 2: Getting user preferences")
            user_preferences = await self._get_enhanced_user_preferences(request.user_id)
            logger.info(f"User preferences retrieved: {user_preferences.proficiency_level}")
            
            # Get current topic and manage topic flow
            logger.info("Step 3: Managing topic flow")
            current_topic, topic_transition = await self._manage_topic_flow(
                session, request.message_content, user_preferences
            )
            logger.info(f"Current topic: {current_topic.name if current_topic else 'None'}")
            
            # Build enhanced conversation context
            logger.info("Step 4: Building conversation context")
            conversation_context = await self._build_enhanced_conversation_context(
                session, user_preferences, current_topic
            )
            logger.info("Conversation context built")
            
            # Store user message
            logger.info("Step 5: Storing user message")
            user_message = await self._store_user_message(
                session.id, request.message_content
            )
            logger.info(f"User message stored: {user_message.id}")
            
            # Enhanced native language detection and translation
            logger.info("Step 6: Processing language detection and translation")
            user_language = await self._enhanced_language_detection(
                request.message_content, user_preferences
            )
            translation = None
            if user_language == 'native':
                translation = await self._enhanced_translation(
                    request.message_content, 
                    user_preferences.native_language,
                    user_preferences.target_language,
                    current_topic
                )
            
            # Generate AI response with topic awareness
            logger.info("Step 7: Generating AI response")
            ai_response = await self._generate_topic_aware_response(
                conversation_context, request.message_content, current_topic
            )
            
            # Extract corrections from user message and AI response
            logger.info(f"AI Response for correction analysis: {ai_response}")
            raw_corrections = self._extract_corrections_from_response(
                request.message_content, ai_response
            )
            logger.info(f"AI response generated with {len(raw_corrections)} corrections")
            
            # Get session message count for feedback cycle
            session_message_count = await self._get_session_message_count(session.id)
            
            # Check for 3-message structured feedback cycle
            logger.info("Step 8: Checking for structured feedback cycle")
            structured_feedback = await self._check_and_generate_structured_feedback(
                session, user_preferences, session_message_count, current_topic
            )
            
            # Apply enhanced pedagogical optimization
            logger.info("Step 9: Applying enhanced pedagogical optimization")
            pedagogical_response = await self._apply_enhanced_pedagogy(
                ai_response, raw_corrections, conversation_context, 
                session_message_count, structured_feedback
            )
            logger.info("Enhanced pedagogical optimization applied")
            
            # Store AI message with corrections
            ai_message = await self._store_ai_message(
                session.id,
                pedagogical_response.formatted_response,
                pedagogical_response.selected_corrections
            )
            
            # Update session with topic and feedback tracking
            await self._update_enhanced_session_state(
                session.id, current_topic, structured_feedback is not None, session_message_count
            )
            
            # Update memory cache
            await self._update_memory_cache(session.id, user_message, ai_message)
            
            # Track enhanced statistics
            self.total_corrections_made += len(pedagogical_response.selected_corrections)
            if pedagogical_response.micro_exercise:
                self.total_exercises_generated += 1
            if structured_feedback:
                self.total_structured_feedback_provided += 1
            
            # Create enhanced response
            response = ChatResponse(
                session_id=session.id,
                ai_response=pedagogical_response.formatted_response,
                corrections=pedagogical_response.selected_corrections,
                translation=translation,
                micro_exercise=pedagogical_response.micro_exercise,
                message_id=ai_message.id,
                session_mode=session.mode,
                proficiency_level=user_preferences.proficiency_level,
                structured_feedback=structured_feedback,
                current_topic=current_topic,
                topic_transition_suggestion=topic_transition,
                metadata={
                    'user_message_id': str(user_message.id),
                    'processing_time': datetime.utcnow().isoformat(),
                    'pedagogical_metadata': pedagogical_response.response_metadata,
                    'session_message_count': session_message_count,
                    'user_language_detected': user_language,
                    'topic_coherence_checked': current_topic is not None,
                    'structured_feedback_provided': structured_feedback is not None
                }
            )
            
            logger.info(f"Successfully processed enhanced chat message: {len(pedagogical_response.selected_corrections)} corrections, exercise: {pedagogical_response.micro_exercise is not None}, structured feedback: {structured_feedback is not None}")
            return response
            
        except Exception as e:
            import traceback
            import sys
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(f"Failed to process chat message: {e}")
            logger.error(f"Exception type: {exc_type}")
            logger.error(f"Exception value: {exc_value}")
            logger.error(f"Full traceback:")
            for line in traceback.format_tb(exc_traceback):
                logger.error(line.strip())
            raise ChatUseCaseError(f"Chat processing failed: {str(e)}")
    
    async def _get_or_create_session(self, request: ChatRequest) -> Session:
        """Get existing session or create new one with level assessment integration.
        
        Args:
            request: Chat request
            
        Returns:
            Session object
        """
        if request.session_id:
            # Try to get existing session
            session = await self.session_repository.get_by_id(request.session_id)
            if session and session.user_id == request.user_id:
                return session
            else:
                logger.warning(f"Session {request.session_id} not found or access denied")
        
        # Get user to check for assessed level
        user = await self.user_repository.get_by_id(request.user_id)
        if not user:
            raise ChatUseCaseError(f"User {request.user_id} not found")
        
        # Create new session with level assessment integration
        session_mode = request.session_mode or SessionMode.TUTOR
        
        # Use assessed level if available, otherwise use provided or default level
        proficiency_level = request.proficiency_level
        if hasattr(user, 'assessed_level') and user.assessed_level:
            # Convert string level to enum
            level_mapping = {
                'A1': ProficiencyLevel.A1,
                'A2': ProficiencyLevel.A2,
                'B1': ProficiencyLevel.B1,
                'B2': ProficiencyLevel.B2,
                'C1': ProficiencyLevel.C1,
                'C2': ProficiencyLevel.C2
            }
            proficiency_level = level_mapping.get(user.assessed_level, ProficiencyLevel.A2)
            logger.info(f"Using assessed level {user.assessed_level} for new session")
        elif not proficiency_level:
            # Fallback to user's proficiency level or default
            user_level = getattr(user, 'proficiency_level', 'A2')
            level_mapping = {
                'beginner': ProficiencyLevel.A1,
                'intermediate': ProficiencyLevel.A2,
                'advanced': ProficiencyLevel.B1,
                'A1': ProficiencyLevel.A1,
                'A2': ProficiencyLevel.A2,
                'B1': ProficiencyLevel.B1,
                'B2': ProficiencyLevel.B2,
                'C1': ProficiencyLevel.C1,
                'C2': ProficiencyLevel.C2
            }
            proficiency_level = level_mapping.get(user_level, ProficiencyLevel.A2)
        
        session = Session(
            id=uuid.uuid4(),
            user_id=request.user_id,
            mode=session_mode,
            level=proficiency_level,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            # Initialize new fields for enhanced features
            current_topic=None,
            topic_history=[],
            feedback_count=0,
            last_feedback_message=None
        )
        
        created_session = await self.session_repository.create(session)
        self.total_conversations += 1
        
        logger.info(f"Created new session {created_session.id} for user {request.user_id} with level {proficiency_level}")
        return created_session
    
    async def _get_user_preferences(self, user_id: uuid.UUID) -> UserPreferences:
        """Get user language preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences
            
        Raises:
            ChatUseCaseError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ChatUseCaseError(f"User {user_id} not found")
        
        # Get proficiency level and convert to enum if it's a string
        proficiency_level = getattr(user, 'proficiency_level', 'A2')
        if isinstance(proficiency_level, str):
            # Map string values to enum
            level_mapping = {
                'beginner': ProficiencyLevel.A1,
                'intermediate': ProficiencyLevel.A2,
                'advanced': ProficiencyLevel.B1,
                'A1': ProficiencyLevel.A1,
                'A2': ProficiencyLevel.A2,
                'B1': ProficiencyLevel.B1,
                'B2': ProficiencyLevel.B2,
                'C1': ProficiencyLevel.C1,
                'C2': ProficiencyLevel.C2
            }
            proficiency_level = level_mapping.get(proficiency_level, ProficiencyLevel.A2)
        
        return UserPreferences(
            native_language=getattr(user, 'native_language', 'tr'),
            target_language=getattr(user, 'target_language', 'en'),
            proficiency_level=proficiency_level
        )
    
    async def _build_conversation_context(
        self,
        session: Session,
        user_preferences: UserPreferences
    ) -> ConversationContext:
        """Build conversation context for AI generation.
        
        Args:
            session: Current session
            user_preferences: User preferences
            
        Returns:
            Conversation context
        """
        # Get recent messages from memory cache
        recent_messages = await self.memory_manager.get_recent_messages(
            session.id, count=10
        )
        
        # Get conversation summary if available
        summary = await self.memory_manager.get_conversation_summary(session.id)
        
        return ConversationContext(
            recent_messages=recent_messages,
            summary=summary,
            user_preferences=user_preferences,
            session_mode=session.mode
        )
    
    async def _store_user_message(
        self,
        session_id: uuid.UUID,
        content: str
    ) -> Message:
        """Store user message in database.
        
        Args:
            session_id: Session ID
            content: Message content
            
        Returns:
            Stored message
        """
        message = Message(
            id=uuid.uuid4(),
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            created_at=datetime.utcnow()
        )
        
        return await self.message_repository.create(message)
    
    async def _store_ai_message(
        self,
        session_id: uuid.UUID,
        content: str,
        corrections: List[Correction]
    ) -> Message:
        """Store AI message with corrections in database.
        
        Args:
            session_id: Session ID
            content: Message content
            corrections: List of corrections
            
        Returns:
            Stored message
        """
        message = Message(
            id=uuid.uuid4(),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            corrections=corrections,
            created_at=datetime.utcnow()
        )
        
        return await self.message_repository.create(message)
    
    async def _update_memory_cache(
        self,
        session_id: uuid.UUID,
        user_message: Message,
        ai_message: Message
    ):
        """Update memory cache with new messages.
        
        Args:
            session_id: Session ID
            user_message: User message
            ai_message: AI message
        """
        try:
            await self.memory_manager.add_message(user_message)
            await self.memory_manager.add_message(ai_message)
        except Exception as e:
            logger.warning(f"Failed to update memory cache: {e}")
            # Non-critical error, continue processing
    
    async def _update_session_activity(self, session_id: uuid.UUID):
        """Update session last activity timestamp.
        
        Args:
            session_id: Session ID
        """
        try:
            await self.session_repository.update_activity(session_id, datetime.utcnow())
        except Exception as e:
            logger.warning(f"Failed to update session activity: {e}")
            # Non-critical error, continue processing
    
    async def _get_session_message_count(self, session_id: uuid.UUID) -> int:
        """Get total message count for session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Message count
        """
        try:
            return await self.message_repository.count_by_session(session_id)
        except Exception as e:
            logger.warning(f"Failed to get message count: {e}")
            return 0
    
    async def _get_last_exercise_message(self, session_id: uuid.UUID) -> Optional[int]:
        """Get message number of last micro-exercise.
        
        Args:
            session_id: Session ID
            
        Returns:
            Message number of last exercise or None
        """
        try:
            # This would need to be implemented in message repository
            # For now, return None (will generate exercises based on frequency)
            return None
        except Exception as e:
            logger.warning(f"Failed to get last exercise message: {e}")
            return None
    
    def _extract_corrections_from_response(self, user_message: str, ai_response: str) -> List[Correction]:
        """Extract corrections from AI response text.
        
        Args:
            user_message: Original user message
            ai_response: AI response containing corrections
            
        Returns:
            List of extracted corrections
        """
        corrections = []
        try:
            # Pattern 1: **Original:** **Corrected:** **Explanation:** format
            if "**Original:**" in ai_response and "**Corrected:**" in ai_response:
                lines = ai_response.split('\n')
                original_line = None
                corrected_line = None
                explanation = "Grammar correction"
                
                for i, line in enumerate(lines):
                    if "**Original:**" in line:
                        original_line = line.replace("**Original:**", "").strip().strip('"').strip("'")
                    elif "**Corrected:**" in line:
                        corrected_line = line.replace("**Corrected:**", "").strip().strip('"').strip("'")
                    elif "**Explanation:**" in line:
                        explanation = line.replace("**Explanation:**", "").strip().strip('"').strip("'")
                
                if original_line and corrected_line and original_line != corrected_line:
                    corrections.append(Correction(
                        original=original_line,
                        correction=corrected_line,
                        explanation=explanation,
                        category=CorrectionCategory.GRAMMAR
                    ))
            
            # Pattern 2: "Correction:" format (legacy support)
            if not corrections and "Correction:" in ai_response:
                lines = ai_response.split('\n')
                for line in lines:
                    if line.strip().startswith('Correction:'):
                        corrected_text = line.replace('Correction:', '').strip().strip('"').strip("'")
                        if corrected_text and corrected_text != user_message:
                            corrections.append(Correction(
                                original=user_message,
                                correction=corrected_text,
                                explanation="Grammar correction from AI",
                                category=CorrectionCategory.GRAMMAR
                            ))
                            break
            
            # Pattern 3: Common grammar error detection
            if not corrections:
                corrections.extend(self._detect_common_grammar_errors(user_message, ai_response))
            
            logger.info(f"Extracted {len(corrections)} corrections from AI response")
            return corrections
            
        except Exception as e:
            logger.error(f"Error extracting corrections: {str(e)}")
            return []
    
    def _detect_common_grammar_errors(self, user_message: str, ai_response: str) -> List[Correction]:
        """Detect common grammar errors by analyzing patterns.
        
        Args:
            user_message: Original user message
            ai_response: AI response
            
        Returns:
            List of detected corrections
        """
        corrections = []
        try:
            import re
            
            # Common error patterns
            error_patterns = [
                # Subject-verb agreement
                (r'\bI are\b', 'I am', 'Subject-verb agreement: Use "I am" not "I are"'),
                (r'\bto learning\b', 'to learn', 'Infinitive form: Use "to learn" not "to learning"'),
                (r'\bvery much happy\b', 'very happy', 'Word order: Use "very happy" not "very much happy"'),
                (r'\bI have 20 years old\b', 'I am 20 years old', 'Age expression: Use "I am" not "I have"'),
                (r'\bI am agree\b', 'I agree', 'Verb form: Use "I agree" not "I am agree"'),
                (r'\bI am boring\b', 'I am bored', 'Adjective choice: Use "bored" not "boring" for feelings'),
            ]
            
            for pattern, correction, explanation in error_patterns:
                if re.search(pattern, user_message, re.IGNORECASE):
                    corrected_text = re.sub(pattern, correction, user_message, flags=re.IGNORECASE)
                    if corrected_text != user_message:
                        corrections.append(Correction(
                            original=user_message,
                            correction=corrected_text,
                            explanation=explanation,
                            category=CorrectionCategory.GRAMMAR
                        ))
                        break  # Only one correction per message for now
            
            return corrections
            
        except Exception as e:
            logger.error(f"Error detecting common grammar errors: {str(e)}")
            return []
    
    def _detect_message_language(self, message: str, user_preferences: UserPreferences) -> str:
        """Detect if message is in native or target language.
        
        Args:
            message: User message
            user_preferences: User language preferences
            
        Returns:
            'native' or 'target' indicating detected language
        """
        try:
            # Simple heuristic: check for common words in each language
            native_lang = user_preferences.native_language.lower()
            target_lang = user_preferences.target_language.lower()
            
            # Common words for language detection
            language_indicators = {
                'es': ['hola', 'gracias', 'por favor', 'sí', 'no', 'muy', 'bien', 'que', 'como', 'donde'],
                'fr': ['bonjour', 'merci', 'oui', 'non', 'très', 'bien', 'que', 'comment', 'où', 'avec'],
                'de': ['hallo', 'danke', 'bitte', 'ja', 'nein', 'sehr', 'gut', 'wie', 'wo', 'mit'],
                'it': ['ciao', 'grazie', 'prego', 'sì', 'no', 'molto', 'bene', 'che', 'come', 'dove'],
                'pt': ['olá', 'obrigado', 'por favor', 'sim', 'não', 'muito', 'bem', 'que', 'como', 'onde'],
                'tr': ['merhaba', 'teşekkür', 'lütfen', 'evet', 'hayır', 'çok', 'iyi', 'ne', 'nasıl', 'nerede'],
                'en': ['hello', 'thank', 'please', 'yes', 'no', 'very', 'good', 'what', 'how', 'where']
            }
            
            message_lower = message.lower()
            
            # Count indicators for each language
            native_score = sum(1 for word in language_indicators.get(native_lang, []) if word in message_lower)
            target_score = sum(1 for word in language_indicators.get(target_lang, []) if word in message_lower)
            
            # If native language has more indicators, assume native
            if native_score > target_score:
                return 'native'
            else:
                return 'target'
                
        except Exception as e:
            logger.error(f"Error detecting message language: {str(e)}")
            return 'target'  # Default to target language
    
    async def _translate_to_target_language(self, message: str, native_lang: str, target_lang: str) -> str:
        """Translate message from native to target language.
        
        Args:
            message: Message in native language
            native_lang: Native language code
            target_lang: Target language code
            
        Returns:
            Translated message
        """
        try:
            # Don't translate if languages are the same
            if native_lang.lower() == target_lang.lower():
                logger.info(f"Skipping translation: native and target languages are the same ({native_lang})")
                return None
            
            language_names = {
                'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
                'it': 'Italian', 'pt': 'Portuguese', 'tr': 'Turkish', 'ar': 'Arabic',
                'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ru': 'Russian'
            }
            
            native_name = language_names.get(native_lang.lower(), native_lang)
            target_name = language_names.get(target_lang.lower(), target_lang)
            
            logger.info(f"Translating from {native_name} to {target_name}: {message[:50]}...")
            
            # Create a simple translation context without using the main conversation context
            from src.domain.entities.conversation_context import ConversationContext
            from src.domain.entities.message import Message, MessageRole
            
            # Simple translation prompt
            translation_messages = [
                Message(
                    id=uuid.uuid4(),
                    session_id=uuid.uuid4(),
                    role=MessageRole.USER,
                    content=f"Translate this {native_name} text to {target_name}: \"{message}\"",
                    created_at=datetime.utcnow()
                )
            ]
            
            translation_context = ConversationContext(
                recent_messages=[],
                summary=None,
                user_preferences=UserPreferences(
                    native_language=native_lang,
                    target_language=target_lang,
                    proficiency_level=ProficiencyLevel.A1
                ),
                session_mode=SessionMode.TUTOR
            )
            
            # Use LLM for translation
            translation_response = await self.llm_adapter.generate_response(
                translation_context,
                f"Translate this {native_name} text to {target_name}: \"{message}\""
            )
            
            translated_text = translation_response.content.strip()
            
            # Clean up the response (remove quotes and extra text)
            if translated_text.startswith('"') and translated_text.endswith('"'):
                translated_text = translated_text[1:-1]
            
            # Remove common prefixes that LLM might add
            prefixes_to_remove = [
                f"Translation to {target_name}:",
                f"In {target_name}:",
                "Translation:",
                "Here is the translation:",
                "The translation is:"
            ]
            
            for prefix in prefixes_to_remove:
                if translated_text.lower().startswith(prefix.lower()):
                    translated_text = translated_text[len(prefix):].strip()
            
            logger.info(f"Translation result: {translated_text}")
            return translated_text
            
        except Exception as e:
            logger.error(f"Error translating message: {str(e)}")
            return None  # Return None if translation fails
    
    async def get_session_info(self, session_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        """Get session information and statistics.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            
        Returns:
            Session information dictionary
            
        Raises:
            ChatUseCaseError: If session not found or access denied
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ChatUseCaseError("Session not found or access denied")
        
        message_count = await self._get_session_message_count(session_id)
        recent_messages = await self.memory_manager.get_recent_messages(session_id, count=5)
        
        return {
            'session_id': str(session.id),
            'mode': str(session.mode),
            'level': str(session.level),
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': message_count,
            'recent_message_count': len(recent_messages),
            'has_conversation_summary': await self.memory_manager.get_conversation_summary(session_id) is not None
        }
    
    async def end_session(self, session_id: uuid.UUID, user_id: uuid.UUID):
        """End a chat session and clean up resources.
        
        Args:
            session_id: Session ID
            user_id: User ID for authorization
            
        Raises:
            ChatUseCaseError: If session not found or access denied
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ChatUseCaseError("Session not found or access denied")
        
        try:
            # Flush memory cache to database
            await self.memory_manager.flush_session_to_database(session_id)
            
            # Clear memory cache
            await self.memory_manager.clear_session_cache(session_id)
            
            # Update session end time (if we add this field)
            await self._update_session_activity(session_id)
            
            logger.info(f"Successfully ended session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            raise ChatUseCaseError(f"Failed to end session: {str(e)}")
    
    def get_use_case_stats(self) -> dict:
        """Get use case performance statistics.
        
        Returns:
            Dictionary with use case statistics
        """
        avg_corrections = (self.total_corrections_made / self.total_messages_processed 
                          if self.total_messages_processed > 0 else 0)
        
        exercise_rate = (self.total_exercises_generated / self.total_messages_processed * 100
                        if self.total_messages_processed > 0 else 0)
        
        return {
            'total_conversations': self.total_conversations,
            'total_messages_processed': self.total_messages_processed,
            'total_corrections_made': self.total_corrections_made,
            'total_exercises_generated': self.total_exercises_generated,
            'total_structured_feedback_provided': self.total_structured_feedback_provided,
            'average_corrections_per_message': round(avg_corrections, 2),
            'exercise_generation_rate_percent': round(exercise_rate, 2)
        }
    
    # Enhanced methods for advanced features
    
    async def _get_enhanced_user_preferences(self, user_id: uuid.UUID) -> UserPreferences:
        """Get enhanced user preferences with level assessment integration.
        
        Args:
            user_id: User ID
            
        Returns:
            Enhanced user preferences
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ChatUseCaseError(f"User {user_id} not found")
        
        # Use assessed level if available, otherwise fall back to regular level
        proficiency_level = getattr(user, 'proficiency_level', 'A2')
        if hasattr(user, 'assessed_level') and user.assessed_level:
            proficiency_level = user.assessed_level
        
        # Convert string to enum if needed
        if isinstance(proficiency_level, str):
            level_mapping = {
                'beginner': ProficiencyLevel.A1,
                'intermediate': ProficiencyLevel.A2,
                'advanced': ProficiencyLevel.B1,
                'A1': ProficiencyLevel.A1,
                'A2': ProficiencyLevel.A2,
                'B1': ProficiencyLevel.B1,
                'B2': ProficiencyLevel.B2,
                'C1': ProficiencyLevel.C1,
                'C2': ProficiencyLevel.C2
            }
            proficiency_level = level_mapping.get(proficiency_level, ProficiencyLevel.A2)
        
        return UserPreferences(
            native_language=getattr(user, 'native_language', 'tr'),
            target_language=getattr(user, 'target_language', 'en'),
            proficiency_level=proficiency_level
        )
    
    async def _manage_topic_flow(
        self, 
        session: Session, 
        message_content: str, 
        user_preferences: UserPreferences
    ) -> Tuple[Optional['Topic'], Optional[str]]:
        """Manage topic flow and selection.
        
        Args:
            session: Current session
            message_content: User's message
            user_preferences: User preferences
            
        Returns:
            Tuple of (current_topic, topic_transition_suggestion)
        """
        try:
            # Get current topic from session if available
            current_topic = None
            if hasattr(session, 'current_topic') and session.current_topic:
                current_topic = await self.topic_repository.get_by_id(session.current_topic)
            
            # If no current topic, suggest one based on message content and user level
            if not current_topic:
                suggested_topics = await self.topic_manager.suggest_topics(
                    user_preferences, user_preferences.proficiency_level
                )
                if suggested_topics:
                    current_topic = suggested_topics[0]  # Use first suggestion
            
            # Check if topic transition is needed
            topic_transition = None
            if current_topic:
                coherence_check = await self.topic_manager.check_topic_coherence(
                    [], current_topic  # Would need recent messages here
                )
                if not coherence_check:
                    # Suggest topic transition
                    related_topics = await self.topic_repository.get_related_topics(current_topic.id)
                    if related_topics:
                        topic_transition = f"Would you like to talk about {related_topics[0].name}?"
            
            return current_topic, topic_transition
            
        except Exception as e:
            logger.warning(f"Error managing topic flow: {e}")
            return None, None
    
    async def _build_enhanced_conversation_context(
        self,
        session: Session,
        user_preferences: UserPreferences,
        current_topic: Optional['Topic']
    ) -> ConversationContext:
        """Build enhanced conversation context with topic information.
        
        Args:
            session: Current session
            user_preferences: User preferences
            current_topic: Current conversation topic
            
        Returns:
            Enhanced conversation context
        """
        # Get recent messages from memory cache
        recent_messages = await self.memory_manager.get_recent_messages(
            session.id, count=10
        )
        
        # Get conversation summary if available
        summary = await self.memory_manager.get_conversation_summary(session.id)
        
        # Add topic context to summary if available
        if current_topic and summary:
            summary = f"Topic: {current_topic.name} - {summary}"
        elif current_topic:
            summary = f"Current topic: {current_topic.name} - {current_topic.description}"
        
        return ConversationContext(
            recent_messages=recent_messages,
            summary=summary,
            user_preferences=user_preferences,
            session_mode=session.mode
        )
    
    async def _enhanced_language_detection(
        self, 
        message_content: str, 
        user_preferences: UserPreferences
    ) -> str:
        """Enhanced language detection with better accuracy.
        
        Args:
            message_content: User's message
            user_preferences: User preferences
            
        Returns:
            'native' or 'target' indicating detected language
        """
        try:
            # Use translation service for better language detection
            detected_language = await self.translation_service.detect_language(message_content)
            
            # Compare with user's native and target languages
            if detected_language.lower() == user_preferences.native_language.lower():
                return 'native'
            else:
                return 'target'
                
        except Exception as e:
            logger.warning(f"Enhanced language detection failed: {e}")
            # Fall back to simple detection
            return self._detect_message_language(message_content, user_preferences)
    
    async def _enhanced_translation(
        self,
        message_content: str,
        native_language: str,
        target_language: str,
        current_topic: Optional['Topic']
    ) -> Optional[str]:
        """Enhanced translation with topic context.
        
        Args:
            message_content: Message to translate
            native_language: Native language code
            target_language: Target language code
            current_topic: Current conversation topic for context
            
        Returns:
            Translated message or None if translation fails
        """
        try:
            # Add topic context to translation if available
            context = None
            if current_topic:
                context = f"Topic: {current_topic.name} - {current_topic.description}"
            
            return await self.translation_service.translate_with_context(
                message_content, native_language, target_language, context
            )
            
        except Exception as e:
            logger.warning(f"Enhanced translation failed: {e}")
            # Fall back to basic translation
            return await self._translate_to_target_language(
                message_content, native_language, target_language
            )
    
    async def _generate_topic_aware_response(
        self,
        conversation_context: ConversationContext,
        message_content: str,
        current_topic: Optional['Topic']
    ) -> str:
        """Generate AI response with topic awareness.
        
        Args:
            conversation_context: Conversation context
            message_content: User's message
            current_topic: Current conversation topic
            
        Returns:
            AI response
        """
        try:
            # Add topic information to the prompt if available
            enhanced_prompt = message_content
            if current_topic:
                topic_context = f"[Current topic: {current_topic.name} - {current_topic.description}] "
                enhanced_prompt = topic_context + message_content
            
            # Generate response using LLM adapter
            response = await self.llm_adapter.generate_response(
                conversation_context, enhanced_prompt
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating topic-aware response: {e}")
            # Fall back to basic response generation
            response = await self.llm_adapter.generate_response(
                conversation_context, message_content
            )
            return response.content
    
    async def _check_and_generate_structured_feedback(
        self,
        session: Session,
        user_preferences: UserPreferences,
        session_message_count: int,
        current_topic: Optional['Topic']
    ) -> Optional['StructuredFeedback']:
        """Check if structured feedback should be provided and generate it.
        
        Args:
            session: Current session
            user_preferences: User preferences
            session_message_count: Current message count
            current_topic: Current conversation topic
            
        Returns:
            Structured feedback if it's time for feedback cycle, None otherwise
        """
        try:
            # Check if it's time for structured feedback (every 3 messages)
            if session_message_count % 3 != 0:
                return None
            
            # Get recent messages for feedback analysis
            recent_messages = await self.memory_manager.get_recent_messages(
                session.id, count=3
            )
            
            if len(recent_messages) < 3:
                return None
            
            # Generate structured feedback using pedagogy engine
            corrections = []  # Would extract from recent messages
            
            return await self.pedagogy_engine.generate_structured_feedback(
                recent_messages, corrections, current_topic
            )
            
        except Exception as e:
            logger.warning(f"Error generating structured feedback: {e}")
            return None
    
    async def _apply_enhanced_pedagogy(
        self,
        ai_response: str,
        raw_corrections: List[Correction],
        conversation_context: ConversationContext,
        session_message_count: int,
        structured_feedback: Optional['StructuredFeedback']
    ) -> 'PedagogicalResponse':
        """Apply enhanced pedagogical optimization.
        
        Args:
            ai_response: AI response
            raw_corrections: Raw corrections
            conversation_context: Conversation context
            session_message_count: Session message count
            structured_feedback: Structured feedback if available
            
        Returns:
            Enhanced pedagogical response
        """
        try:
            # Use pedagogy engine with enhanced features
            return await self.pedagogy_engine.optimize_response_with_feedback(
                ai_response, raw_corrections, conversation_context, 
                session_message_count, structured_feedback
            )
            
        except Exception as e:
            logger.warning(f"Enhanced pedagogy failed: {e}")
            # Fall back to basic pedagogy
            return await self.pedagogy_engine.optimize_response_with_feedback(
                ai_response, raw_corrections, conversation_context, session_message_count
            )
    
    async def _update_enhanced_session_state(
        self,
        session_id: uuid.UUID,
        current_topic: Optional['Topic'],
        feedback_provided: bool,
        session_message_count: int
    ):
        """Update session state with enhanced tracking.
        
        Args:
            session_id: Session ID
            current_topic: Current topic
            feedback_provided: Whether structured feedback was provided
            session_message_count: Current message count
        """
        try:
            # Update session with topic and feedback information
            update_data = {
                'updated_at': datetime.utcnow()
            }
            
            if current_topic:
                update_data['current_topic'] = current_topic.id
            
            if feedback_provided:
                update_data['feedback_count'] = getattr(
                    await self.session_repository.get_by_id(session_id), 
                    'feedback_count', 0
                ) + 1
                update_data['last_feedback_message'] = session_message_count
            
            await self.session_repository.update_enhanced_state(session_id, update_data)
            
        except Exception as e:
            logger.warning(f"Failed to update enhanced session state: {e}")
            # Fall back to basic session update
            await self._update_session_activity(session_id)