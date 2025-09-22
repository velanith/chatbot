"""Fallback service for handling service failures gracefully."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from src.domain.entities.message import Message, MessageRole, Correction
from src.domain.entities.session import SessionMode, ProficiencyLevel
from src.domain.exceptions import ServiceError

logger = logging.getLogger(__name__)


class FallbackService:
    """Service providing fallback responses when primary services fail."""
    
    def __init__(self):
        """Initialize fallback service."""
        self.fallback_responses = self._load_fallback_responses()
        self.fallback_corrections = self._load_fallback_corrections()
        self.fallback_exercises = self._load_fallback_exercises()
    
    def get_fallback_chat_response(
        self,
        user_message: str,
        session_mode: SessionMode,
        proficiency_level: ProficiencyLevel,
        error_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get fallback chat response when AI service fails.
        
        Args:
            user_message: User's message
            session_mode: Session mode (tutor/buddy)
            proficiency_level: User's proficiency level
            error_context: Context about the error that occurred
            
        Returns:
            Fallback response data
        """
        try:
            logger.info(f"Generating fallback response for {session_mode.value} mode, level {proficiency_level.value}")
            
            # Select appropriate fallback response
            response_key = f"{session_mode.value}_{proficiency_level.value}"
            fallback_response = self.fallback_responses.get(
                response_key,
                self.fallback_responses.get("default")
            )
            
            # Personalize the response
            personalized_response = self._personalize_response(
                fallback_response,
                user_message,
                session_mode,
                proficiency_level
            )
            
            # Add basic corrections if possible
            corrections = self._generate_basic_corrections(user_message)
            
            # Add simple exercise if in tutor mode
            exercise = None
            if session_mode == SessionMode.TUTOR:
                exercise = self._generate_simple_exercise(proficiency_level)
            
            return {
                "response": personalized_response,
                "corrections": corrections,
                "exercise": exercise,
                "is_fallback": True,
                "fallback_reason": error_context or "Service temporarily unavailable"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate fallback response: {e}")
            return self._get_emergency_response()
    
    def get_fallback_session_summary(
        self,
        session_id: str,
        message_count: int,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """Get fallback session summary when summary generation fails.
        
        Args:
            session_id: Session ID
            message_count: Number of messages in session
            duration_minutes: Session duration
            
        Returns:
            Fallback session summary
        """
        return {
            "session_id": session_id,
            "summary": f"Conversation session with {message_count} messages over {duration_minutes} minutes.",
            "highlights": [
                "Practice session completed",
                f"Exchanged {message_count} messages",
                f"Session lasted {duration_minutes} minutes"
            ],
            "recommendations": [
                "Continue practicing regularly",
                "Focus on areas where you received corrections",
                "Try different conversation topics"
            ],
            "is_fallback": True
        }
    
    def get_fallback_corrections(
        self,
        text: str,
        max_corrections: int = 3
    ) -> List[Correction]:
        """Get basic fallback corrections when correction service fails.
        
        Args:
            text: Text to check for corrections
            max_corrections: Maximum number of corrections to return
            
        Returns:
            List of basic corrections
        """
        corrections = []
        
        try:
            # Basic grammar checks
            corrections.extend(self._check_basic_grammar(text))
            
            # Basic spelling checks
            corrections.extend(self._check_basic_spelling(text))
            
            # Limit to max corrections
            return corrections[:max_corrections]
            
        except Exception as e:
            logger.error(f"Failed to generate fallback corrections: {e}")
            return []
    
    def _load_fallback_responses(self) -> Dict[str, str]:
        """Load predefined fallback responses."""
        return {
            "tutor_A1": "I understand you're learning English! That's great. I'm here to help you practice. Even though our main system is having a small issue right now, we can still chat. Keep practicing - you're doing well!",
            "tutor_A2": "Thank you for your message! I can see you're working hard on your English. While our AI system is temporarily unavailable, I want you to know that practice is the key to improvement. Keep going!",
            "tutor_B1": "I appreciate your message and your dedication to learning English. Although our advanced features are temporarily unavailable, remember that every conversation helps you improve. Your progress is important!",
            "tutor_B2": "Thank you for continuing to practice with us. While we're experiencing some technical difficulties with our main system, your commitment to learning is admirable. Keep up the excellent work!",
            "tutor_C1": "I acknowledge your message and your advanced English skills. Despite current technical limitations, your continued practice demonstrates excellent dedication to language mastery.",
            "tutor_C2": "Your message reflects sophisticated English usage. While our primary systems are temporarily offline, your persistent engagement with the language learning process is commendable.",
            
            "buddy_A1": "Hey! Thanks for chatting with me. I'm having some technical problems right now, but I still want to talk with you. Your English is getting better!",
            "buddy_A2": "Hi there! I got your message. Sorry, but I'm having some issues with my main system right now. But don't worry - talking with you is always fun!",
            "buddy_B1": "Hello! I see your message and I appreciate you chatting with me. I'm having some technical difficulties at the moment, but I enjoy our conversations!",
            "buddy_B2": "Hi! Thanks for your message. I'm experiencing some system issues right now, but I always enjoy talking with you. Your English sounds great!",
            "buddy_C1": "Hello! I received your message and appreciate our conversation. I'm currently experiencing some technical difficulties, but I value our chats.",
            "buddy_C2": "Hi there! Your message came through clearly. I'm having some system issues at the moment, but I always enjoy our sophisticated conversations.",
            
            "default": "Thank you for your message. I'm experiencing some technical difficulties right now, but I appreciate you practicing your English with me. Please try again in a few moments!"
        }
    
    def _load_fallback_corrections(self) -> Dict[str, Dict[str, str]]:
        """Load basic correction patterns."""
        return {
            "common_mistakes": {
                "i am": "I am",
                "i'm": "I'm",
                "i have": "I have",
                "i've": "I've",
                "i will": "I will",
                "i'll": "I'll",
                "dont": "don't",
                "cant": "can't",
                "wont": "won't",
                "isnt": "isn't",
                "arent": "aren't",
                "wasnt": "wasn't",
                "werent": "weren't"
            },
            "grammar_patterns": {
                "i are": "I am",
                "i is": "I am",
                "he are": "he is",
                "she are": "she is",
                "they is": "they are"
            }
        }
    
    def _load_fallback_exercises(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load simple exercises by proficiency level."""
        return {
            "A1": [
                {
                    "type": "fill_blank",
                    "prompt": "Complete: I ___ happy today.",
                    "answer": "am",
                    "explanation": "Use 'am' with 'I'"
                },
                {
                    "type": "fill_blank", 
                    "prompt": "Complete: She ___ a student.",
                    "answer": "is",
                    "explanation": "Use 'is' with 'she'"
                }
            ],
            "A2": [
                {
                    "type": "fill_blank",
                    "prompt": "Complete: I ___ to school yesterday.",
                    "answer": "went",
                    "explanation": "Use past tense 'went' for yesterday"
                },
                {
                    "type": "fill_blank",
                    "prompt": "Complete: They ___ playing football now.",
                    "answer": "are",
                    "explanation": "Use 'are' with 'they' in present continuous"
                }
            ],
            "B1": [
                {
                    "type": "fill_blank",
                    "prompt": "Complete: If I ___ rich, I would travel the world.",
                    "answer": "were",
                    "explanation": "Use 'were' in second conditional"
                }
            ],
            "B2": [
                {
                    "type": "fill_blank",
                    "prompt": "Complete: I wish I ___ studied harder.",
                    "answer": "had",
                    "explanation": "Use 'had' for past regrets"
                }
            ]
        }
    
    def _personalize_response(
        self,
        base_response: str,
        user_message: str,
        session_mode: SessionMode,
        proficiency_level: ProficiencyLevel
    ) -> str:
        """Personalize the fallback response based on user input."""
        # Add user's name if mentioned
        if "my name is" in user_message.lower():
            try:
                name_part = user_message.lower().split("my name is")[1].strip().split()[0]
                if name_part.isalpha():
                    base_response = f"Nice to meet you, {name_part.capitalize()}! " + base_response
            except:
                pass
        
        # Add encouragement based on message length
        if len(user_message.split()) > 10:
            base_response += " I can see you're using longer sentences - that's excellent progress!"
        
        return base_response
    
    def _generate_basic_corrections(self, text: str) -> List[Dict[str, Any]]:
        """Generate basic corrections using simple pattern matching."""
        corrections = []
        text_lower = text.lower()
        
        # Check common mistakes
        for mistake, correction in self.fallback_corrections["common_mistakes"].items():
            if mistake in text_lower and mistake != correction.lower():
                corrections.append({
                    "original": mistake,
                    "corrected": correction,
                    "category": "spelling",
                    "explanation": f"'{correction}' is the correct spelling"
                })
        
        # Check grammar patterns
        for pattern, correction in self.fallback_corrections["grammar_patterns"].items():
            if pattern in text_lower:
                corrections.append({
                    "original": pattern,
                    "corrected": correction,
                    "category": "grammar",
                    "explanation": f"Use '{correction}' instead of '{pattern}'"
                })
        
        return corrections[:2]  # Limit to 2 corrections
    
    def _check_basic_grammar(self, text: str) -> List[Correction]:
        """Basic grammar checking."""
        corrections = []
        # This would contain basic grammar rules
        # For now, return empty list
        return corrections
    
    def _check_basic_spelling(self, text: str) -> List[Correction]:
        """Basic spelling checking."""
        corrections = []
        # This would contain basic spelling checks
        # For now, return empty list
        return corrections
    
    def _generate_simple_exercise(self, proficiency_level: ProficiencyLevel) -> Optional[Dict[str, Any]]:
        """Generate a simple exercise based on proficiency level."""
        level_exercises = self.fallback_exercises.get(proficiency_level.value, [])
        if level_exercises:
            import random
            return random.choice(level_exercises)
        return None
    
    def _get_emergency_response(self) -> Dict[str, Any]:
        """Get emergency response when all fallback mechanisms fail."""
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
            "corrections": [],
            "exercise": None,
            "is_fallback": True,
            "fallback_reason": "Emergency fallback - all systems unavailable"
        }
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Check if a service is healthy (placeholder for health checking)."""
        # This would implement actual health checks
        # For now, always return True
        return True
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        return {
            "fallback_service": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "available_fallbacks": {
                "chat_responses": len(self.fallback_responses),
                "correction_patterns": len(self.fallback_corrections),
                "exercise_templates": sum(len(exercises) for exercises in self.fallback_exercises.values())
            }
        }