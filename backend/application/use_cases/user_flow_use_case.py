"""User flow management use case for post-login flow handling."""

import uuid
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from src.domain.entities.user import User
from src.domain.entities.language_preferences import LanguagePreferences
from src.domain.entities.session import Session, SessionMode, ProficiencyLevel
from src.domain.entities.topic import TopicCategory
from src.domain.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.repositories.session_repository_interface import SessionRepositoryInterface
from src.domain.exceptions import ValidationError, DomainError


logger = logging.getLogger(__name__)


class UserFlowError(DomainError):
    """User flow specific errors."""
    pass


class UserNotFoundError(UserFlowError):
    """User not found error."""
    pass


class InvalidFlowStateError(UserFlowError):
    """Invalid flow state error."""
    pass


class FlowState(str, Enum):
    """User flow states."""
    LANGUAGE_SELECTION = "language_selection"
    LEVEL_SELECTION = "level_selection"
    TOPIC_PREFERENCES = "topic_preferences"
    READY_FOR_CHAT = "ready_for_chat"
    ONBOARDING_COMPLETE = "onboarding_complete"


@dataclass
class UserFlowState:
    """Current state of user flow."""
    
    user_id: uuid.UUID
    current_state: FlowState
    has_language_preferences: bool
    has_level_assessment: bool
    has_topic_preferences: bool
    onboarding_completed: bool
    next_action: str
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LanguageSelectionOptions:
    """Available language selection options."""
    
    available_languages: List[Dict[str, str]]
    current_native: Optional[str] = None
    current_target: Optional[str] = None
    
    def __post_init__(self):
        if not self.available_languages:
            self.available_languages = self._get_default_languages()
    
    def _get_default_languages(self) -> List[Dict[str, str]]:
        """Get default supported languages."""
        return [
            {"code": "EN", "name": "English"},
            {"code": "ES", "name": "Spanish"},
            {"code": "FR", "name": "French"},
            {"code": "DE", "name": "German"},
            {"code": "IT", "name": "Italian"},
            {"code": "PT", "name": "Portuguese"},
            {"code": "TR", "name": "Turkish"},
            {"code": "AR", "name": "Arabic"},
            {"code": "ZH", "name": "Chinese"},
            {"code": "JA", "name": "Japanese"},
            {"code": "KO", "name": "Korean"},
            {"code": "RU", "name": "Russian"}
        ]


@dataclass
class LevelSelectionOptions:
    """Available level selection options."""
    
    assessment_available: bool = True
    manual_selection_available: bool = True
    current_level: Optional[str] = None
    assessed_level: Optional[str] = None
    assessment_date: Optional[datetime] = None
    
    def get_available_levels(self) -> List[Dict[str, str]]:
        """Get available proficiency levels."""
        return [
            {"code": "A1", "name": "Beginner (A1)", "description": "Basic phrases and simple interactions"},
            {"code": "A2", "name": "Elementary (A2)", "description": "Simple conversations about familiar topics"},
            {"code": "B1", "name": "Intermediate (B1)", "description": "Express opinions and handle most situations"},
            {"code": "B2", "name": "Upper-Intermediate (B2)", "description": "Detailed discussions on complex topics"},
            {"code": "C1", "name": "Advanced (C1)", "description": "Fluent expression with sophisticated vocabulary"},
            {"code": "C2", "name": "Proficient (C2)", "description": "Native-like fluency and precision"}
        ]


@dataclass
class TopicPreferencesOptions:
    """Available topic preference options."""
    
    available_categories: List[Dict[str, str]]
    current_preferences: List[TopicCategory] = None
    
    def __post_init__(self):
        if not self.available_categories:
            self.available_categories = self._get_default_categories()
        if self.current_preferences is None:
            self.current_preferences = []
    
    def _get_default_categories(self) -> List[Dict[str, str]]:
        """Get default topic categories."""
        return [
            {"code": "daily_life", "name": "Daily Life", "description": "Everyday activities and routines"},
            {"code": "travel", "name": "Travel", "description": "Tourism, transportation, and cultural experiences"},
            {"code": "work", "name": "Work", "description": "Professional communication and workplace topics"},
            {"code": "technology", "name": "Technology", "description": "Digital tools, innovation, and modern life"},
            {"code": "culture", "name": "Culture", "description": "Arts, traditions, and cultural differences"},
            {"code": "health", "name": "Health", "description": "Wellness, medical topics, and lifestyle"},
            {"code": "education", "name": "Education", "description": "Learning, academic topics, and personal development"},
            {"code": "entertainment", "name": "Entertainment", "description": "Movies, music, sports, and hobbies"},
            {"code": "food", "name": "Food", "description": "Cuisine, cooking, and dining experiences"},
            {"code": "news", "name": "News", "description": "Current events, politics, and social issues"}
        ]


@dataclass
class ChatSessionOptions:
    """Options for initiating chat session."""
    
    session_modes: List[Dict[str, str]]
    recommended_mode: SessionMode
    user_level: ProficiencyLevel
    
    def __post_init__(self):
        if not self.session_modes:
            self.session_modes = [
                {
                    "code": "tutor",
                    "name": "Tutor Mode",
                    "description": "Get corrections and detailed feedback on your language use"
                },
                {
                    "code": "buddy",
                    "name": "Conversation Buddy",
                    "description": "Practice natural conversation without interruptions"
                }
            ]


class UserFlowUseCase:
    """Use case for managing user flow after login."""
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        session_repository: SessionRepositoryInterface
    ):
        """Initialize user flow use case.
        
        Args:
            user_repository: User repository interface
            session_repository: Session repository interface
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
    
    async def handle_post_login(self, user_id: uuid.UUID) -> UserFlowState:
        """Handle post-login flow and determine user's current state.
        
        Args:
            user_id: ID of the logged-in user
            
        Returns:
            UserFlowState: Current state and next action for the user
            
        Raises:
            UserFlowError: If flow handling fails
        """
        try:
            # Get user data
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            # Analyze user's current state
            flow_state = self._analyze_user_state(user)
            
            logger.info(f"Post-login flow for user {user_id}: {flow_state.current_state}")
            return flow_state
            
        except ValidationError as e:
            raise UserFlowError(f"Validation error: {str(e)}")
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to handle post-login flow: {e}")
            raise UserFlowError(f"Failed to handle post-login flow: {str(e)}")
    
    async def set_language_preferences(
        self, 
        user_id: uuid.UUID, 
        native_language: str, 
        target_language: str
    ) -> UserFlowState:
        """Set user's language preferences.
        
        Args:
            user_id: ID of the user
            native_language: User's native language code
            target_language: User's target language code
            
        Returns:
            UserFlowState: Updated flow state after setting preferences
            
        Raises:
            UserFlowError: If preference setting fails
        """
        try:
            # Validate languages
            self._validate_language_codes(native_language, target_language)
            
            # Get user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            # Update language preferences
            success = await self.user_repository.update_language_preferences(
                user_id=user_id,
                native_language=native_language,
                target_language=target_language,
                proficiency_level=user.proficiency_level or 'A2'
            )
            
            if not success:
                raise UserFlowError("Failed to update language preferences")
            
            # Get updated user and return new flow state
            updated_user = await self.user_repository.get_by_id(user_id)
            flow_state = self._analyze_user_state(updated_user)
            
            logger.info(f"Updated language preferences for user {user_id}: {native_language} -> {target_language}")
            return flow_state
            
        except ValidationError as e:
            raise UserFlowError(f"Validation error: {str(e)}")
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to set language preferences: {e}")
            raise UserFlowError(f"Failed to set language preferences: {str(e)}")
    
    async def initiate_level_selection(self, user_id: uuid.UUID) -> LevelSelectionOptions:
        """Get level selection options for the user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            LevelSelectionOptions: Available level selection options
            
        Raises:
            UserFlowError: If level selection initiation fails
        """
        try:
            # Get user data
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            # Create level selection options
            options = LevelSelectionOptions(
                assessment_available=True,
                manual_selection_available=True,
                current_level=user.proficiency_level,
                assessed_level=user.assessed_level,
                assessment_date=user.assessment_date
            )
            
            logger.info(f"Initiated level selection for user {user_id}")
            return options
            
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to initiate level selection: {e}")
            raise UserFlowError(f"Failed to initiate level selection: {str(e)}")
    
    async def set_manual_level(
        self, 
        user_id: uuid.UUID, 
        proficiency_level: str
    ) -> UserFlowState:
        """Set user's proficiency level manually.
        
        Args:
            user_id: ID of the user
            proficiency_level: Selected proficiency level
            
        Returns:
            UserFlowState: Updated flow state after setting level
            
        Raises:
            UserFlowError: If level setting fails
        """
        try:
            # Validate proficiency level
            valid_levels = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
            if proficiency_level not in valid_levels:
                raise ValidationError(f"Invalid proficiency level: {proficiency_level}")
            
            # Get user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            # Update proficiency level
            success = await self.user_repository.update_language_preferences(
                user_id=user_id,
                native_language=user.native_language,
                target_language=user.target_language,
                proficiency_level=proficiency_level
            )
            
            if not success:
                raise UserFlowError("Failed to update proficiency level")
            
            # Get updated user and return new flow state
            updated_user = await self.user_repository.get_by_id(user_id)
            flow_state = self._analyze_user_state(updated_user)
            
            logger.info(f"Set manual level for user {user_id}: {proficiency_level}")
            return flow_state
            
        except ValidationError as e:
            raise UserFlowError(f"Validation error: {str(e)}")
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to set manual level: {e}")
            raise UserFlowError(f"Failed to set manual level: {str(e)}")
    
    async def get_topic_preferences_options(self, user_id: uuid.UUID) -> TopicPreferencesOptions:
        """Get topic preference options for the user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            TopicPreferencesOptions: Available topic preference options
            
        Raises:
            UserFlowError: If getting options fails
        """
        try:
            # Get user data
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            # Convert string topics to TopicCategory enums if possible
            current_preferences = []
            if user.preferred_topics:
                for topic_str in user.preferred_topics:
                    try:
                        # Try to match string to TopicCategory enum
                        topic_category = TopicCategory(topic_str.upper())
                        current_preferences.append(topic_category)
                    except ValueError:
                        # Skip invalid topic categories
                        logger.warning(f"Invalid topic category in user preferences: {topic_str}")
                        continue
            
            # Create topic preferences options
            options = TopicPreferencesOptions(
                available_categories=[],  # Will be populated by __post_init__
                current_preferences=current_preferences
            )
            
            logger.info(f"Got topic preferences options for user {user_id}")
            return options
            
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to get topic preferences options: {e}")
            raise UserFlowError(f"Failed to get topic preferences options: {str(e)}")
    
    async def set_topic_preferences(
        self, 
        user_id: uuid.UUID, 
        preferred_topics: List[str],
        learning_goals: Optional[List[str]] = None
    ) -> UserFlowState:
        """Set user's topic preferences and learning goals.
        
        Args:
            user_id: ID of the user
            preferred_topics: List of preferred topic category codes
            learning_goals: Optional list of learning goals
            
        Returns:
            UserFlowState: Updated flow state after setting preferences
            
        Raises:
            UserFlowError: If preference setting fails
        """
        try:
            # Get user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            # Validate and convert topic categories
            valid_categories = [category.value for category in TopicCategory]
            validated_topics = []
            
            for topic in preferred_topics:
                # Convert to lowercase to match enum values
                topic_lower = topic.lower()
                if topic_lower in valid_categories:
                    validated_topics.append(topic_lower)
                else:
                    logger.warning(f"Invalid topic category: {topic}")
            
            # Update user preferences
            user.preferred_topics = validated_topics
            if learning_goals is not None:
                user.learning_goals = learning_goals
            
            # Save updated user
            await self.user_repository.update(user)
            
            # Get updated flow state
            flow_state = self._analyze_user_state(user)
            
            logger.info(f"Set topic preferences for user {user_id}: {len(validated_topics)} topics")
            return flow_state
            
        except ValidationError as e:
            raise UserFlowError(f"Validation error: {str(e)}")
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to set topic preferences: {e}")
            raise UserFlowError(f"Failed to set topic preferences: {str(e)}")
    
    async def proceed_to_chat(
        self, 
        user_id: uuid.UUID, 
        session_mode: Optional[SessionMode] = None
    ) -> Tuple[Session, ChatSessionOptions]:
        """Create a chat session and proceed to chat interface.
        
        Args:
            user_id: ID of the user
            session_mode: Optional session mode (defaults to TUTOR)
            
        Returns:
            Tuple of (Session, ChatSessionOptions)
            
        Raises:
            UserFlowError: If chat session creation fails
        """
        try:
            # Get user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            # Validate user is ready for chat
            flow_state = self._analyze_user_state(user)
            if flow_state.current_state not in [FlowState.READY_FOR_CHAT, FlowState.ONBOARDING_COMPLETE]:
                raise InvalidFlowStateError(f"User not ready for chat. Current state: {flow_state.current_state}")
            
            # Determine session mode and level
            mode = session_mode or SessionMode.TUTOR
            
            # Convert proficiency level to enum
            level_mapping = {
                'A1': ProficiencyLevel.A1,
                'A2': ProficiencyLevel.A2,
                'B1': ProficiencyLevel.B1,
                'B2': ProficiencyLevel.B2,
                'C1': ProficiencyLevel.C1,
                'C2': ProficiencyLevel.C2,
                'beginner': ProficiencyLevel.BEGINNER,
                'intermediate': ProficiencyLevel.INTERMEDIATE,
                'advanced': ProficiencyLevel.ADVANCED,
                'native': ProficiencyLevel.NATIVE
            }
            
            user_level_str = user.assessed_level or user.proficiency_level or 'A2'
            user_level = level_mapping.get(user_level_str, ProficiencyLevel.A2)
            
            # Create new session
            session = Session(
                id=uuid.uuid4(),
                user_id=user_id,
                mode=mode,
                level=user_level,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            # Save session
            created_session = await self.session_repository.create(session)
            
            # Mark onboarding as complete if not already
            if not user.onboarding_completed:
                await self.user_repository.update_onboarding_status(user_id, completed=True)
            
            # Create chat session options
            chat_options = ChatSessionOptions(
                session_modes=[],  # Will be populated by __post_init__
                recommended_mode=mode,
                user_level=user_level
            )
            
            logger.info(f"Created chat session {created_session.id} for user {user_id}")
            return created_session, chat_options
            
        except ValidationError as e:
            raise UserFlowError(f"Validation error: {str(e)}")
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to proceed to chat: {e}")
            raise UserFlowError(f"Failed to proceed to chat: {str(e)}")
    
    async def get_language_selection_options(self, user_id: uuid.UUID) -> LanguageSelectionOptions:
        """Get language selection options for the user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            LanguageSelectionOptions: Available language options
            
        Raises:
            UserFlowError: If getting options fails
        """
        try:
            # Get user data
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            # Create language selection options
            options = LanguageSelectionOptions(
                available_languages=[],  # Will be populated by __post_init__
                current_native=user.native_language,
                current_target=user.target_language
            )
            
            logger.info(f"Got language selection options for user {user_id}")
            return options
            
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to get language selection options: {e}")
            raise UserFlowError(f"Failed to get language selection options: {str(e)}")
    
    async def complete_onboarding(self, user_id: uuid.UUID) -> UserFlowState:
        """Mark user's onboarding as complete.
        
        Args:
            user_id: ID of the user
            
        Returns:
            UserFlowState: Final flow state after onboarding completion
            
        Raises:
            UserFlowError: If onboarding completion fails
        """
        try:
            # Update onboarding status
            success = await self.user_repository.update_onboarding_status(user_id, completed=True)
            if not success:
                raise UserFlowError("Failed to update onboarding status")
            
            # Get updated user and return final flow state
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")
            
            flow_state = self._analyze_user_state(user)
            
            logger.info(f"Completed onboarding for user {user_id}")
            return flow_state
            
        except UserFlowError:
            raise
        except Exception as e:
            logger.error(f"Failed to complete onboarding: {e}")
            raise UserFlowError(f"Failed to complete onboarding: {str(e)}")
    
    def _analyze_user_state(self, user: User) -> UserFlowState:
        """Analyze user's current state and determine next action.
        
        Args:
            user: User entity
            
        Returns:
            UserFlowState: Current flow state and next action
        """
        # Check language preferences
        has_language_preferences = (
            user.native_language is not None and 
            user.target_language is not None and
            user.native_language != user.target_language
        )
        
        # Check level assessment/selection
        has_level_assessment = (
            user.proficiency_level is not None or 
            user.assessed_level is not None
        )
        
        # Check topic preferences (optional but recommended)
        has_topic_preferences = (
            user.preferred_topics is not None and 
            len(user.preferred_topics) > 0
        )
        
        # Determine current state and next action
        if not has_language_preferences:
            current_state = FlowState.LANGUAGE_SELECTION
            next_action = "Please select your native and target languages"
        elif not has_level_assessment:
            current_state = FlowState.LEVEL_SELECTION
            next_action = "Please take a level assessment or select your proficiency level"
        elif not has_topic_preferences and not user.onboarding_completed:
            current_state = FlowState.TOPIC_PREFERENCES
            next_action = "Please select your preferred conversation topics (optional)"
        elif not user.onboarding_completed:
            current_state = FlowState.READY_FOR_CHAT
            next_action = "Ready to start your first conversation!"
        else:
            current_state = FlowState.ONBOARDING_COMPLETE
            next_action = "Welcome back! Ready to continue learning?"
        
        return UserFlowState(
            user_id=user.id,
            current_state=current_state,
            has_language_preferences=has_language_preferences,
            has_level_assessment=has_level_assessment,
            has_topic_preferences=has_topic_preferences,
            onboarding_completed=user.onboarding_completed,
            next_action=next_action,
            metadata={
                'native_language': user.native_language,
                'target_language': user.target_language,
                'proficiency_level': user.proficiency_level,
                'assessed_level': user.assessed_level,
                'preferred_topics_count': len(user.preferred_topics) if user.preferred_topics else 0,
                'learning_goals_count': len(user.learning_goals) if user.learning_goals else 0
            }
        )
    
    def _validate_language_codes(self, native_language: str, target_language: str) -> None:
        """Validate language codes.
        
        Args:
            native_language: Native language code
            target_language: Target language code
            
        Raises:
            ValidationError: If language codes are invalid
        """
        valid_languages = {
            'EN', 'ES', 'FR', 'DE', 'IT', 'PT', 'RU', 'ZH', 'JA', 'KO',
            'AR', 'HI', 'TR', 'PL', 'NL', 'SV', 'DA', 'NO', 'FI', 'HE'
        }
        
        if not native_language or native_language.upper() not in valid_languages:
            raise ValidationError(f"Invalid native language: {native_language}")
        
        if not target_language or target_language.upper() not in valid_languages:
            raise ValidationError(f"Invalid target language: {target_language}")
        
        if native_language.upper() == target_language.upper():
            raise ValidationError("Native and target languages must be different")