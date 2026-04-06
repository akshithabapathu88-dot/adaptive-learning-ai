from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
import json
import logging

class StudentAnalyzer:
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.1-8b-instant"):
        """
        Initialize the Student Analyzer agent.
        
        Args:
            groq_api_key: API key for Groq
            model_name: Name of the Groq model to use
        """
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)
        self.logger = logging.getLogger(__name__)
    
    def analyze_student_performance(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze student performance and determine learning stage.
        
        Args:
            student_data: Dictionary containing student information including:
                - student_id: Student ID
                - performance_history: List of past performances
                - current_stage: Current learning stage
                - quiz_results: Recent quiz results
                - weak_topics: List of weak topics
                
        Returns:
            Dictionary containing analysis results
        """
        # Extract relevant information
        student_id = student_data.get('student_id')
        current_stage = student_data.get('current_stage', 0)
        performance_history = student_data.get('performance_history', [])
        quiz_results = student_data.get('quiz_results', [])
        weak_topics = student_data.get('weak_topics', [])
        
        # Calculate performance metrics
        avg_score = 0
        if performance_history:
            avg_score = sum(p.get('score', 0) for p in performance_history) / len(performance_history)
        
        recent_quiz_scores = []
        if quiz_results:
            recent_quiz_scores = [q.get('score', 0) for q in quiz_results[-5:]]  # Last 5 quizzes
            recent_avg = sum(recent_quiz_scores) / len(recent_quiz_scores)
        else:
            recent_avg = 0
        
        # Determine learning stage based on performance
        new_stage = self._determine_learning_stage(avg_score, recent_avg, current_stage)
        
        # Identify learning patterns and recommendations
        learning_patterns = self._identify_learning_patterns(performance_history, quiz_results)
        
        # Create analysis prompt for LLM
        analysis_prompt = self._create_analysis_prompt(
            student_id, current_stage, new_stage, avg_score, recent_avg,
            weak_topics, learning_patterns, performance_history
        )
        
        try:
            # Get LLM analysis
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            llm_analysis = response.content
            
            # Parse the LLM response
            analysis_result = self._parse_llm_analysis(llm_analysis)
            
            # Combine with our analysis
            final_analysis = {
                'student_id': student_id,
                'current_stage': current_stage,
                'recommended_stage': new_stage,
                'average_score': avg_score,
                'recent_average': recent_avg,
                'weak_topics': weak_topics,
                'learning_patterns': learning_patterns,
                'stage_change': new_stage != current_stage,
                'llm_insights': analysis_result,
                'recommendations': analysis_result.get('recommendations', []),
                'improvement_areas': analysis_result.get('improvement_areas', []),
                'strengths': analysis_result.get('strengths', [])
            }
            
            return final_analysis
            
        except Exception as e:
            self.logger.error(f"Error in student analysis: {str(e)}")
            # Return basic analysis without LLM insights
            return {
                'student_id': student_id,
                'current_stage': current_stage,
                'recommended_stage': new_stage,
                'average_score': avg_score,
                'recent_average': recent_avg,
                'weak_topics': weak_topics,
                'learning_patterns': learning_patterns,
                'stage_change': new_stage != current_stage,
                'error': str(e)
            }
    
    def _determine_learning_stage(self, avg_score: float, recent_avg: float, current_stage: int) -> int:
        """
        Determine the appropriate learning stage based on performance.
        
        Args:
            avg_score: Overall average score
            recent_avg: Recent average score
            current_stage: Current learning stage
            
        Returns:
            Recommended learning stage
        """
        # Give more weight to recent performance
        weighted_score = (avg_score * 0.3) + (recent_avg * 0.7)
        
        if weighted_score >= 80:
            # Excellent performance - advance stage
            return max(current_stage + 1, 3)
        elif weighted_score >= 60:
            # Good performance - maintain or slightly advance
            return max(current_stage, 2)
        elif weighted_score >= 40:
            # Average performance - maintain current stage
            return current_stage
        else:
            # Poor performance - go back to fundamentals
            return max(0, current_stage - 1)
    
    def _identify_learning_patterns(self, performance_history: List[Dict], 
                                 quiz_results: List[Dict]) -> Dict[str, Any]:
        """
        Identify learning patterns from student history.
        
        Args:
            performance_history: List of performance records
            quiz_results: List of quiz results
            
        Returns:
            Dictionary containing learning patterns
        """
        patterns = {
            'improvement_trend': 'stable',
            'consistency': 'medium',
            'topic_preferences': [],
            'difficulty_adaptation': 'adaptive'
        }
        
        # Analyze improvement trend
        if len(performance_history) >= 3:
            recent_scores = [p.get('score', 0) for p in performance_history[-3:]]
            if recent_scores[-1] > recent_scores[0]:
                patterns['improvement_trend'] = 'improving'
            elif recent_scores[-1] < recent_scores[0]:
                patterns['improvement_trend'] = 'declining'
        
        # Analyze consistency
        if performance_history:
            scores = [p.get('score', 0) for p in performance_history]
            score_variance = max(scores) - min(scores)
            if score_variance < 20:
                patterns['consistency'] = 'high'
            elif score_variance > 40:
                patterns['consistency'] = 'low'
        
        # Analyze topic preferences
        topic_scores = {}
        for perf in performance_history:
            topic = perf.get('topic', '')
            score = perf.get('score', 0)
            if topic:
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(score)
        
        # Find best and worst performing topics
        topic_averages = {topic: sum(scores) / len(scores) 
                         for topic, scores in topic_scores.items()}
        
        if topic_averages:
            best_topic = max(topic_averages, key=topic_averages.get)
            worst_topic = min(topic_averages, key=topic_averages.get)
            patterns['topic_preferences'] = {
                'strongest': best_topic,
                'weakest': worst_topic,
                'all_topics': topic_averages
            }
        
        return patterns
    
    def _create_analysis_prompt(self, student_id: int, current_stage: int, new_stage: int,
                              avg_score: float, recent_avg: float, weak_topics: List[str],
                              learning_patterns: Dict, performance_history: List[Dict]) -> str:
        """
        Create a comprehensive prompt for LLM analysis.
        
        Args:
            student_id: Student identifier
            current_stage: Current learning stage
            new_stage: Recommended new stage
            avg_score: Average score
            recent_avg: Recent average score
            weak_topics: List of weak topics
            learning_patterns: Learning patterns identified
            performance_history: Performance history
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
        You are an expert educational psychologist and AI learning analyst. Analyze the following student data and provide comprehensive insights.

        STUDENT PROFILE:
        - Student ID: {student_id}
        - Current Learning Stage: {current_stage}
        - Recommended New Stage: {new_stage}
        - Overall Average Score: {avg_score:.2f}%
        - Recent Average Score: {recent_avg:.2f}%
        - Weak Topics: {', '.join(weak_topics) if weak_topics else 'None identified'}

        LEARNING PATTERNS:
        - Improvement Trend: {learning_patterns.get('improvement_trend', 'unknown')}
        - Consistency Level: {learning_patterns.get('consistency', 'unknown')}
        - Topic Preferences: {learning_patterns.get('topic_preferences', {})}

        RECENT PERFORMANCE:
        {json.dumps(performance_history[-5:], indent=2) if performance_history else 'No performance history available'}

        TASK:
        Provide a detailed analysis in JSON format with the following structure:
        {{
            "overall_assessment": "Brief summary of student's current state",
            "strengths": ["List of student's strengths"],
            "improvement_areas": ["Areas that need improvement"],
            "recommendations": ["Specific recommendations for learning"],
            "learning_strategy": "Recommended learning approach",
            "motivation_level": "Assessed motivation level (high/medium/low)",
            "next_steps": ["Immediate next steps for the student"]
        }}

        Focus on:
        1. Identifying the root causes of performance issues
        2. Recognizing student strengths and building on them
        3. Providing actionable, personalized recommendations
        4. Considering psychological aspects of learning
        5. Suggesting appropriate difficulty progression

        Ensure your response is valid JSON that can be parsed.
        """
        
        return prompt
    
    def _parse_llm_analysis(self, llm_response: str) -> Dict[str, Any]:
        """
        Parse the LLM response and extract structured information.
        
        Args:
            llm_response: Raw response from LLM
            
        Returns:
            Parsed analysis dictionary
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
            self.logger.warning("Failed to parse LLM response as JSON")
        
        # Fallback: extract key information using text parsing
        fallback_analysis = {
            'overall_assessment': llm_response[:200] + "..." if len(llm_response) > 200 else llm_response,
            'strengths': [],
            'improvement_areas': [],
            'recommendations': [],
            'learning_strategy': 'adaptive',
            'motivation_level': 'medium',
            'next_steps': []
        }
        
        return fallback_analysis
    
    def get_stage_description(self, stage: int) -> str:
        """
        Get a description of the learning stage.
        
        Args:
            stage: Learning stage number
            
        Returns:
            Description of the stage
        """
        stage_descriptions = {
            0: "Beginner - Learning fundamental concepts and building basic understanding",
            1: "Elementary - Developing core skills and applying basic concepts",
            2: "Intermediate - Strengthening understanding and tackling more complex problems",
            3: "Advanced - Mastering concepts and handling challenging material",
            4: "Expert - Demonstrating mastery and exploring advanced applications"
        }
        
        return stage_descriptions.get(stage, "Unknown stage")
