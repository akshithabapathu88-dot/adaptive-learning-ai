from typing import List, Dict, Any, Optional
from .vector_store import VectorStore
import json

class RAGRetriever:
    def __init__(self, vector_store: VectorStore):
        """
        Initialize the RAG retriever.
        
        Args:
            vector_store: VectorStore instance for document retrieval
        """
        self.vector_store = vector_store
    
    def retrieve_context(self, query: str, topic: str, difficulty_level: str, 
                        max_context_length: int = 2000) -> str:
        """
        Retrieve relevant context for a given query, topic, and difficulty level.
        
        Args:
            query: The query or topic to retrieve context for
            topic: The specific topic
            difficulty_level: The difficulty level (Beginner, Intermediate, Advanced)
            max_context_length: Maximum length of context to return
            
        Returns:
            Retrieved context as a string
        """
        # Search for relevant documents
        results = self.vector_store.search(
            query=query,
            topic=topic,
            difficulty_level=difficulty_level,
            n_results=5
        )
        
        # Combine and format context
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result['content']
            metadata = result['metadata']
            
            # Format the content with metadata
            formatted_content = f"Topic: {metadata.get('topic', 'Unknown')}\n"
            formatted_content += f"Difficulty: {metadata.get('difficulty_level', 'Unknown')}\n"
            formatted_content += f"Content: {content}\n"
            formatted_content += "---\n"
            
            # Check if adding this content would exceed the max length
            if current_length + len(formatted_content) > max_context_length:
                # Truncate the content if needed
                remaining_length = max_context_length - current_length
                if remaining_length > 100:  # Only add if there's meaningful space
                    truncated_content = formatted_content[:remaining_length-3] + "..."
                    context_parts.append(truncated_content)
                break
            
            context_parts.append(formatted_content)
            current_length += len(formatted_content)
        
        return "\n".join(context_parts)
    
    def retrieve_study_materials(self, topic: str, difficulty_level: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive study materials for a topic and difficulty level.
        
        Args:
            topic: The topic to retrieve materials for
            difficulty_level: The difficulty level
            
        Returns:
            Dictionary containing study materials
        """
        # Get all documents for the topic and difficulty level
        documents = self.vector_store.get_documents_by_topic(
            topic=topic,
            difficulty_level=difficulty_level
        )
        
        if not documents:
            # Try to get documents for the topic regardless of difficulty
            documents = self.vector_store.get_documents_by_topic(topic=topic)
        
        # Organize content by type
        study_materials = {
            'topic': topic,
            'difficulty_level': difficulty_level,
            'content': [],
            'key_concepts': [],
            'examples': [],
            'explanations': []
        }
        
        for doc in documents:
            content = doc['content']
            metadata = doc['metadata']
            
            # Categorize content based on metadata or content analysis
            if 'content_type' in metadata:
                content_type = metadata['content_type']
                if content_type in study_materials:
                    study_materials[content_type].append(content)
                else:
                    study_materials['content'].append(content)
            else:
                # Basic categorization based on content
                content_lower = content.lower()
                if 'example' in content_lower or 'illustration' in content_lower:
                    study_materials['examples'].append(content)
                elif 'concept' in content_lower or 'definition' in content_lower:
                    study_materials['key_concepts'].append(content)
                elif 'explanation' in content_lower or 'because' in content_lower:
                    study_materials['explanations'].append(content)
                else:
                    study_materials['content'].append(content)
        
        return study_materials
    
    def retrieve_related_topics(self, topic: str, difficulty_level: str, 
                              n_results: int = 3) -> List[str]:
        """
        Retrieve related topics based on the current topic.
        
        Args:
            topic: Current topic
            difficulty_level: Difficulty level
            n_results: Number of related topics to return
            
        Returns:
            List of related topics
        """
        # Search for documents with similar content
        results = self.vector_store.search(
            query=topic,
            difficulty_level=difficulty_level,
            n_results=n_results * 2  # Get more to filter unique topics
        )
        
        # Extract unique topics (excluding the current topic)
        related_topics = set()
        for result in results:
            result_topic = result['metadata'].get('topic', '')
            if result_topic and result_topic != topic:
                related_topics.add(result_topic)
        
        return list(related_topics)[:n_results]
    
    def get_difficulty_adaptation_context(self, topic: str, current_score: float) -> str:
        """
        Get context for difficulty adaptation based on student performance.
        
        Args:
            topic: The topic being studied
            current_score: Student's current score (0-100)
            
        Returns:
            Context string for difficulty adaptation
        """
        # Determine difficulty level based on score
        if current_score <= 40:
            difficulty_level = "Beginner"
            adaptation_query = f"basic concepts and fundamentals of {topic}"
        elif current_score <= 70:
            difficulty_level = "Intermediate"
            adaptation_query = f"intermediate level concepts and applications of {topic}"
        else:
            difficulty_level = "Advanced"
            adaptation_query = f"advanced concepts and complex problems in {topic}"
        
        # Retrieve context for the determined difficulty level
        context = self.retrieve_context(
            query=adaptation_query,
            topic=topic,
            difficulty_level=difficulty_level
        )
        
        # Add adaptation information
        adaptation_info = f"""
        Performance-Based Adaptation:
        - Current Score: {current_score}%
        - Recommended Difficulty: {difficulty_level}
        - Focus Area: {adaptation_query}
        
        Retrieved Context:
        {context}
        """
        
        return adaptation_info
    
    def initialize_sample_content(self):
        """Initialize the vector store with sample educational content."""
        sample_documents = [
            {
                'content': 'Python is a high-level, interpreted programming language known for its simple syntax and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.',
                'topic': 'Python Programming',
                'difficulty_level': 'Beginner',
                'metadata': {'content_type': 'explanations'}
            },
            {
                'content': 'Variables in Python are used to store data values. Python has no command for declaring a variable. A variable is created the moment you first assign a value to it. Example: x = 5, name = "John"',
                'topic': 'Python Programming',
                'difficulty_level': 'Beginner',
                'metadata': {'content_type': 'examples'}
            },
            {
                'content': 'Object-oriented programming (OOP) in Python involves classes and objects. A class is a blueprint for creating objects, providing initial values for state (attributes) and implementations of behavior (methods).',
                'topic': 'Python Programming',
                'difficulty_level': 'Intermediate',
                'metadata': {'content_type': 'key_concepts'}
            },
            {
                'content': 'Decorators in Python are a powerful tool that allows you to modify the behavior of a function or class. They are essentially functions that wrap another function and extend its behavior.',
                'topic': 'Python Programming',
                'difficulty_level': 'Advanced',
                'metadata': {'content_type': 'key_concepts'}
            },
            {
                'content': 'Data structures are fundamental concepts in computer science. In Python, common data structures include lists, tuples, dictionaries, and sets, each with specific use cases and performance characteristics.',
                'topic': 'Data Structures',
                'difficulty_level': 'Beginner',
                'metadata': {'content_type': 'explanations'}
            },
            {
                'content': 'Algorithm complexity analysis involves understanding the time and space complexity of algorithms. Big O notation is used to describe the upper bound of an algorithm\'s growth rate.',
                'topic': 'Algorithms',
                'difficulty_level': 'Intermediate',
                'metadata': {'content_type': 'key_concepts'}
            }
        ]
        
        self.vector_store.add_documents(sample_documents)
