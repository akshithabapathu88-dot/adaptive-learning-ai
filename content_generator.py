from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
import json
import logging
from datetime import datetime
from rag.retriever import RAGRetriever

class ContentGenerator:
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.3-70b-versatile", 
                 rag_retriever: Optional[RAGRetriever] = None):
        """
        Initialize the Content Generator agent.
        
        Args:
            groq_api_key: API key for Groq
            model_name: Name of the Groq model to use
            rag_retriever: Optional RAG retriever for context
        """
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.1-8b-instant", max_tokens=2000)
        self.rag_retriever = rag_retriever
        self.logger = logging.getLogger(__name__)
    
    def generate_personalized_content(self, content_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized learning content based on student profile and request.
        
        Args:
            content_request: Dictionary containing:
                - student_id: Student ID
                - topic: Topic to generate content for
                - difficulty_level: Difficulty level (Beginner, Intermediate, Advanced)
                - student_stage: Current learning stage
                - learning_style: Optional learning style preference
                - weak_areas: Optional list of weak areas to focus on
                - content_type: Type of content (explanation, tutorial, examples)
                
        Returns:
            Dictionary containing generated content
        """
        # Extract parameters
        student_id = content_request.get('student_id')
        topic = content_request.get('topic')
        difficulty_level = content_request.get('difficulty_level', 'Intermediate')
        student_stage = content_request.get('student_stage', 1)
        learning_style = content_request.get('learning_style', 'visual')
        weak_areas = content_request.get('weak_areas', [])
        content_type = content_request.get('content_type', 'comprehensive')
        
        # Retrieve relevant context using RAG
        context = ""
        if self.rag_retriever:
            try:
                context = self.rag_retriever.retrieve_context(
                    query=topic,
                    topic=topic,
                    difficulty_level=difficulty_level,
                    max_context_length=1500
                )
            except Exception as e:
                self.logger.warning(f"RAG retrieval failed: {str(e)}")
                context = ""
        
        # Create content generation prompt
        content_prompt = self._create_content_prompt(
            topic, difficulty_level, student_stage, learning_style,
            weak_areas, content_type, context
        )
        
        try:
            # Generate content using LLM
            response = self.llm.invoke([HumanMessage(content=content_prompt)])
            generated_content = response.content
            
            # Parse and structure the content
            structured_content = self._parse_generated_content(generated_content)
            
            # Add metadata
            final_content = {
                'student_id': student_id,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'student_stage': student_stage,
                'content_type': content_type,
                'generated_at': self._get_timestamp(),
                'content': structured_content.get('main_content', ''),
                'key_concepts': structured_content.get('key_concepts', []),
                'examples': structured_content.get('examples', []),
                'exercises': structured_content.get('exercises', []),
                'learning_objectives': structured_content.get('learning_objectives', []),
                'summary': structured_content.get('summary', ''),
                'context_used': len(context) > 0,
                'rag_context': context[:500] + "..." if len(context) > 500 else context
            }
            
            return final_content
            
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            return {
                'student_id': student_id,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'error': str(e),
                'content': f"Error generating content: {str(e)}"
            }
    
    def _create_content_prompt(self, topic: str, difficulty_level: str, student_stage: int,
                              learning_style: str, weak_areas: List[str], content_type: str,
                              context: str) -> str:
        """
        Create a comprehensive prompt for content generation.
        
        Args:
            topic: Topic to generate content for
            difficulty_level: Difficulty level
            student_stage: Student's current learning stage
            learning_style: Learning style preference
            weak_areas: Areas the student struggles with
            content_type: Type of content to generate
            context: Retrieved context from RAG
            
        Returns:
            Formatted prompt string
        """
        # Determine content complexity based on difficulty and stage
        complexity_guidelines = self._get_complexity_guidelines(difficulty_level, student_stage)
        
        # Level-based content adaptation
        if difficulty_level.lower() == "beginner":
            level_instruction = """
            Provide a SIMPLE and EASY-TO-UNDERSTAND explanation.
            Start with a clear, basic definition of the topic.
            Use simple language.
            Include 2-3 basic examples that are easy to follow.
            Focus on fundamental concepts and basic understanding.
            Keep explanations concise and straightforward.
            For key concepts, provide simple 1-2 sentence explanations.
            For examples, provide basic illustrations without complex code.
            """
        elif difficulty_level.lower() == "intermediate":
            level_instruction = """
            Provide a CLEAR definition with MODERATE elaboration.
            Start with a comprehensive definition of the topic.
            Use moderate technical language with clear explanations.
            Include 3-4 practical examples with some complexity.
            Explain key concepts in depth but remain accessible.
            Focus on practical application and understanding.
            For key concepts, provide detailed explanations with context.
            For examples, include practical code snippets if topic is technical.
            """
        else:  # Advanced
            level_instruction = """
            Provide a CLEAR definition with ADVANCED and IN-DEPTH elaboration.
            Start with a precise and comprehensive technical definition of the topic.
            Use advanced language and with detailed explanations.
            Include 4-5 complex examples demonstrating deeper concepts and real-world scenarios.
            Explain key concepts thoroughly with advanced insights and underlying mechanisms.
            Focus on deep understanding, real-world applications, and professional-level knowledge.
            For key concepts, provide detailed explanations including theories, architecture, or advanced principles.
            For examples, include well-structured code snippets, best practices, and optimized implementations if the topic is technical.
            """
        
        # Learning style adaptations
        style_adaptations = self._get_learning_style_adaptations(learning_style)
        
        prompt = f"""
        Generate personalized learning content for a student with the following profile:
        
        Student Profile:
        - Topic: {topic}
        - Difficulty Level: {difficulty_level}
        - Learning Stage: {student_stage}
        
        Available Context (if relevant):
        {context}
        
        Instructions:
        1. {level_instruction}
        2. Start your response with a clear definition of "{topic}".
        3. Include key concepts that are essential for understanding this topic.
        4. Provide practical examples that demonstrate the concepts.
        5. Include 2-3 exercises or practice activities.
        6. End with a concise summary of main points.
        
        Content Structure:
        - Definition: Clear explanation of what {topic} is
        - Key Concepts: 3-5 essential concepts with detailed explanations
        - Examples: Practical, level-appropriate examples with real explanations
        - Exercises: Practice activities for reinforcement
        - Summary: Concise recap of main points
        
        Special Instructions for Examples:
        - If "{topic}" is programming/technical (Python, Data Structures, Algorithms, Web Development, Database, etc.):
          * For Beginner: Include basic examples with simple explanations
          * For Intermediate: Focus on theoretical explanations and concepts, NOT code blocks
          * For Advanced: Focus on theoretical explanations and concepts, NOT code blocks
          * Only provide code for any level if specifically requested by user
        - If "{topic}" is theoretical (Machine Learning, Operating Systems, etc.):
          * For Beginner: Include simple scenarios and basic concepts
          * For Intermediate: Include practical applications and step-by-step processes
          * For Advanced: Include in-depth analysis, real-world applications, and advanced theories
          * Focus on comprehensive explanations rather than code
        
        Special Instructions for Key Concepts:
        - For Beginner: Simple 1-2 sentence explanations
        - For Intermediate: Detailed explanations with context and examples
        - For Advanced: In-depth technical explanations with best practices and edge cases
        
        IMPORTANT: Generate the content in PLAIN TEXT FORMAT, not JSON. Provide the content directly as text that can be displayed to the user.
        
        Ensure the content is educational, engaging, and appropriate for the {difficulty_level} level.
        For advanced level, ensure the main content is at least 500-800 words with deep technical insights.
        """
        
        return prompt
    
    def _get_complexity_guidelines(self, difficulty_level: str, student_stage: int) -> str:
        """
        Get complexity guidelines based on difficulty level and student stage.
        
        Args:
            difficulty_level: Difficulty level
            student_stage: Student's learning stage
            
        Returns:
            Complexity guidelines string
        """
        guidelines = {
            'Beginner': {
                0: "Focus on fundamental concepts. Use simple language, short sentences, and concrete examples. Avoid abstract concepts.",
                1: "Introduce basic terminology with clear definitions. Use step-by-step explanations and visual aids."
            },
            'Intermediate': {
                1: "Build on basic knowledge. Introduce more complex concepts with moderate technical depth.",
                2: "Include theoretical foundations and practical applications. Use moderate complexity in examples."
            },
            'Advanced': {
                2: "Assume solid foundation. Focus on complex topics, edge cases, and optimization techniques.",
                3: "Cover expert-level content, advanced patterns, and best practices. Include industry applications."
            }
        }
        
        return guidelines.get(difficulty_level, {}).get(student_stage, 
            "Adapt content complexity based on the difficulty level and student's current stage.")
    
    def _get_learning_style_adaptations(self, learning_style: str) -> str:
        """
        Get adaptations for different learning styles.
        
        Args:
            learning_style: Learning style preference
            
        Returns:
            Learning style adaptations string
        """
        adaptations = {
            'visual': "Include diagrams, charts, and visual examples. Use color coding and spatial organization.",
            'auditory': "Use analogies, stories, and conversational tone. Include reading suggestions.",
            'kinesthetic': "Include hands-on exercises, practical applications, and interactive elements.",
            'reading': "Provide detailed text explanations, written examples, and comprehensive notes.",
            'mixed': "Balance visual, auditory, and kinesthetic elements for multi-modal learning."
        }
        
        return adaptations.get(learning_style, adaptations['mixed'])
    
    def _parse_generated_content(self, generated_content: str) -> Dict[str, Any]:
        """
        Parse the generated content from LLM response.
        
        Args:
            generated_content: Raw content from LLM
            
        Returns:
            Structured content dictionary
        """
        # Since we're now generating plain text, return it as a structured dictionary
        return {
            'main_content': generated_content,
            'key_concepts': [],
            'examples': [],
            'exercises': [],
            'learning_objectives': [],
            'summary': '',
            'topic': '',
            'difficulty_level': '',
            'student_stage': 1
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def generate_practice_examples(self, topic: str, difficulty_level: str, 
                                 count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate practice examples for a given topic and difficulty level.
        
        Args:
            topic: Topic to generate examples for
            difficulty_level: Difficulty level
            count: Number of examples to generate
            
        Returns:
            List of practice examples
        """
        examples_prompt = f"""
        Generate {count} practice examples for {topic} at {difficulty_level} level.
        
        For each example, provide:
        1. A clear problem statement
        2. Step-by-step solution
        3. Key learning points
        4. Common mistakes to avoid
        
        Format as JSON array of objects.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=examples_prompt)])
            examples_data = json.loads(response.content)
            
            if isinstance(examples_data, list):
                return examples_data
            elif isinstance(examples_data, dict) and 'examples' in examples_data:
                return examples_data['examples']
            else:
                return [{'description': response.content, 'solution': 'See explanation above'}]
                
        except Exception as e:
            self.logger.error(f"Error generating practice examples: {str(e)}")
            return [{'description': f"Error generating examples: {str(e)}", 'solution': ''}]
    
    def adapt_content_difficulty(self, content: str, current_difficulty: str, 
                               target_difficulty: str) -> str:
        """
        Adapt existing content to a different difficulty level.
        
        Args:
            content: Original content
            current_difficulty: Current difficulty level
            target_difficulty: Target difficulty level
            
        Returns:
            Adapted content
        """
        adaptation_prompt = f"""
        Adapt the following content from {current_difficulty} level to {target_difficulty} level:
        
        ORIGINAL CONTENT:
        {content}
        
        Adaptation guidelines:
        - If going to Beginner: Simplify language, add more basic examples, break down complex concepts
        - If going to Intermediate: Add depth, introduce more complexity, include practical applications
        - If going to Advanced: Add expert insights, cover edge cases, include optimization techniques
        
        Maintain the core meaning but adjust complexity appropriately.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=adaptation_prompt)])
            return response.content
        except Exception as e:
            self.logger.error(f"Error adapting content: {str(e)}")
            return content  # Return original content if adaptation fails
