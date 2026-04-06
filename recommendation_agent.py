from typing import Dict, Any, List, Optional, Tuple
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
import json
import logging
from datetime import datetime

class RecommendationAgent:
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.1-8b-instant"):
        """
        Initialize the Recommendation Agent.
        
        Args:
            groq_api_key: API key for Groq
            model_name: Name of the Groq model to use
        """
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)
        self.logger = logging.getLogger(__name__)
    
    def generate_recommendations(self, recommendation_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized learning recommendations based on student performance and profile.
        
        Args:
            recommendation_request: Dictionary containing:
                - student_id: Student ID
                - current_performance: Recent performance data
                - performance_history: Historical performance data
                - learning_goals: Student's learning goals
                - preferred_topics: Topics student is interested in
                - weak_areas: Areas needing improvement
                - strong_areas: Areas of strength
                - current_stage: Current learning stage
                - time_available: Time available for learning (hours per week)
                
        Returns:
            Dictionary containing personalized recommendations
        """
        # Extract parameters
        student_id = recommendation_request.get('student_id')
        current_performance = recommendation_request.get('current_performance', {})
        performance_history = recommendation_request.get('performance_history', [])
        learning_goals = recommendation_request.get('learning_goals', [])
        preferred_topics = recommendation_request.get('preferred_topics', [])
        weak_areas = recommendation_request.get('weak_areas', [])
        strong_areas = recommendation_request.get('strong_areas', [])
        current_stage = recommendation_request.get('current_stage', 1)
        time_available = recommendation_request.get('time_available', 5)
        
        # Analyze performance patterns
        performance_analysis = self._analyze_performance_patterns(
            current_performance, performance_history
        )
        
        # Create recommendation prompt
        recommendation_prompt = self._create_recommendation_prompt(
            student_id, current_performance, performance_history, learning_goals,
            preferred_topics, weak_areas, strong_areas, current_stage, 
            time_available, performance_analysis
        )
        
        try:
            # Get LLM recommendations
            response = self.llm.invoke([HumanMessage(content=recommendation_prompt)])
            llm_recommendations = response.content
            
            # Parse recommendations
            parsed_recommendations = self._parse_recommendations(llm_recommendations)
            
            # Enhance with algorithmic recommendations
            enhanced_recommendations = self._enhance_recommendations(
                parsed_recommendations, performance_analysis, weak_areas, 
                strong_areas, current_stage
            )
            
            # Final recommendation structure
            final_recommendations = {
                'student_id': student_id,
                'generated_at': datetime.utcnow().isoformat(),
                'current_stage': current_stage,
                'performance_summary': performance_analysis,
                'learning_path': enhanced_recommendations.get('learning_path', {}),
                'topic_recommendations': enhanced_recommendations.get('topic_recommendations', []),
                'difficulty_adjustments': enhanced_recommendations.get('difficulty_adjustments', {}),
                'study_schedule': enhanced_recommendations.get('study_schedule', {}),
                'resource_recommendations': enhanced_recommendations.get('resource_recommendations', []),
                'practice_recommendations': enhanced_recommendations.get('practice_recommendations', []),
                'next_milestones': enhanced_recommendations.get('next_milestones', []),
                'motivation_tips': enhanced_recommendations.get('motivation_tips', []),
                'estimated_timeline': enhanced_recommendations.get('estimated_timeline', {}),
                'success_metrics': enhanced_recommendations.get('success_metrics', [])
            }
            
            return final_recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            # Return basic recommendations without LLM insights
            return {
                'student_id': student_id,
                'error': str(e),
                'basic_recommendations': self._get_basic_recommendations(
                    weak_areas, current_stage, time_available
                )
            }
    
    def _analyze_performance_patterns(self, current_performance: Dict, 
                                    performance_history: List[Dict]) -> Dict[str, Any]:
        """
        Analyze performance patterns to inform recommendations.
        
        Args:
            current_performance: Current performance data
            performance_history: Historical performance data
            
        Returns:
            Performance analysis dictionary
        """
        analysis = {
            'trend': 'stable',
            'consistency': 'medium',
            'strengths': [],
            'weaknesses': [],
            'improvement_rate': 0,
            'optimal_difficulty': 'Intermediate',
            'learning_velocity': 'average'
        }
        
        # Analyze trend
        if len(performance_history) >= 3:
            recent_scores = [p.get('score_percentage', 0) for p in performance_history[-3:]]
            if recent_scores[-1] > recent_scores[0] + 10:
                analysis['trend'] = 'improving'
                analysis['improvement_rate'] = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
            elif recent_scores[-1] < recent_scores[0] - 10:
                analysis['trend'] = 'declining'
                analysis['improvement_rate'] = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
        
        # Analyze consistency
        if performance_history:
            scores = [p.get('score_percentage', 0) for p in performance_history]
            variance = max(scores) - min(scores)
            if variance < 15:
                analysis['consistency'] = 'high'
            elif variance < 30:
                analysis['consistency'] = 'medium'
            else:
                analysis['consistency'] = 'low'
        
        # Determine optimal difficulty
        current_score = current_performance.get('score_percentage', 50)
        if current_score >= 80:
            analysis['optimal_difficulty'] = 'Advanced'
        elif current_score >= 60:
            analysis['optimal_difficulty'] = 'Intermediate'
        else:
            analysis['optimal_difficulty'] = 'Beginner'
        
        # Determine learning velocity
        if analysis['improvement_rate'] > 5:
            analysis['learning_velocity'] = 'fast'
        elif analysis['improvement_rate'] < -5:
            analysis['learning_velocity'] = 'slow'
        else:
            analysis['learning_velocity'] = 'average'
        
        return analysis
    
    def _create_recommendation_prompt(self, student_id: int, current_performance: Dict,
                                    performance_history: List[Dict], learning_goals: List[str],
                                    preferred_topics: List[str], weak_areas: List[str],
                                    strong_areas: List[str], current_stage: int,
                                    time_available: int, performance_analysis: Dict) -> str:
        """
        Create a comprehensive prompt for recommendation generation.
        
        Args:
            student_id: Student ID
            current_performance: Current performance data
            performance_history: Historical performance data
            learning_goals: Student's learning goals
            preferred_topics: Topics student prefers
            weak_areas: Areas needing improvement
            strong_areas: Areas of strength
            current_stage: Current learning stage
            time_available: Available study time per week
            performance_analysis: Performance analysis results
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
        You are an expert educational counselor and AI learning strategist. Generate comprehensive, personalized learning recommendations for the following student:

        STUDENT PROFILE:
        - Student ID: {student_id}
        - Current Learning Stage: {current_stage}
        - Available Study Time: {time_available} hours per week
        - Learning Goals: {', '.join(learning_goals) if learning_goals else 'Not specified'}
        - Preferred Topics: {', '.join(preferred_topics) if preferred_topics else 'Open to all topics'}

        PERFORMANCE ANALYSIS:
        - Current Score: {current_performance.get('score_percentage', 'N/A')}%
        - Performance Trend: {performance_analysis['trend']}
        - Consistency Level: {performance_analysis['consistency']}
        - Learning Velocity: {performance_analysis['learning_velocity']}
        - Optimal Difficulty: {performance_analysis['optimal_difficulty']}

        STRENGTHS & WEAKNESSES:
        - Strong Areas: {', '.join(strong_areas) if strong_areas else 'To be identified'}
        - Weak Areas: {', '.join(weak_areas) if weak_areas else 'None identified'}

        RECENT PERFORMANCE:
        {json.dumps(current_performance, indent=2)}

        TASK:
        Generate comprehensive learning recommendations in JSON format with the following structure:
        {{
            "learning_path": {{
                "current_focus": "Primary focus area for next 2-3 weeks",
                "next_topics": ["Topic 1", "Topic 2", "Topic 3"],
                "progression_timeline": "Estimated timeline for current stage",
                "milestone_goals": ["Milestone 1", "Milestone 2"]
            }},
            "topic_recommendations": [
                {{
                    "topic": "Topic name",
                    "priority": "high/medium/low",
                    "reason": "Why this topic is recommended",
                    "estimated_duration": "Time to complete",
                    "prerequisites": ["Prerequisite topics"]
                }}
            ],
            "difficulty_adjustments": {{
                "current_difficulty": "Current recommended difficulty",
                "target_difficulty": "Target difficulty for next stage",
                "adjustment_timeline": "When to make adjustment",
                "preparation_needed": "What to do before adjustment"
            }},
            "study_schedule": {{
                "weekly_structure": [
                    {{"day": "Monday", "focus": "Topic/Activity", "duration": "minutes"}},
                    {{"day": "Tuesday", "focus": "Topic/Activity", "duration": "minutes"}}
                ],
                "study_techniques": ["Technique 1", "Technique 2"],
                "break_recommendations": "Break schedule advice"
            }},
            "resource_recommendations": [
                {{
                    "type": "video/book/practice/project",
                    "title": "Resource title",
                    "description": "Brief description",
                    "difficulty": "Beginner/Intermediate/Advanced"
                }}
            ],
            "practice_recommendations": [
                {{
                    "type": "quiz/assignment/project",
                    "focus": "Area of practice",
                    "frequency": "How often to practice",
                    "difficulty": "Recommended difficulty"
                }}
            ],
            "next_milestones": [
                {{
                    "milestone": "Milestone description",
                    "target_date": "Estimated achievement date",
                    "success_criteria": ["Criteria 1", "Criteria 2"]
                }}
            ],
            "motivation_tips": [
                "Personalized motivation tip 1",
                "Personalized motivation tip 2"
            ],
            "estimated_timeline": {{
                "current_stage_completion": "Time to complete current stage",
                "next_stage_readiness": "Time until ready for next stage",
                "overall_goal_timeline": "Timeline for major goals"
            }},
            "success_metrics": [
                "Metric 1 to track progress",
                "Metric 2 to track progress"
            ]
        }}

        RECOMMENDATION PRINCIPLES:
        1. Personalize based on performance patterns and learning velocity
        2. Address weak areas while building on strengths
        3. Consider available time and create realistic schedules
        4. Provide specific, actionable recommendations
        5. Include both short-term and long-term goals
        6. Suggest appropriate difficulty progression
        7. Include diverse learning resources and methods
        8. Consider student preferences and goals
        9. Provide motivation and success strategies
        10. Ensure recommendations are measurable and trackable

        Focus on creating a balanced, progressive learning path that challenges the student appropriately while ensuring success.

        Return valid JSON that can be parsed.
        """
        
        return prompt
    
    def _parse_recommendations(self, llm_response: str) -> Dict[str, Any]:
        """
        Parse the LLM recommendation response.
        
        Args:
            llm_response: Raw response from LLM
            
        Returns:
            Parsed recommendations dictionary
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
            self.logger.warning("Failed to parse recommendations as JSON")
        
        # Fallback: create basic recommendation structure
        fallback_recommendations = {
            'learning_path': {
                'current_focus': 'Continue with current studies',
                'next_topics': [],
                'progression_timeline': '2-4 weeks',
                'milestone_goals': []
            },
            'topic_recommendations': [],
            'difficulty_adjustments': {
                'current_difficulty': 'Intermediate',
                'target_difficulty': 'Intermediate',
                'adjustment_timeline': '2 weeks',
                'preparation_needed': 'Continue practice'
            },
            'study_schedule': {
                'weekly_structure': [],
                'study_techniques': ['Regular practice', 'Review concepts'],
                'break_recommendations': 'Take breaks every 45 minutes'
            },
            'resource_recommendations': [],
            'practice_recommendations': [],
            'next_milestones': [],
            'motivation_tips': ['Stay consistent', 'Track your progress'],
            'estimated_timeline': {
                'current_stage_completion': '2-3 weeks',
                'next_stage_readiness': '3-4 weeks',
                'overall_goal_timeline': '2-3 months'
            },
            'success_metrics': ['Quiz scores', 'Assignment completion']
        }
        
        return fallback_recommendations
    
    def _enhance_recommendations(self, parsed_recommendations: Dict, 
                               performance_analysis: Dict, weak_areas: List[str],
                               strong_areas: List[str], current_stage: int) -> Dict[str, Any]:
        """
        Enhance LLM recommendations with algorithmic insights.
        
        Args:
            parsed_recommendations: Recommendations from LLM
            performance_analysis: Performance analysis
            weak_areas: Weak areas
            strong_areas: Strong areas
            current_stage: Current learning stage
            
        Returns:
            Enhanced recommendations
        """
        # Add algorithmic topic recommendations based on weak areas
        if weak_areas:
            for area in weak_areas:
                # Check if this area is already in recommendations
                existing_topics = [rec.get('topic', '') for rec in parsed_recommendations.get('topic_recommendations', [])]
                if area not in existing_topics:
                    parsed_recommendations['topic_recommendations'].append({
                        'topic': area,
                        'priority': 'high',
                        'reason': f'Identified as weak area needing improvement',
                        'estimated_duration': '1-2 weeks',
                        'prerequisites': []
                    })
        
        # Adjust difficulty recommendations based on performance
        optimal_difficulty = performance_analysis.get('optimal_difficulty', 'Intermediate')
        parsed_recommendations['difficulty_adjustments']['current_difficulty'] = optimal_difficulty
        
        # Add study techniques based on learning velocity
        learning_velocity = performance_analysis.get('learning_velocity', 'average')
        if learning_velocity == 'fast':
            parsed_recommendations['study_schedule']['study_techniques'].extend([
                'Advanced problem-solving',
                'Challenge exercises',
                'Peer teaching'
            ])
        elif learning_velocity == 'slow':
            parsed_recommendations['study_schedule']['study_techniques'].extend([
                'Frequent review sessions',
                'Step-by-step learning',
                'Additional practice problems'
            ])
        
        # Add motivation tips based on performance trend
        trend = performance_analysis.get('trend', 'stable')
        if trend == 'declining':
            parsed_recommendations['motivation_tips'].extend([
                'Focus on fundamentals before advancing',
                'Celebrate small wins to build confidence',
                'Consider study group for support'
            ])
        elif trend == 'improving':
            parsed_recommendations['motivation_tips'].extend([
                'Maintain current momentum',
                'Set slightly higher goals',
                'Share success with peers'
            ])
        
        return parsed_recommendations
    
    def _get_basic_recommendations(self, weak_areas: List[str], current_stage: int,
                                 time_available: int) -> Dict[str, Any]:
        """
        Get basic recommendations without LLM insights.
        
        Args:
            weak_areas: Areas needing improvement
            current_stage: Current learning stage
            time_available: Available study time
            
        Returns:
            Basic recommendations
        """
        return {
            'focus_areas': weak_areas if weak_areas else ['General improvement'],
            'recommended_difficulty': 'Intermediate' if current_stage >= 2 else 'Beginner',
            'study_frequency': f'{min(time_available // 2, 3)} sessions per week',
            'session_duration': f'{min(time_available * 20, 60)} minutes per session',
            'next_steps': [
                'Review weak areas',
                'Practice regularly',
                'Seek help when needed'
            ]
        }
    
    def suggest_next_topic(self, student_performance: Dict[str, Any], 
                          completed_topics: List[str]) -> Dict[str, Any]:
        """
        Suggest the next topic for the student to study.
        
        Args:
            student_performance: Student performance data
            completed_topics: List of completed topics
            
        Returns:
            Next topic recommendation
        """
        current_score = student_performance.get('score_percentage', 50)
        weak_areas = student_performance.get('weak_areas', [])
        strong_areas = student_performance.get('strong_areas', [])
        
        # Priority logic for next topic selection
        if weak_areas:
            # Prioritize weak areas for improvement
            next_topic = weak_areas[0]
            reason = 'Focus on improving weak areas'
            priority = 'high'
        elif strong_areas:
            # Build on strengths after addressing weaknesses
            next_topic = strong_areas[0]
            reason = 'Build on existing strengths'
            priority = 'medium'
        else:
            # Suggest foundational topic
            next_topic = 'Fundamentals'
            reason = 'Establish strong foundation'
            priority = 'high'
        
        # Determine appropriate difficulty
        if current_score >= 80:
            difficulty = 'Advanced'
        elif current_score >= 60:
            difficulty = 'Intermediate'
        else:
            difficulty = 'Beginner'
        
        return {
            'recommended_topic': next_topic,
            'difficulty': difficulty,
            'priority': priority,
            'reason': reason,
            'estimated_duration': self._estimate_topic_duration(difficulty),
            'prerequisites': self._get_prerequisites(next_topic),
            'learning_objectives': self._get_topic_objectives(next_topic)
        }
    
    def _estimate_topic_duration(self, difficulty: str) -> str:
        """Estimate duration for a topic based on difficulty."""
        durations = {
            'Beginner': '1-2 weeks',
            'Intermediate': '2-3 weeks',
            'Advanced': '3-4 weeks'
        }
        return durations.get(difficulty, '2-3 weeks')
    
    def _get_prerequisites(self, topic: str) -> List[str]:
        """Get prerequisites for a topic."""
        # This would typically come from a curriculum mapping
        prerequisites = {
            'Advanced Programming': ['Basic Programming', 'Data Structures'],
            'Data Structures': ['Basic Programming'],
            'Machine Learning': ['Statistics', 'Linear Algebra', 'Programming'],
            'Web Development': ['HTML/CSS', 'JavaScript Basics']
        }
        return prerequisites.get(topic, [])
    
    def _get_topic_objectives(self, topic: str) -> List[str]:
        """Get learning objectives for a topic."""
        # This would typically come from a curriculum mapping
        objectives = {
            'Python Programming': [
                'Understand basic syntax and data types',
                'Write functions and classes',
                'Handle errors and exceptions',
                'Work with files and modules'
            ],
            'Data Structures': [
                'Understand arrays and linked lists',
                'Implement stacks and queues',
                'Work with trees and graphs',
                'Analyze algorithm complexity'
            ]
        }
        return objectives.get(topic, ['Master the fundamental concepts', 'Apply knowledge in practice'])
