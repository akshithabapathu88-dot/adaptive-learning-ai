from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
import json
import logging
from datetime import datetime

class AssignmentGenerator:
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.1-8b-instant"):
        """
        Initialize the Assignment Generator agent.
        
        Args:
            groq_api_key: API key for Groq
            model_name: Name of the Groq model to use
        """
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)
        self.logger = logging.getLogger(__name__)
    
    def generate_assignments(self, assignment_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized assignments based on student profile and topic.
        
        Args:
            assignment_request: Dictionary containing:
                - student_id: Student ID
                - topic: Topic for assignments
                - difficulty_level: Difficulty level (Beginner, Intermediate, Advanced)
                - student_stage: Current learning stage
                - assignment_count: Number of assignments to generate (default: 3-5)
                - focus_areas: Specific areas to focus on
                - assignment_types: Types of assignments (coding, theoretical, practical)
                
        Returns:
            Dictionary containing generated assignments
        """
        # Extract parameters
        student_id = assignment_request.get('student_id')
        topic = assignment_request.get('topic')
        difficulty_level = assignment_request.get('difficulty_level', 'Intermediate')
        student_stage = assignment_request.get('student_stage', 1)
        assignment_count = assignment_request.get('assignment_count', 4)
        focus_areas = assignment_request.get('focus_areas', [])
        assignment_types = assignment_request.get('assignment_types', ['mixed'])
        
        # Determine assignment types
        if 'mixed' in assignment_types:
            assignment_types = self._get_mixed_assignment_types(difficulty_level)
        
        # Create assignment generation prompt
        assignment_prompt = self._create_assignment_prompt(
            topic, difficulty_level, student_stage, assignment_count,
            focus_areas, assignment_types
        )
        
        try:
            # Generate assignments using LLM
            response = self.llm.invoke([HumanMessage(content=assignment_prompt)])
            generated_assignments = response.content
            
            # Parse and structure the assignments
            structured_assignments = self._parse_assignments(generated_assignments)
            
            # Add metadata and validation
            final_assignments = {
                'student_id': student_id,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'student_stage': student_stage,
                'generated_at': datetime.utcnow().isoformat(),
                'assignments': structured_assignments,
                'total_assignments': len(structured_assignments),
                'estimated_completion_time': self._estimate_completion_time(structured_assignments),
                'learning_objectives': self._extract_learning_objectives(structured_assignments),
                'focus_areas': focus_areas,
                'assignment_types': assignment_types
            }
            
            return final_assignments
            
        except Exception as e:
            self.logger.error(f"Error generating assignments: {str(e)}")
            return {
                'student_id': student_id,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'error': str(e),
                'assignments': []
            }
    
    def _create_assignment_prompt(self, topic: str, difficulty_level: str, student_stage: int,
                                assignment_count: int, focus_areas: List[str], 
                                assignment_types: List[str]) -> str:
        """
        Create a comprehensive prompt for assignment generation.
        
        Args:
            topic: Topic for assignments
            difficulty_level: Difficulty level
            student_stage: Student's current learning stage
            assignment_count: Number of assignments to generate
            focus_areas: Specific areas to focus on
            assignment_types: Types of assignments to generate
            
        Returns:
            Formatted prompt string
        """
        # Get difficulty-specific guidelines
        difficulty_guidelines = self._get_difficulty_guidelines(difficulty_level, student_stage)
        
        # Get assignment type specifications
        type_specifications = self._get_assignment_type_specifications(assignment_types)
        
        prompt = f"""
        You are an expert educational assignment designer. Create {assignment_count} engaging and effective assignments for the following specifications:

        TOPIC: {topic}
        DIFFICULTY LEVEL: {difficulty_level}
        STUDENT STAGE: {student_stage}
        FOCUS AREAS: {', '.join(focus_areas) if focus_areas else 'General topic coverage'}
        ASSIGNMENT TYPES: {', '.join(assignment_types)}

        DIFFICULTY GUIDELINES:
        {difficulty_guidelines}

        ASSIGNMENT TYPE SPECIFICATIONS:
        {type_specifications}

        REQUIREMENTS:
        1. Create exactly {assignment_count} distinct assignments
        2. Each assignment should be appropriate for the specified difficulty level
        3. Include a mix of theoretical and practical tasks
        4. Provide clear instructions and expected outcomes
        5. Include estimated completion time for each assignment
        6. Add evaluation criteria for each assignment
        7. Ensure assignments build on each other when possible

        Generate assignments in the following JSON format:
        {{
            "assignments": [
                {{
                    "id": 1,
                    "title": "Assignment title",
                    "type": "coding/theoretical/practical/research",
                    "description": "Detailed description of the assignment (100-200 words)",
                    "instructions": ["Step 1", "Step 2", "Step 3"],
                    "learning_objectives": ["Objective 1", "Objective 2"],
                    "estimated_time": "Time in minutes",
                    "difficulty": "easy/medium/hard",
                    "evaluation_criteria": [
                        {{"criterion": "Criteria 1", "weight": "percentage"}},
                        {{"criterion": "Criteria 2", "weight": "percentage"}}
                    ],
                    "resources_needed": ["Resource 1", "Resource 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"],
                    "hints": ["Optional hint 1", "Optional hint 2"]
                }}
            ]
        }}

        Ensure assignments are:
        - Engaging and relevant to real-world applications
        - Appropriately challenging for the difficulty level
        - Clear and unambiguous in instructions
        - Designed to reinforce key concepts
        - Varied in approach and methodology

        Return valid JSON that can be parsed.
        """
        
        return prompt
    
    def _get_difficulty_guidelines(self, difficulty_level: str, student_stage: int) -> str:
        """
        Get difficulty-specific guidelines for assignment generation.
        
        Args:
            difficulty_level: Difficulty level
            student_stage: Student's learning stage
            
        Returns:
            Difficulty guidelines string
        """
        guidelines = {
            'Beginner': {
                0: "Focus on basic concepts recall and simple application. Use guided exercises with clear examples. Include step-by-step instructions.",
                1: "Introduce problem-solving with moderate guidance. Include templates and partially completed solutions."
            },
            'Intermediate': {
                1: "Require independent application of concepts. Include multi-step problems and some open-ended tasks.",
                2: "Focus on analysis and synthesis. Include case studies and more complex problem-solving scenarios."
            },
            'Advanced': {
                2: "Emphasize critical thinking and evaluation. Include complex, open-ended problems with multiple valid approaches.",
                3: "Require creation and innovation. Include research components, optimization tasks, and real-world projects."
            }
        }
        
        return guidelines.get(difficulty_level, {}).get(student_stage, 
            "Adapt assignment complexity based on the difficulty level and student's current stage.")
    
    def _get_assignment_type_specifications(self, assignment_types: List[str]) -> str:
        """
        Get specifications for different assignment types.
        
        Args:
            assignment_types: List of assignment types
            
        Returns:
            Assignment type specifications string
        """
        specifications = {
            'coding': "Include programming tasks with clear requirements, test cases, and expected outputs.",
            'theoretical': "Include conceptual questions, explanations, and analytical tasks.",
            'practical': "Include hands-on activities, real-world applications, and implementation tasks.",
            'research': "Include investigation tasks, literature review, and discovery-based learning.",
            'project': "Include comprehensive multi-part assignments that integrate multiple concepts."
        }
        
        return '\n'.join([f"- {atype}: {specifications.get(atype, 'Standard assignment type')}" 
                         for atype in assignment_types])
    
    def _get_mixed_assignment_types(self, difficulty_level: str) -> List[str]:
        """
        Get a balanced mix of assignment types based on difficulty level.
        
        Args:
            difficulty_level: Difficulty level
            
        Returns:
            List of assignment types
        """
        if difficulty_level == 'Beginner':
            return ['coding', 'theoretical', 'practical']
        elif difficulty_level == 'Intermediate':
            return ['coding', 'theoretical', 'practical', 'research']
        else:  # Advanced
            return ['coding', 'practical', 'research', 'project']
    
    def _parse_assignments(self, generated_assignments: str) -> List[Dict[str, Any]]:
        """
        Parse the generated assignments from LLM response.
        
        Args:
            generated_assignments: Raw assignments from LLM
            
        Returns:
            List of structured assignment dictionaries
        """
        try:
            # Try to parse as JSON directly
            if generated_assignments.strip().startswith('{'):
                data = json.loads(generated_assignments)
                if 'assignments' in data:
                    return data['assignments']
                return [data]  # Single assignment
            
            # Look for JSON content in the response
            start_idx = generated_assignments.find('{')
            end_idx = generated_assignments.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = generated_assignments[start_idx:end_idx]
                data = json.loads(json_content)
                if 'assignments' in data:
                    return data['assignments']
                return [data]
            
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse assignments as JSON")
        
        # Fallback: create basic assignment structure from text
        fallback_assignment = {
            'id': 1,
            'title': 'Generated Assignment',
            'type': 'theoretical',
            'description': generated_assignments[:500] + "..." if len(generated_assignments) > 500 else generated_assignments,
            'instructions': ['Review the provided material', 'Complete the assigned tasks'],
            'learning_objectives': ['Understand the topic', 'Apply the concepts'],
            'estimated_time': '60 minutes',
            'difficulty': 'medium',
            'evaluation_criteria': [{'criterion': 'Completion', 'weight': '100%'}],
            'resources_needed': ['Study materials'],
            'deliverables': ['Completed assignment'],
            'hints': []
        }
        
        return [fallback_assignment]
    
    def _estimate_completion_time(self, assignments: List[Dict[str, Any]]) -> str:
        """
        Estimate total completion time for all assignments.
        
        Args:
            assignments: List of assignment dictionaries
            
        Returns:
            Estimated completion time string
        """
        total_minutes = 0
        
        for assignment in assignments:
            time_str = assignment.get('estimated_time', '60 minutes')
            # Extract number from time string
            import re
            match = re.search(r'(\d+)', time_str)
            if match:
                total_minutes += int(match.group(1))
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _extract_learning_objectives(self, assignments: List[Dict[str, Any]]) -> List[str]:
        """
        Extract all learning objectives from assignments.
        
        Args:
            assignments: List of assignment dictionaries
            
        Returns:
            List of unique learning objectives
        """
        all_objectives = []
        
        for assignment in assignments:
            objectives = assignment.get('learning_objectives', [])
            all_objectives.extend(objectives)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_objectives = []
        for obj in all_objectives:
            if obj not in seen:
                seen.add(obj)
                unique_objectives.append(obj)
        
        return unique_objectives
    
    def generate_extension_activities(self, topic: str, difficulty_level: str, 
                                    student_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate extension activities based on student performance.
        
        Args:
            topic: Topic for extension activities
            difficulty_level: Current difficulty level
            student_performance: Student performance data
            
        Returns:
            List of extension activities
        """
        performance_score = student_performance.get('score', 50)
        weak_areas = student_performance.get('weak_areas', [])
        
        if performance_score >= 80:
            # Advanced extension activities
            extension_type = "advanced"
        elif performance_score >= 60:
            # Reinforcement activities
            extension_type = "reinforcement"
        else:
            # Remedial activities
            extension_type = "remedial"
        
        extension_prompt = f"""
        Generate 3 extension activities for {topic} based on student performance:
        - Performance Score: {performance_score}%
        - Weak Areas: {', '.join(weak_areas) if weak_areas else 'None identified'}
        - Extension Type: {extension_type}
        
        Activities should be challenging but achievable, focusing on {extension_type} learning.
        
        Format as JSON array of activity objects with: title, description, type, difficulty, time_estimate.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=extension_prompt)])
            activities = json.loads(response.content)
            
            if isinstance(activities, list):
                return activities
            else:
                return [activities]
                
        except Exception as e:
            self.logger.error(f"Error generating extension activities: {str(e)}")
            return []
