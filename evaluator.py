from typing import Dict, Any, List, Optional, Tuple
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
import json
import logging
from datetime import datetime

class Evaluator:
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.1-8b-instant"):
        """
        Initialize the Evaluator agent.
        
        Args:
            groq_api_key: API key for Groq
            model_name: Name of the Groq model to use
        """
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)
        self.logger = logging.getLogger(__name__)
    
    def evaluate_quiz_answers(self, evaluation_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate student quiz answers and provide detailed feedback.
        
        Args:
            evaluation_request: Dictionary containing:
                - student_id: Student ID
                - quiz_id: Quiz identifier
                - questions: List of quiz questions
                - student_answers: List of student's answers
                - time_taken: Time taken to complete quiz (in seconds)
                - topic: Quiz topic
                - difficulty_level: Quiz difficulty level
                
        Returns:
            Dictionary containing evaluation results
        """
        # Extract parameters
        student_id = evaluation_request.get('student_id')
        quiz_id = evaluation_request.get('quiz_id')
        questions = evaluation_request.get('questions', [])
        student_answers = evaluation_request.get('student_answers', [])
        time_taken = evaluation_request.get('time_taken', 0)
        topic = evaluation_request.get('topic')
        difficulty_level = evaluation_request.get('difficulty_level', 'Intermediate')
        
        # Perform basic evaluation
        basic_evaluation = self._perform_basic_evaluation(questions, student_answers)
        
        # Create detailed evaluation prompt for LLM
        evaluation_prompt = self._create_evaluation_prompt(
            questions, student_answers, basic_evaluation, topic, difficulty_level
        )
        
        try:
            # Get detailed LLM evaluation
            response = self.llm.invoke([HumanMessage(content=evaluation_prompt)])
            llm_evaluation = response.content
            
            # Parse LLM evaluation
            detailed_evaluation = self._parse_llm_evaluation(llm_evaluation)
            
            # Combine evaluations
            final_evaluation = {
                'student_id': student_id,
                'quiz_id': quiz_id,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'evaluated_at': datetime.utcnow().isoformat(),
                'time_taken': time_taken,
                'total_questions': len(questions),
                'correct_answers': basic_evaluation['correct_count'],
                'incorrect_answers': basic_evaluation['incorrect_count'],
                'score_percentage': basic_evaluation['score_percentage'],
                'grade': self._calculate_grade(basic_evaluation['score_percentage']),
                'passed': basic_evaluation['score_percentage'] >= self._get_passing_score(difficulty_level),
                'question_analysis': basic_evaluation['question_analysis'],
                'detailed_feedback': detailed_evaluation.get('detailed_feedback', ''),
                'strengths': detailed_evaluation.get('strengths', []),
                'improvement_areas': detailed_evaluation.get('improvement_areas', []),
                'recommendations': detailed_evaluation.get('recommendations', []),
                'learning_insights': detailed_evaluation.get('learning_insights', {}),
                'next_steps': detailed_evaluation.get('next_steps', []),
                'performance_trend': detailed_evaluation.get('performance_trend', 'stable'),
                'difficulty_adjustment': self._recommend_difficulty_adjustment(
                    basic_evaluation['score_percentage'], difficulty_level
                )
            }
            
            return final_evaluation
            
        except Exception as e:
            self.logger.error(f"Error in evaluation: {str(e)}")
            # Return basic evaluation without LLM insights
            return {
                'student_id': student_id,
                'quiz_id': quiz_id,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'evaluated_at': datetime.utcnow().isoformat(),
                'time_taken': time_taken,
                'total_questions': len(questions),
                'correct_answers': basic_evaluation['correct_count'],
                'incorrect_answers': basic_evaluation['incorrect_count'],
                'score_percentage': basic_evaluation['score_percentage'],
                'grade': self._calculate_grade(basic_evaluation['score_percentage']),
                'passed': basic_evaluation['score_percentage'] >= self._get_passing_score(difficulty_level),
                'question_analysis': basic_evaluation['question_analysis'],
                'error': str(e)
            }
    
    def _perform_basic_evaluation(self, questions: List[Dict], 
                                 student_answers: List[str]) -> Dict[str, Any]:
        """
        Perform basic evaluation by comparing answers with correct answers.
        
        Args:
            questions: List of quiz questions
            student_answers: List of student's answers
            
        Returns:
            Basic evaluation results
        """
        correct_count = 0
        incorrect_count = 0
        question_analysis = []
        
        for i, question in enumerate(questions):
            if i >= len(student_answers):
                # Student didn't answer this question
                question_analysis.append({
                    'question_id': question.get('id', i + 1),
                    'student_answer': '',
                    'correct_answer': question.get('correct_answer', ''),
                    'is_correct': False,
                    'question_text': question.get('question', ''),
                    'explanation': question.get('explanation', ''),
                    'status': 'not_answered'
                })
                incorrect_count += 1
                continue
            
            student_answer = student_answers[i].strip().upper()
            correct_answer = question.get('correct_answer', '').strip().upper()
            
            is_correct = student_answer == correct_answer
            
            if is_correct:
                correct_count += 1
                status = 'correct'
            else:
                incorrect_count += 1
                status = 'incorrect'
            
            question_analysis.append({
                'question_id': question.get('id', i + 1),
                'student_answer': student_answers[i],
                'correct_answer': question.get('correct_answer', ''),
                'is_correct': is_correct,
                'question_text': question.get('question', ''),
                'explanation': question.get('explanation', ''),
                'difficulty': question.get('difficulty', 'medium'),
                'cognitive_level': question.get('cognitive_level', 'recall'),
                'topic_area': question.get('topic_area', ''),
                'status': status
            })
        
        total_questions = len(questions)
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        return {
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'total_questions': total_questions,
            'score_percentage': score_percentage,
            'question_analysis': question_analysis
        }
    
    def _create_evaluation_prompt(self, questions: List[Dict], student_answers: List[str],
                                 basic_evaluation: Dict[str, Any], topic: str, 
                                 difficulty_level: str) -> str:
        """
        Create a comprehensive prompt for detailed evaluation.
        
        Args:
            questions: List of quiz questions
            student_answers: List of student's answers
            basic_evaluation: Basic evaluation results
            topic: Quiz topic
            difficulty_level: Difficulty level
            
        Returns:
            Formatted prompt string
        """
        # Prepare question details for analysis
        question_details = []
        for i, (question, analysis) in enumerate(zip(questions, basic_evaluation['question_analysis'])):
            question_details.append({
                'question_number': i + 1,
                'question': question.get('question', ''),
                'student_answer': analysis['student_answer'],
                'correct_answer': analysis['correct_answer'],
                'is_correct': analysis['is_correct'],
                'difficulty': question.get('difficulty', 'medium'),
                'cognitive_level': question.get('cognitive_level', 'recall'),
                'topic_area': question.get('topic_area', ''),
                'explanation': question.get('explanation', '')
            })
        
        prompt = f"""
        You are an expert educational evaluator and learning analyst. Analyze the following quiz results and provide comprehensive feedback:

        QUIZ DETAILS:
        - Topic: {topic}
        - Difficulty Level: {difficulty_level}
        - Score: {basic_evaluation['score_percentage']:.1f}%
        - Correct: {basic_evaluation['correct_count']}/{basic_evaluation['total_questions']}

        QUESTION ANALYSIS:
        {json.dumps(question_details, indent=2)}

        TASK:
        Provide a detailed evaluation in JSON format with the following structure:
        {{
            "detailed_feedback": "Overall feedback on performance (100-150 words)",
            "strengths": ["List of 3-5 specific strengths demonstrated"],
            "improvement_areas": ["List of 3-5 specific areas needing improvement"],
            "recommendations": ["List of 3-5 actionable recommendations"],
            "learning_insights": {{
                "cognitive_strengths": ["Types of questions student excels at"],
                "cognitive_challenges": ["Types of questions student struggles with"],
                "topic_mastery": ["Topics well understood"],
                "topic_gaps": ["Topics needing more work"]
            }},
            "next_steps": ["Immediate next steps for improvement"],
            "performance_trend": "improving/stable/declining (based on question patterns)",
            "confidence_level": "high/medium/low (based on answer patterns)"
        }}

        ANALYSIS FOCUS:
        1. Identify patterns in correct vs incorrect answers
        2. Analyze performance by difficulty level and cognitive level
        3. Identify specific knowledge gaps
        4. Recognize learning strengths and build on them
        5. Provide specific, actionable feedback
        6. Consider the difficulty level when evaluating performance
        7. Suggest appropriate next steps for learning

        Consider:
        - Are mistakes due to knowledge gaps or misunderstanding?
        - Does the student struggle with specific question types?
        - Are there patterns in the types of errors made?
        - How does performance vary by topic area?
        - What does this performance indicate about learning stage?

        Return valid JSON that can be parsed.
        """
        
        return prompt
    
    def _parse_llm_evaluation(self, llm_response: str) -> Dict[str, Any]:
        """
        Parse the LLM evaluation response.
        
        Args:
            llm_response: Raw response from LLM
            
        Returns:
            Parsed evaluation dictionary
        """
        try:
            # Try to parse as JSON directly
            if llm_response.strip().startswith('{'):
                return json.loads(llm_response)
            
            # Look for JSON content in the response
            start_idx = llm_response.find('{')
            end_idx = llm_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = llm_response[start_idx:end_idx]
                return json.loads(json_content)
            
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse LLM evaluation as JSON")
        
        # Fallback: extract key information using text parsing
        fallback_evaluation = {
            'detailed_feedback': llm_response[:300] + "..." if len(llm_response) > 300 else llm_response,
            'strengths': [],
            'improvement_areas': [],
            'recommendations': [],
            'learning_insights': {
                'cognitive_strengths': [],
                'cognitive_challenges': [],
                'topic_mastery': [],
                'topic_gaps': []
            },
            'next_steps': [],
            'performance_trend': 'stable',
            'confidence_level': 'medium'
        }
        
        return fallback_evaluation
    
    def _calculate_grade(self, score_percentage: float) -> str:
        """
        Calculate letter grade based on percentage score.
        
        Args:
            score_percentage: Score percentage
            
        Returns:
            Letter grade
        """
        if score_percentage >= 90:
            return 'A'
        elif score_percentage >= 80:
            return 'B'
        elif score_percentage >= 70:
            return 'C'
        elif score_percentage >= 60:
            return 'D'
        else:
            return 'F'
    
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
    
    def _recommend_difficulty_adjustment(self, score_percentage: float, 
                                       current_difficulty: str) -> Dict[str, Any]:
        """
        Recommend difficulty adjustment based on performance.
        
        Args:
            score_percentage: Student's score percentage
            current_difficulty: Current difficulty level
            
        Returns:
            Difficulty adjustment recommendation
        """
        if score_percentage >= 85:
            # Excellent performance - recommend increase
            difficulty_map = {'Beginner': 'Intermediate', 'Intermediate': 'Advanced', 'Advanced': 'Advanced'}
            recommended_difficulty = difficulty_map.get(current_difficulty, 'Advanced')
            action = 'increase'
            reason = 'Excellent performance indicates readiness for more challenging material'
        elif score_percentage >= 60:
            # Good performance - maintain current level
            recommended_difficulty = current_difficulty
            action = 'maintain'
            reason = 'Performance is appropriate for current difficulty level'
        else:
            # Poor performance - recommend decrease
            difficulty_map = {'Advanced': 'Intermediate', 'Intermediate': 'Beginner', 'Beginner': 'Beginner'}
            recommended_difficulty = difficulty_map.get(current_difficulty, 'Beginner')
            action = 'decrease'
            reason = 'Performance suggests need for foundational reinforcement'
        
        return {
            'current_difficulty': current_difficulty,
            'recommended_difficulty': recommended_difficulty,
            'action': action,
            'reason': reason,
            'score_based': score_percentage
        }
    
    def evaluate_assignment(self, assignment_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate student assignment submission.
        
        Args:
            assignment_request: Dictionary containing:
                - student_id: Student ID
                - assignment_id: Assignment ID
                - submission: Student's submission
                - assignment_requirements: Original assignment requirements
                - evaluation_criteria: Assignment evaluation criteria
                
        Returns:
            Assignment evaluation results
        """
        evaluation_prompt = f"""
        Evaluate the following assignment submission:

        ASSIGNMENT REQUIREMENTS:
        {json.dumps(assignment_request.get('assignment_requirements', {}), indent=2)}

        EVALUATION CRITERIA:
        {json.dumps(assignment_request.get('evaluation_criteria', []), indent=2)}

        STUDENT SUBMISSION:
        {assignment_request.get('submission', '')}

        Provide evaluation in JSON format:
        {{
            "score": 0-100,
            "grade": "A-F",
            "feedback": "Overall feedback",
            "strengths": ["List of strengths"],
            "improvements": ["List of improvements"],
            "criteria_scores": [{{"criterion": "Criteria name", "score": 0-100, "feedback": "Feedback"}}],
            "next_steps": ["Recommendations for improvement"]
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=evaluation_prompt)])
            evaluation = json.loads(response.content)
            
            evaluation.update({
                'student_id': assignment_request.get('student_id'),
                'assignment_id': assignment_request.get('assignment_id'),
                'evaluated_at': datetime.utcnow().isoformat()
            })
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating assignment: {str(e)}")
            return {
                'student_id': assignment_request.get('student_id'),
                'assignment_id': assignment_request.get('assignment_id'),
                'error': str(e),
                'score': 0
            }
    
    def generate_performance_report(self, student_id: int, performance_history: List[Dict]) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report for a student.
        
        Args:
            student_id: Student ID
            performance_history: List of past performance records
            
        Returns:
            Comprehensive performance report
        """
        # Calculate performance metrics
        if not performance_history:
            return {
                'student_id': student_id,
                'message': 'No performance history available'
            }
        
        # Calculate trends and patterns
        scores = [p.get('score_percentage', 0) for p in performance_history]
        recent_scores = scores[-5:]  # Last 5 performances
        
        avg_score = sum(scores) / len(scores)
        recent_avg = sum(recent_scores) / len(recent_scores)
        
        # Determine trend
        if len(recent_scores) >= 3:
            if recent_scores[-1] > recent_scores[0]:
                trend = 'improving'
            elif recent_scores[-1] < recent_scores[0]:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'student_id': student_id,
            'generated_at': datetime.utcnow().isoformat(),
            'total_assessments': len(performance_history),
            'overall_average': avg_score,
            'recent_average': recent_avg,
            'trend': trend,
            'best_score': max(scores),
            'worst_score': min(scores),
            'performance_consistency': self._calculate_consistency(scores),
            'topic_performance': self._analyze_topic_performance(performance_history),
            'difficulty_performance': self._analyze_difficulty_performance(performance_history)
        }
    
    def _calculate_consistency(self, scores: List[float]) -> str:
        """Calculate performance consistency."""
        if len(scores) < 2:
            return 'insufficient_data'
        
        variance = max(scores) - min(scores)
        if variance < 15:
            return 'high'
        elif variance < 30:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_topic_performance(self, performance_history: List[Dict]) -> Dict[str, float]:
        """Analyze performance by topic."""
        topic_scores = {}
        
        for performance in performance_history:
            topic = performance.get('topic', 'Unknown')
            score = performance.get('score_percentage', 0)
            
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(score)
        
        # Calculate averages
        topic_averages = {topic: sum(scores) / len(scores) 
                         for topic, scores in topic_scores.items()}
        
        return topic_averages
    
    def _analyze_difficulty_performance(self, performance_history: List[Dict]) -> Dict[str, float]:
        """Analyze performance by difficulty level."""
        difficulty_scores = {}
        
        for performance in performance_history:
            difficulty = performance.get('difficulty_level', 'Intermediate')
            score = performance.get('score_percentage', 0)
            
            if difficulty not in difficulty_scores:
                difficulty_scores[difficulty] = []
            difficulty_scores[difficulty].append(score)
        
        # Calculate averages
        difficulty_averages = {difficulty: sum(scores) / len(scores) 
                              for difficulty, scores in difficulty_scores.items()}
        
        return difficulty_averages
