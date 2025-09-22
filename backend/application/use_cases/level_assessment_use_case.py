"""Level assessment use case for AI-powered proficiency evaluation."""

import uuid
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.domain.entities.assessment import (
    AssessmentSession, 
    AssessmentResponse, 
    AssessmentStatus, 
    LanguagePair
)
from src.domain.entities.user import User
from src.domain.repositories.assessment_session_repository_interface import AssessmentSessionRepositoryInterface
from src.domain.repositories.user_repository_interface import UserRepositoryInterface
from src.application.services.llm_service_interface import (
    LLMServiceInterface, 
    LLMRequest, 
    LLMModel,
    LLMServiceError
)
from src.domain.exceptions import ValidationError, DomainError


logger = logging.getLogger(__name__)


class LevelAssessmentError(DomainError):
    """Level assessment specific errors."""
    pass


class AssessmentSessionNotFoundError(LevelAssessmentError):
    """Assessment session not found error."""
    pass


class AssessmentAlreadyCompletedError(LevelAssessmentError):
    """Assessment already completed error."""
    pass


class AssessmentExpiredError(LevelAssessmentError):
    """Assessment session expired error."""
    pass


@dataclass
class AssessmentQuestion:
    """Assessment question data structure."""
    
    id: str
    content: str
    expected_level: str
    category: str
    instructions: Optional[str] = None


@dataclass
class AssessmentResult:
    """Assessment evaluation result."""
    
    question_id: str
    user_response: str
    ai_evaluation: str
    complexity_score: float
    accuracy_score: float
    fluency_score: float
    estimated_level: str
    feedback: Optional[str] = None


@dataclass
class LevelAssessmentOptions:
    """Options for level assessment configuration."""
    
    max_questions: int = 10
    min_questions: int = 5
    session_timeout_hours: int = 2
    confidence_threshold: float = 0.8
    adaptive_questioning: bool = True


class AssessmentQuestionGenerator:
    """Generates assessment questions based on language pair and current level estimate."""
    
    # Question templates for different levels and categories
    QUESTION_TEMPLATES = {
        'A1': {
            'introduction': [
                "Please introduce yourself. Tell me your name and where you are from.",
                "What do you like to do in your free time?",
                "Describe your family. How many people are in your family?"
            ],
            'daily_life': [
                "What did you eat for breakfast today?",
                "Describe your typical day from morning to evening.",
                "What time do you usually wake up and go to sleep?"
            ],
            'preferences': [
                "What is your favorite color and why?",
                "Do you prefer coffee or tea? Why?",
                "What kind of music do you like?"
            ]
        },
        'A2': {
            'past_experiences': [
                "Tell me about your last vacation. Where did you go and what did you do?",
                "Describe a memorable day from your childhood.",
                "What was your favorite subject in school and why?"
            ],
            'opinions': [
                "What do you think about social media? Is it good or bad?",
                "Do you prefer living in a city or in the countryside? Explain your choice.",
                "What is the most important quality in a friend?"
            ],
            'future_plans': [
                "What are your plans for next weekend?",
                "Where would you like to travel in the future and why?",
                "What job would you like to have in 5 years?"
            ]
        },
        'B1': {
            'complex_situations': [
                "Describe a time when you had to solve a difficult problem. How did you handle it?",
                "If you could change one thing about your city, what would it be and why?",
                "Explain the advantages and disadvantages of learning languages online."
            ],
            'abstract_topics': [
                "What does success mean to you? How do you measure it?",
                "Do you think technology makes our lives better or worse? Explain your opinion.",
                "How has your country changed in the last 10 years?"
            ],
            'hypothetical': [
                "If you could meet any person from history, who would it be and what would you ask them?",
                "What would you do if you won a million dollars?",
                "If you could have any superpower, what would it be and how would you use it?"
            ]
        },
        'B2': {
            'analytical': [
                "Analyze the impact of globalization on local cultures. What are the benefits and drawbacks?",
                "Compare the education system in your country with other countries you know about.",
                "Discuss the role of artificial intelligence in modern society. What opportunities and risks do you see?"
            ],
            'argumentative': [
                "Some people believe that social media should be regulated by governments. What is your position on this issue?",
                "Argue for or against the statement: 'Money is the most important factor in job satisfaction.'",
                "Should countries prioritize economic growth or environmental protection? Defend your viewpoint."
            ],
            'complex_narrative': [
                "Describe a situation where you had to adapt to a completely new environment. What challenges did you face and how did you overcome them?",
                "Tell me about a time when your opinion about something important changed. What caused this change?",
                "Explain a complex process or system that you understand well to someone who knows nothing about it."
            ]
        }
    }
    
    def generate_question(self, level_estimate: str, question_number: int, language_pair: LanguagePair) -> AssessmentQuestion:
        """Generate an assessment question based on current level estimate.
        
        Args:
            level_estimate: Current estimated proficiency level
            question_number: Question sequence number
            language_pair: Language pair for assessment
            
        Returns:
            AssessmentQuestion: Generated question
        """
        # Select appropriate level questions
        if level_estimate in ['A1', 'A2']:
            question_level = level_estimate
        elif level_estimate in ['B1', 'B2']:
            question_level = level_estimate
        else:
            # Default to A2 for unknown levels
            question_level = 'A2'
        
        # Get questions for the level
        level_questions = self.QUESTION_TEMPLATES.get(question_level, self.QUESTION_TEMPLATES['A2'])
        
        # Select category based on question number
        categories = list(level_questions.keys())
        category = categories[question_number % len(categories)]
        
        # Select question from category
        questions = level_questions[category]
        question_content = questions[question_number % len(questions)]
        
        # Create question ID
        question_id = f"{question_level}_{category}_{question_number}"
        
        # Add language-specific instructions
        target_lang = language_pair.target_language.upper()
        lang_names = {
            'EN': 'English', 'ES': 'Spanish', 'FR': 'French', 'DE': 'German',
            'IT': 'Italian', 'PT': 'Portuguese', 'TR': 'Turkish', 'AR': 'Arabic'
        }
        target_lang_name = lang_names.get(target_lang, 'the target language')
        
        instructions = f"Please answer in {target_lang_name}. Take your time and answer as completely as you can."
        
        return AssessmentQuestion(
            id=question_id,
            content=question_content,
            expected_level=question_level,
            category=category,
            instructions=instructions
        )


class LevelAssessmentUseCase:
    """Use case for AI-powered level assessment system."""
    
    def __init__(
        self,
        assessment_repository: AssessmentSessionRepositoryInterface,
        user_repository: UserRepositoryInterface,
        llm_service: LLMServiceInterface,
        options: Optional[LevelAssessmentOptions] = None
    ):
        """Initialize level assessment use case.
        
        Args:
            assessment_repository: Assessment session repository
            user_repository: User repository
            llm_service: LLM service for AI evaluation
            options: Assessment configuration options
        """
        self.assessment_repository = assessment_repository
        self.user_repository = user_repository
        self.llm_service = llm_service
        self.options = options or LevelAssessmentOptions()
        self.question_generator = AssessmentQuestionGenerator()
    
    async def start_assessment(
        self, 
        user_id: uuid.UUID, 
        language_pair: LanguagePair
    ) -> Tuple[AssessmentSession, AssessmentQuestion]:
        """Start a new level assessment session.
        
        Args:
            user_id: ID of the user taking the assessment
            language_pair: Language pair for assessment
            
        Returns:
            Tuple of (AssessmentSession, first AssessmentQuestion)
            
        Raises:
            LevelAssessmentError: If assessment cannot be started
        """
        try:
            # Validate user exists
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise LevelAssessmentError(f"User not found: {user_id}")
            
            # Check for existing active assessment
            existing_session = await self.assessment_repository.get_active_by_user_id(user_id)
            if existing_session:
                # Check if session is expired
                if self._is_session_expired(existing_session):
                    await self._expire_session(existing_session.id)
                else:
                    raise LevelAssessmentError("User already has an active assessment session")
            
            # Create new assessment session
            session_id = uuid.uuid4()
            session = AssessmentSession(
                id=session_id,
                user_id=user_id,
                language_pair=language_pair,
                current_question=0,
                responses=[],
                estimated_level=None,
                status=AssessmentStatus.ACTIVE,
                created_at=datetime.utcnow()
            )
            
            # Save session
            created_session = await self.assessment_repository.create(session)
            
            # Generate first question
            first_question = self.question_generator.generate_question(
                level_estimate='A2',  # Start with A2 as baseline
                question_number=0,
                language_pair=language_pair
            )
            
            logger.info(f"Started assessment session {session_id} for user {user_id}")
            return created_session, first_question
            
        except ValidationError as e:
            raise LevelAssessmentError(f"Validation error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to start assessment: {e}")
            raise LevelAssessmentError(f"Failed to start assessment: {str(e)}")
    
    async def process_assessment_response(
        self, 
        session_id: uuid.UUID, 
        user_response: str
    ) -> Tuple[AssessmentResult, Optional[AssessmentQuestion]]:
        """Process a user's response to an assessment question.
        
        Args:
            session_id: ID of the assessment session
            user_response: User's response to the current question
            
        Returns:
            Tuple of (AssessmentResult, next AssessmentQuestion or None if complete)
            
        Raises:
            LevelAssessmentError: If response cannot be processed
        """
        try:
            # Get assessment session
            session = await self.assessment_repository.get_by_id(session_id)
            if not session:
                raise AssessmentSessionNotFoundError(f"Assessment session not found: {session_id}")
            
            # Validate session state
            if session.status != AssessmentStatus.ACTIVE:
                raise AssessmentAlreadyCompletedError("Assessment session is not active")
            
            if self._is_session_expired(session):
                await self._expire_session(session_id)
                raise AssessmentExpiredError("Assessment session has expired")
            
            # Generate current question for evaluation context
            current_question = self.question_generator.generate_question(
                level_estimate=session.estimated_level or 'A2',
                question_number=session.current_question,
                language_pair=session.language_pair
            )
            
            # Evaluate response using AI
            evaluation_result = await self._evaluate_response(
                question=current_question,
                user_response=user_response,
                language_pair=session.language_pair,
                previous_responses=session.responses
            )
            
            # Create assessment response
            assessment_response = AssessmentResponse(
                question_id=current_question.id,
                user_response=user_response,
                ai_evaluation=evaluation_result.ai_evaluation,
                complexity_score=evaluation_result.complexity_score,
                accuracy_score=evaluation_result.accuracy_score,
                fluency_score=evaluation_result.fluency_score,
                created_at=datetime.utcnow()
            )
            
            # Add response to session
            session.add_response(assessment_response)
            
            # Update estimated level based on all responses
            new_estimated_level = self._calculate_estimated_level(session.responses)
            session.update_estimated_level(new_estimated_level)
            
            # Save updated session
            await self.assessment_repository.update(session)
            
            # Determine if assessment should continue
            next_question = None
            if self._should_continue_assessment(session):
                next_question = self.question_generator.generate_question(
                    level_estimate=new_estimated_level,
                    question_number=session.current_question,
                    language_pair=session.language_pair
                )
            
            logger.info(f"Processed response for session {session_id}, estimated level: {new_estimated_level}")
            return evaluation_result, next_question
            
        except ValidationError as e:
            raise LevelAssessmentError(f"Validation error: {str(e)}")
        except LevelAssessmentError:
            raise
        except Exception as e:
            logger.error(f"Failed to process assessment response: {e}")
            raise LevelAssessmentError(f"Failed to process response: {str(e)}")
    
    async def complete_assessment(self, session_id: uuid.UUID) -> str:
        """Complete an assessment session and return final level.
        
        Args:
            session_id: ID of the assessment session
            
        Returns:
            Final proficiency level (A1, A2, B1, B2, C1, C2)
            
        Raises:
            LevelAssessmentError: If assessment cannot be completed
        """
        try:
            # Get assessment session
            session = await self.assessment_repository.get_by_id(session_id)
            if not session:
                raise AssessmentSessionNotFoundError(f"Assessment session not found: {session_id}")
            
            if session.status != AssessmentStatus.ACTIVE:
                raise AssessmentAlreadyCompletedError("Assessment session is not active")
            
            # Calculate final level
            final_level = self._calculate_final_level(session.responses)
            
            # Complete the session
            session.complete_assessment(final_level)
            await self.assessment_repository.update(session)
            
            # Update user's assessed level
            user = await self.user_repository.get_by_id(session.user_id)
            if user:
                user.assessed_level = final_level
                user.assessment_date = datetime.utcnow()
                await self.user_repository.update(user)
            
            logger.info(f"Completed assessment session {session_id} with final level: {final_level}")
            return final_level
            
        except ValidationError as e:
            raise LevelAssessmentError(f"Validation error: {str(e)}")
        except LevelAssessmentError:
            raise
        except Exception as e:
            logger.error(f"Failed to complete assessment: {e}")
            raise LevelAssessmentError(f"Failed to complete assessment: {str(e)}")
    
    async def get_assessment_status(self, session_id: uuid.UUID) -> Dict:
        """Get current status of an assessment session.
        
        Args:
            session_id: ID of the assessment session
            
        Returns:
            Dictionary with assessment status information
            
        Raises:
            LevelAssessmentError: If session cannot be found
        """
        try:
            session = await self.assessment_repository.get_by_id(session_id)
            if not session:
                raise AssessmentSessionNotFoundError(f"Assessment session not found: {session_id}")
            
            # Calculate progress
            progress_percentage = min(
                (len(session.responses) / self.options.max_questions) * 100,
                100.0
            )
            
            # Get average scores
            avg_scores = session.get_average_scores()
            
            return {
                'session_id': str(session.id),
                'user_id': str(session.user_id),
                'status': session.status.value,
                'current_question': session.current_question,
                'total_responses': len(session.responses),
                'estimated_level': session.estimated_level,
                'progress_percentage': round(progress_percentage, 1),
                'average_scores': avg_scores,
                'created_at': session.created_at.isoformat(),
                'is_expired': self._is_session_expired(session),
                'language_pair': {
                    'native_language': session.language_pair.native_language,
                    'target_language': session.language_pair.target_language
                }
            }
            
        except LevelAssessmentError:
            raise
        except Exception as e:
            logger.error(f"Failed to get assessment status: {e}")
            raise LevelAssessmentError(f"Failed to get status: {str(e)}")
    
    async def cancel_assessment(self, session_id: uuid.UUID) -> bool:
        """Cancel an active assessment session.
        
        Args:
            session_id: ID of the assessment session
            
        Returns:
            True if session was cancelled, False if not found
            
        Raises:
            LevelAssessmentError: If cancellation fails
        """
        try:
            session = await self.assessment_repository.get_by_id(session_id)
            if not session:
                return False
            
            if session.status == AssessmentStatus.ACTIVE:
                session.cancel_assessment()
                await self.assessment_repository.update(session)
                logger.info(f"Cancelled assessment session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel assessment: {e}")
            raise LevelAssessmentError(f"Failed to cancel assessment: {str(e)}")
    
    async def _evaluate_response(
        self,
        question: AssessmentQuestion,
        user_response: str,
        language_pair: LanguagePair,
        previous_responses: List[AssessmentResponse]
    ) -> AssessmentResult:
        """Evaluate user response using AI.
        
        Args:
            question: The assessment question
            user_response: User's response
            language_pair: Language pair for assessment
            previous_responses: Previous responses for context
            
        Returns:
            AssessmentResult with evaluation scores
        """
        try:
            # Build evaluation prompt
            evaluation_prompt = self._build_evaluation_prompt(
                question, user_response, language_pair, previous_responses
            )
            
            # Create LLM request
            messages = [
                {"role": "system", "content": evaluation_prompt},
                {"role": "user", "content": f"Question: {question.content}\n\nUser Response: {user_response}"}
            ]
            
            llm_request = LLMRequest(
                messages=messages,
                model=LLMModel.GPT_4,  # Use GPT-4 for more accurate evaluation
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent evaluation
                user_id=str(language_pair.native_language),
                session_id=question.id,
                prompt_version="assessment_v1.0"
            )
            
            # Get AI evaluation
            response = await self.llm_service.generate_response(llm_request)
            
            # Parse evaluation response
            evaluation_data = self._parse_evaluation_response(response.content)
            
            return AssessmentResult(
                question_id=question.id,
                user_response=user_response,
                ai_evaluation=response.content,
                complexity_score=evaluation_data['complexity_score'],
                accuracy_score=evaluation_data['accuracy_score'],
                fluency_score=evaluation_data['fluency_score'],
                estimated_level=evaluation_data['estimated_level'],
                feedback=evaluation_data.get('feedback')
            )
            
        except LLMServiceError as e:
            logger.error(f"LLM service error during evaluation: {e}")
            # Fallback to basic evaluation
            return self._fallback_evaluation(question, user_response)
        except Exception as e:
            logger.error(f"Failed to evaluate response: {e}")
            raise LevelAssessmentError(f"Failed to evaluate response: {str(e)}")
    
    def _build_evaluation_prompt(
        self,
        question: AssessmentQuestion,
        user_response: str,
        language_pair: LanguagePair,
        previous_responses: List[AssessmentResponse]
    ) -> str:
        """Build evaluation prompt for AI assessment."""
        
        target_lang = language_pair.target_language.upper()
        native_lang = language_pair.native_language.upper()
        
        lang_names = {
            'EN': 'English', 'ES': 'Spanish', 'FR': 'French', 'DE': 'German',
            'IT': 'Italian', 'PT': 'Portuguese', 'TR': 'Turkish', 'AR': 'Arabic'
        }
        
        target_lang_name = lang_names.get(target_lang, 'the target language')
        native_lang_name = lang_names.get(native_lang, 'the native language')
        
        # Build context from previous responses
        context = ""
        if previous_responses:
            avg_scores = {
                'complexity': sum(r.complexity_score for r in previous_responses) / len(previous_responses),
                'accuracy': sum(r.accuracy_score for r in previous_responses) / len(previous_responses),
                'fluency': sum(r.fluency_score for r in previous_responses) / len(previous_responses)
            }
            context = f"\nPrevious response averages: Complexity: {avg_scores['complexity']:.2f}, Accuracy: {avg_scores['accuracy']:.2f}, Fluency: {avg_scores['fluency']:.2f}"
        
        return f"""You are an expert language assessment evaluator for {target_lang_name} proficiency. 
You are evaluating a {native_lang_name} speaker's {target_lang_name} response to determine their proficiency level.

CEFR Levels:
- A1: Basic user, simple phrases, present tense, basic vocabulary
- A2: Elementary, simple sentences, past/future tense, everyday topics
- B1: Intermediate, connected speech, opinions, complex sentences
- B2: Upper-intermediate, detailed descriptions, abstract topics, nuanced expression
- C1: Advanced, fluent expression, complex ideas, sophisticated vocabulary
- C2: Proficient, native-like fluency, subtle meanings, complex argumentation

Evaluate the response on three dimensions (0.0-1.0 scale):

1. COMPLEXITY: Sentence structure, grammar complexity, vocabulary sophistication
   - 0.0-0.3: Simple words, basic sentences, elementary grammar
   - 0.4-0.6: Some complex sentences, intermediate vocabulary
   - 0.7-1.0: Complex structures, advanced vocabulary, sophisticated expression

2. ACCURACY: Grammar correctness, word choice, language mechanics
   - 0.0-0.3: Many errors that impede understanding
   - 0.4-0.6: Some errors but meaning is clear
   - 0.7-1.0: Few or no errors, natural language use

3. FLUENCY: Natural flow, coherence, completeness of response
   - 0.0-0.3: Fragmented, incomplete thoughts
   - 0.4-0.6: Understandable but some hesitation/awkwardness
   - 0.7-1.0: Natural, coherent, complete expression

Expected level for this question: {question.expected_level}
Question category: {question.category}{context}

Respond in this EXACT format:
COMPLEXITY_SCORE: [0.0-1.0]
ACCURACY_SCORE: [0.0-1.0]
FLUENCY_SCORE: [0.0-1.0]
ESTIMATED_LEVEL: [A1/A2/B1/B2/C1/C2]
FEEDBACK: [Brief explanation of the assessment]"""
    
    def _parse_evaluation_response(self, response_content: str) -> Dict:
        """Parse AI evaluation response into structured data."""
        try:
            lines = response_content.strip().split('\n')
            result = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('COMPLEXITY_SCORE:'):
                    result['complexity_score'] = float(line.split(':', 1)[1].strip())
                elif line.startswith('ACCURACY_SCORE:'):
                    result['accuracy_score'] = float(line.split(':', 1)[1].strip())
                elif line.startswith('FLUENCY_SCORE:'):
                    result['fluency_score'] = float(line.split(':', 1)[1].strip())
                elif line.startswith('ESTIMATED_LEVEL:'):
                    result['estimated_level'] = line.split(':', 1)[1].strip()
                elif line.startswith('FEEDBACK:'):
                    result['feedback'] = line.split(':', 1)[1].strip()
            
            # Validate required fields
            required_fields = ['complexity_score', 'accuracy_score', 'fluency_score', 'estimated_level']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate score ranges
            for score_field in ['complexity_score', 'accuracy_score', 'fluency_score']:
                score = result[score_field]
                if not (0.0 <= score <= 1.0):
                    result[score_field] = max(0.0, min(1.0, score))  # Clamp to valid range
            
            # Validate level
            valid_levels = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
            if result['estimated_level'] not in valid_levels:
                result['estimated_level'] = 'A2'  # Default fallback
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            # Return fallback evaluation
            return {
                'complexity_score': 0.5,
                'accuracy_score': 0.5,
                'fluency_score': 0.5,
                'estimated_level': 'A2',
                'feedback': 'Unable to parse AI evaluation'
            }
    
    def _fallback_evaluation(self, question: AssessmentQuestion, user_response: str) -> AssessmentResult:
        """Provide fallback evaluation when AI service fails."""
        # Simple heuristic-based evaluation
        response_length = len(user_response.split())
        
        # Basic scoring based on response length and expected level
        if response_length < 5:
            complexity_score = 0.2
            fluency_score = 0.3
        elif response_length < 15:
            complexity_score = 0.4
            fluency_score = 0.5
        elif response_length < 30:
            complexity_score = 0.6
            fluency_score = 0.7
        else:
            complexity_score = 0.8
            fluency_score = 0.8
        
        # Assume reasonable accuracy for fallback
        accuracy_score = 0.6
        
        return AssessmentResult(
            question_id=question.id,
            user_response=user_response,
            ai_evaluation="Fallback evaluation due to AI service unavailability",
            complexity_score=complexity_score,
            accuracy_score=accuracy_score,
            fluency_score=fluency_score,
            estimated_level=question.expected_level,
            feedback="Assessment completed with basic evaluation"
        )
    
    def _calculate_estimated_level(self, responses: List[AssessmentResponse]) -> str:
        """Calculate estimated proficiency level based on responses."""
        if not responses:
            return 'A2'
        
        # Calculate average scores
        avg_complexity = sum(r.complexity_score for r in responses) / len(responses)
        avg_accuracy = sum(r.accuracy_score for r in responses) / len(responses)
        avg_fluency = sum(r.fluency_score for r in responses) / len(responses)
        
        # Overall score
        overall_score = (avg_complexity + avg_accuracy + avg_fluency) / 3.0
        
        # Map score to CEFR level
        if overall_score < 0.25:
            return 'A1'
        elif overall_score < 0.45:
            return 'A2'
        elif overall_score < 0.65:
            return 'B1'
        elif overall_score < 0.85:
            return 'B2'
        elif overall_score < 0.95:
            return 'C1'
        else:
            return 'C2'
    
    def _calculate_final_level(self, responses: List[AssessmentResponse]) -> str:
        """Calculate final proficiency level with confidence weighting."""
        if not responses:
            return 'A2'
        
        # Use more sophisticated calculation for final level
        recent_responses = responses[-3:] if len(responses) >= 3 else responses
        
        # Weight recent responses more heavily
        total_weight = 0
        weighted_complexity = 0
        weighted_accuracy = 0
        weighted_fluency = 0
        
        for i, response in enumerate(recent_responses):
            weight = i + 1  # More recent responses get higher weight
            total_weight += weight
            weighted_complexity += response.complexity_score * weight
            weighted_accuracy += response.accuracy_score * weight
            weighted_fluency += response.fluency_score * weight
        
        avg_complexity = weighted_complexity / total_weight
        avg_accuracy = weighted_accuracy / total_weight
        avg_fluency = weighted_fluency / total_weight
        
        # Overall score with accuracy weighted more heavily
        overall_score = (avg_complexity * 0.3 + avg_accuracy * 0.4 + avg_fluency * 0.3)
        
        # Map to CEFR level with stricter thresholds for final assessment
        if overall_score < 0.3:
            return 'A1'
        elif overall_score < 0.5:
            return 'A2'
        elif overall_score < 0.7:
            return 'B1'
        elif overall_score < 0.85:
            return 'B2'
        elif overall_score < 0.95:
            return 'C1'
        else:
            return 'C2'
    
    def _should_continue_assessment(self, session: AssessmentSession) -> bool:
        """Determine if assessment should continue based on current state."""
        response_count = len(session.responses)
        
        # Always continue if below minimum questions
        if response_count < self.options.min_questions:
            return True
        
        # Stop if reached maximum questions
        if response_count >= self.options.max_questions:
            return False
        
        # For adaptive questioning, check confidence level
        if self.options.adaptive_questioning and response_count >= 3:
            # Calculate score variance to determine confidence
            recent_scores = [r.get_overall_score() for r in session.responses[-3:]]
            score_variance = sum((s - sum(recent_scores)/len(recent_scores))**2 for s in recent_scores) / len(recent_scores)
            
            # If variance is low (consistent scores), we can be confident
            if score_variance < 0.05:  # Low variance threshold
                return False
        
        return True
    
    def _is_session_expired(self, session: AssessmentSession) -> bool:
        """Check if assessment session has expired."""
        if session.status != AssessmentStatus.ACTIVE:
            return False
        
        expiry_time = session.created_at + timedelta(hours=self.options.session_timeout_hours)
        return datetime.utcnow() > expiry_time
    
    async def _expire_session(self, session_id: uuid.UUID) -> None:
        """Mark session as expired."""
        try:
            await self.assessment_repository.update_status(session_id, AssessmentStatus.EXPIRED)
            logger.info(f"Expired assessment session {session_id}")
        except Exception as e:
            logger.error(f"Failed to expire session {session_id}: {e}")