from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
import json
import logging
import random
from datetime import datetime

class QuizGenerator:
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.1-8b-instant"):
        """
        Initialize the Quiz Generator agent.
        
        Args:
            groq_api_key: API key for Groq
            model_name: Name of the Groq model to use
        """
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)
        self.logger = logging.getLogger(__name__)
    
    def generate_quiz(self, quiz_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a personalized quiz based on student profile and topic.
        
        Args:
            quiz_request: Dictionary containing:
                - student_id: Student ID
                - topic: Topic for the quiz
                - difficulty_level: Difficulty level (Beginner, Intermediate, Advanced)
                - student_stage: Current learning stage
                - question_count: Number of questions (default: 5)
                - question_types: Types of questions (MCQ, true_false, fill_blank)
                - focus_areas: Specific areas to focus on
                - time_limit: Optional time limit in minutes
                
        Returns:
            Dictionary containing generated quiz
        """
        # Extract parameters
        student_id = quiz_request.get('student_id')
        topic = quiz_request.get('topic')
        difficulty_level = quiz_request.get('difficulty_level', 'Intermediate')
        student_stage = quiz_request.get('student_stage', 1)
        question_count = quiz_request.get('question_count', 5)
        question_types = quiz_request.get('question_types', ['MCQ'])
        focus_areas = quiz_request.get('focus_areas', [])
        time_limit = quiz_request.get('time_limit', self._estimate_time_limit(question_count))
        
        # Ensure MCQ is included as default
        if 'MCQ' not in question_types:
            question_types.append('MCQ')
        
        # Create quiz generation prompt
        quiz_prompt = self._create_quiz_prompt(
            topic, difficulty_level, student_stage, question_count,
            question_types, focus_areas, time_limit
        )
        
        try:
            # Generate quiz using LLM
            response = self.llm.invoke([HumanMessage(content=quiz_prompt)])
            generated_quiz = response.content
            
            # Parse and structure the quiz
            structured_quiz = self._parse_quiz(generated_quiz, question_count)
            
            # ALWAYS create fallback questions to ensure quiz works
            if not structured_quiz or len(structured_quiz) < question_count:
                fallback_questions = self._create_fallback_questions(topic, question_count - len(structured_quiz), difficulty_level)
                structured_quiz.extend(fallback_questions)
            
            # Validate and randomize options
            validated_quiz = self._validate_and_randomize_quiz(structured_quiz)
            
            # Add metadata
            final_quiz = {
                'student_id': student_id,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'student_stage': student_stage,
                'generated_at': datetime.utcnow().isoformat(),
                'questions': validated_quiz,
                'total_questions': len(validated_quiz),
                'time_limit': time_limit,
                'question_types': question_types,
                'focus_areas': focus_areas,
                'quiz_id': self._generate_quiz_id(),
                'instructions': self._get_quiz_instructions(difficulty_level),
                'passing_score': self._get_passing_score(difficulty_level)
            }
            
            return final_quiz
            
        except Exception as e:
            self.logger.error(f"Error generating quiz: {str(e)}")
            # ALWAYS return valid quiz even on error
            fallback_questions = self._create_fallback_questions(topic, question_count, difficulty_level)
            return {
                'student_id': student_id,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'error': str(e),
                'questions': fallback_questions,
                'quiz_id': self._generate_quiz_id(),
                'total_questions': len(fallback_questions),
                'time_limit': time_limit,
                'instructions': self._get_quiz_instructions(difficulty_level),
                'passing_score': self._get_passing_score(difficulty_level)
            }
    
    def _create_quiz_prompt(self, topic: str, difficulty_level: str, student_stage: int,
                          question_count: int, question_types: List[str], focus_areas: List[str],
                          time_limit: int) -> str:
        """
        Create a comprehensive prompt for quiz generation.
        
        Args:
            topic: Topic for the quiz
            difficulty_level: Difficulty level
            student_stage: Student's current learning stage
            question_count: Number of questions to generate
            question_types: Types of questions to generate
            focus_areas: Specific areas to focus on
            time_limit: Time limit for the quiz
            
        Returns:
            Formatted prompt string
        """
        # Get difficulty-specific guidelines
        difficulty_guidelines = self._get_quiz_difficulty_guidelines(difficulty_level, student_stage)
        
        # Get question type specifications
        type_specifications = self._get_question_type_specifications(question_types)
        
        prompt = f"""
        You are an expert educational assessment designer. Create a comprehensive quiz with the following specifications:

        TOPIC: {topic}
        DIFFICULTY LEVEL: {difficulty_level}
        STUDENT STAGE: {student_stage}
        QUESTION COUNT: {question_count}
        QUESTION TYPES: {', '.join(question_types)}
        FOCUS AREAS: {', '.join(focus_areas) if focus_areas else 'Comprehensive topic coverage'}
        TIME LIMIT: {time_limit} minutes

        DIFFICULTY GUIDELINES:
        {difficulty_guidelines}

        QUESTION TYPE SPECIFICATIONS:
        {type_specifications}

        REQUIREMENTS:
        1. Generate exactly {question_count} questions
        2. Each question must be appropriate for the specified difficulty level
        3. Include a mix of cognitive levels (recall, application, analysis)
        4. Ensure questions test understanding, not just memorization
        5. Provide clear, unambiguous questions
        6. Include plausible distractors for MCQ questions
        7. Focus on the specified areas if provided

        Generate the quiz in the following JSON format:
        {{
            "questions": [
                {{
                    "id": 1,
                    "type": "MCQ/true_false/fill_blank",
                    "question": "Clear question text",
                    "options": [
                        {{"letter": "A", "text": "Option A text"}},
                        {{"letter": "B", "text": "Option B text"}},
                        {{"letter": "C", "text": "Option C text"}},
                        {{"letter": "D", "text": "Option D text"}}
                    ],
                    "correct_answer": "A",
                    "explanation": "Explanation of why this is correct",
                    "difficulty": "easy/medium/hard",
                    "cognitive_level": "recall/application/analysis",
                    "topic_area": "Specific sub-topic",
                    "hint": "Optional hint for the student"
                }}
            ]
        }}

        For true_false questions, use only A and B options.
        For fill_blank questions, omit the options array and include "blank_answer" field.

        Ensure questions are:
        - Factually accurate
        - Clear and unambiguous
        - Appropriate difficulty
        - Varied in cognitive demand
        - Relevant to learning objectives

        Return valid JSON that can be parsed.
        """
        
        return prompt
    
    def _get_quiz_difficulty_guidelines(self, difficulty_level: str, student_stage: int) -> str:
        """
        Get difficulty-specific guidelines for quiz generation.
        
        Args:
            difficulty_level: Difficulty level
            student_stage: Student's learning stage
            
        Returns:
            Difficulty guidelines string
        """
        guidelines = {
            'Beginner': {
                0: "Focus on basic recall and simple recognition. Use straightforward language. Include visual cues where possible.",
                1: "Include basic application and simple problem-solving. Use familiar contexts and examples."
            },
            'Intermediate': {
                1: "Balance recall with application and analysis. Include multi-step problems and case-based scenarios.",
                2: "Emphasize application and analysis. Include complex problems requiring synthesis of concepts."
            },
            'Advanced': {
                2: "Focus on analysis, evaluation, and creation. Include complex scenarios and open-ended problems.",
                3: "Emphasize critical thinking and problem-solving. Include real-world applications and novel situations."
            }
        }
        
        return guidelines.get(difficulty_level, {}).get(student_stage, 
            "Adapt question complexity based on the difficulty level and student's current stage.")
    
    def _get_question_type_specifications(self, question_types: List[str]) -> str:
        """
        Get specifications for different question types.
        
        Args:
            question_types: List of question types
            
        Returns:
            Question type specifications string
        """
        specifications = {
            'MCQ': "Multiple choice questions with 4 options (A, B, C, D). Include one correct answer and 3 plausible distractors.",
            'true_false': "True or false questions with clear statements that can be definitively evaluated.",
            'fill_blank': "Fill-in-the-blank questions with specific, short answers. Include context clues."
        }
        
        return '\n'.join([f"- {qtype}: {specifications.get(qtype, 'Standard question type')}" 
                         for qtype in question_types])
    
    def _parse_quiz(self, generated_quiz: str, expected_count: int) -> List[Dict[str, Any]]:
        """
        Parse the generated quiz from LLM response.
        
        Args:
            generated_quiz: Raw quiz from LLM
            expected_count: Expected number of questions
            
        Returns:
            List of structured question dictionaries
        """
        try:
            # Try to parse as JSON directly
            if generated_quiz.strip().startswith('{'):
                data = json.loads(generated_quiz)
                if 'questions' in data:
                    return data['questions']
                return [data]  # Single question
            
            # Look for JSON content in the response
            start_idx = generated_quiz.find('{')
            end_idx = generated_quiz.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = generated_quiz[start_idx:end_idx]
                data = json.loads(json_content)
                if 'questions' in data:
                    return data['questions']
                return [data]
            
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse quiz as JSON")
        
        # Fallback: create basic question structure from text
        fallback_questions = []
        lines = generated_quiz.split('\n')
        
        for i, line in enumerate(lines[:expected_count]):
            if line.strip():
                fallback_questions.append({
                    'id': i + 1,
                    'type': 'MCQ',
                    'question': line.strip()[:200],
                    'options': [
                        {'letter': 'A', 'text': 'Option A'},
                        {'letter': 'B', 'text': 'Option B'},
                        {'letter': 'C', 'text': 'Option C'},
                        {'letter': 'D', 'text': 'Option D'}
                    ],
                    'correct_answer': 'A',
                    'explanation': 'Please review the material to determine the correct answer.',
                    'difficulty': 'medium',
                    'cognitive_level': 'recall',
                    'topic_area': 'General',
                    'hint': ''
                })
        
        return fallback_questions
    
    def _create_fallback_questions(self, topic: str, question_count: int, difficulty_level: str) -> List[Dict[str, Any]]:
        """Create fallback questions when LLM generation fails."""
        fallback_questions = []
        
        for i in range(question_count):
            fallback_questions.append({
                'id': i + 1,
                'type': 'MCQ',
                'question': f"Question {i+1} about {topic} - {difficulty_level} level",
                'options': [
                    {'letter': 'A', 'text': f'Option A for question {i+1}'},
                    {'letter': 'B', 'text': f'Option B for question {i+1}'},
                    {'letter': 'C', 'text': f'Option C for question {i+1}'},
                    {'letter': 'D', 'text': f'Option D for question {i+1}'}
                ],
                'correct_answer': 'A',
                'explanation': 'This is a fallback question. Please review the learning material.',
                'difficulty': difficulty_level,
                'cognitive_level': 'recall',
                'topic_area': topic,
                'hint': 'Review the learning content for this topic.'
            })
        
        return fallback_questions
    
    def _validate_and_randomize_quiz(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate quiz questions and randomize option order.
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Validated and randomized questions
        """
        validated_questions = []
        
        for i, question in enumerate(questions):
            # Ensure required fields
            validated_question = {
                'id': question.get('id', i + 1),
                'type': question.get('type', 'MCQ'),
                'question': question.get('question', ''),
                'options': question.get('options', []),
                'correct_answer': question.get('correct_answer', ''),
                'explanation': question.get('explanation', ''),
                'difficulty': question.get('difficulty', 'medium'),
                'cognitive_level': question.get('cognitive_level', 'recall'),
                'topic_area': question.get('topic_area', 'General'),
                'hint': question.get('hint', '')
            }
            
            # For MCQ questions, randomize options while tracking correct answer
            if validated_question['type'] == 'MCQ' and len(validated_question['options']) >= 2:
                options = validated_question['options']
                correct_letter = validated_question['correct_answer']
                
                # Find correct option
                correct_option = None
                for opt in options:
                    if opt['letter'] == correct_letter:
                        correct_option = opt.copy()
                        break
                
                if correct_option:
                    # Randomize options
                    random.shuffle(options)
                    
                    # Update correct answer letter
                    for i, opt in enumerate(options):
                        if opt['text'] == correct_option['text']:
                            validated_question['correct_answer'] = opt['letter']
                            break
                    
                    validated_question['options'] = options
            
            validated_questions.append(validated_question)
        
        return validated_questions
    
    def _estimate_time_limit(self, question_count: int) -> int:
        """
        Estimate appropriate time limit based on question count.
        
        Args:
            question_count: Number of questions
            
        Returns:
            Time limit in minutes
        """
        # Average 2 minutes per question
        return max(5, question_count * 2)
    
    def _generate_quiz_id(self) -> str:
        """Generate a unique quiz ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_quiz_instructions(self, difficulty_level: str) -> str:
        """
        Get appropriate instructions based on difficulty level.
        
        Args:
            difficulty_level: Difficulty level
            
        Returns:
            Instructions string
        """
        instructions = {
            'Beginner': "Read each question carefully. Choose the best answer from the options provided. Take your time and think through each option.",
            'Intermediate': "Analyze each question thoroughly. Apply your knowledge to select the most appropriate answer. Some questions may require careful consideration.",
            'Advanced': "Evaluate each question critically. Consider all aspects before selecting your answer. Questions may require synthesis of multiple concepts."
        }
        
        return instructions.get(difficulty_level, instructions['Intermediate'])
    
    def _get_passing_score(self, difficulty_level: str) -> int:
        """
        Get passing score percentage based on difficulty level.
        
        Args:
            difficulty_level: Difficulty level
            
        Returns:
            Passing score percentage
        """
        passing_scores = {
            'Beginner': 70,
            'Intermediate': 75,
            'Advanced': 80
        }
        
        return passing_scores.get(difficulty_level, 75)
    
    def generate_adaptive_quiz(self, topic: str, student_performance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an adaptive quiz based on student performance.
        
        Args:
            topic: Topic for the quiz
            student_performance: Student performance data
            
        Returns:
            Adaptive quiz configuration
        """
        performance_score = student_performance.get('score', 50)
        weak_areas = student_performance.get('weak_areas', [])
        
        # Determine difficulty based on performance
        if performance_score >= 80:
            difficulty = 'Advanced'
            question_count = 6
        elif performance_score >= 60:
            difficulty = 'Intermediate'
            question_count = 5
        else:
            difficulty = 'Beginner'
            question_count = 4
        
        # Create adaptive quiz request
        adaptive_request = {
            'student_id': student_performance.get('student_id'),
            'topic': topic,
            'difficulty_level': difficulty,
            'student_stage': student_performance.get('stage', 1),
            'question_count': question_count,
            'focus_areas': weak_areas,
            'question_types': ['MCQ']
        }
        
        return self.generate_quiz(adaptive_request)
    
    def generate_practice_questions(self, topic: str, difficulty_level: str, 
                                  count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate practice questions for a given topic and difficulty level.
        
        Args:
            topic: Topic to generate questions for
            difficulty_level: Difficulty level
            count: Number of questions to generate
            
        Returns:
            List of practice questions
        """
        practice_prompt = f"""
        Generate {count} practice questions for {topic} at {difficulty_level} level.
        
        Focus on reinforcing key concepts and common problem areas.
        Include immediate feedback and explanations.
        
        Format as JSON array of question objects with the same structure as regular quiz questions.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=practice_prompt)])
            questions_data = json.loads(response.content)
            
            if isinstance(questions_data, list):
                return questions_data
            elif isinstance(questions_data, dict) and 'questions' in questions_data:
                return questions_data['questions']
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error generating practice questions: {str(e)}")
            return []
