"""
AI-Based Personalized Content and Assignment Generation for Adaptive Student Learning

Main entry point for the adaptive learning system.
This file provides a command-line interface to run the Streamlit application
and initialize the system components.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('adaptive_learning.log'),
            logging.StreamHandler()
        ]
    )

def check_environment():
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
    
    required_vars = ['GROQ_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set the following environment variables:")
        print("export GROQ_API_KEY='your_groq_api_key_here'")
        print("\nOr create a .env file with these variables.")
        return False
    
    return True

def initialize_database():
    """Initialize the database and create tables."""
    try:
        from database.models import create_tables
        create_tables()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False

def initialize_sample_data():
    """Initialize sample data for testing."""
    try:
        from rag.vector_store import VectorStore
        from rag.retriever import RAGRetriever
        
        print("🔄 Initializing sample data...")
        
        # Initialize vector store
        vector_store = VectorStore()
        retriever = RAGRetriever(vector_store)
        
        # Add sample content
        retriever.initialize_sample_content()
        
        # Get collection stats
        stats = vector_store.get_collection_stats()
        print(f"✅ Sample data initialized: {stats['total_documents']} documents added")
        
        return True
    except Exception as e:
        print(f"❌ Error initializing sample data: {str(e)}")
        return False

def create_sample_student():
    """Create a sample student for testing."""
    try:
        from database.models import get_db
        from database.db import DatabaseManager
        
        db = DatabaseManager(next(get_db()))
        
        # Check if sample student already exists
        existing_student = db.get_student_by_username("demo_student")
        if existing_student:
            print("ℹ️  Demo student already exists")
            return True
        
        # Create sample student
        student = db.create_student(
            username="demo_student",
            email="demo@example.com",
            password_hash="demo123"  # In production, use proper hashing
        )
        
        print(f"✅ Demo student created: {student.username} (ID: {student.id})")
        print("   Login with: username=demo_student, password=demo123")
        
        return True
    except Exception as e:
        print(f"❌ Error creating sample student: {str(e)}")
        return False

def run_streamlit_app():
    """Run the Streamlit application."""
    try:
        import subprocess
        print("🚀 Starting Streamlit application...")
        
        # Run streamlit from the frontend directory
        frontend_dir = Path(__file__).parent / "frontend"
        app_file = frontend_dir / "streamlit_app.py"
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(app_file),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ]
        
        print(f"📱 Opening app at: http://localhost:8501")
        print("🛑 Press Ctrl+C to stop the application")
        
        subprocess.run(cmd, cwd=str(frontend_dir))
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running Streamlit app: {str(e)}")

def run_langgraph_demo():
    """Run a demonstration of the LangGraph workflow."""
    try:
        print("🔄 Running LangGraph workflow demonstration...")
        
        # Import required modules
        from database.models import get_db
        from database.db import DatabaseManager
        from rag.vector_store import VectorStore
        from rag.retriever import RAGRetriever
        from agents.student_analyzer import StudentAnalyzer
        from agents.content_generator import ContentGenerator
        from agents.quiz_generator import QuizGenerator
        from agents.evaluator import Evaluator
        from agents.recommendation_agent import RecommendationAgent
        
        # Initialize components
        db = DatabaseManager(next(get_db()))
        vector_store = VectorStore()
        retriever = RAGRetriever(vector_store)
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        
        # Initialize agents
        student_analyzer = StudentAnalyzer(groq_api_key)
        content_generator = ContentGenerator(groq_api_key, rag_retriever=retriever)
        quiz_generator = QuizGenerator(groq_api_key)
        evaluator = Evaluator(groq_api_key)
        recommendation_agent = RecommendationAgent(groq_api_key)
        
        print("✅ All agents initialized successfully")
        
        # Demo workflow
        print("\n📋 Running demo workflow...")
        
        # Step 1: Analyze student
        print("1. Analyzing student performance...")
        demo_student_id = 1  # Assuming demo student exists
        
        student_data = {
            'student_id': demo_student_id,
            'performance_history': [
                {'score': 75, 'topic': 'Python Programming'},
                {'score': 60, 'topic': 'Data Structures'}
            ],
            'current_stage': 1,
            'quiz_results': [{'score': 70}],
            'weak_topics': ['Recursion', 'Algorithms']
        }
        
        analysis = student_analyzer.analyze_student_performance(student_data)
        print(f"   Recommended stage: {analysis['recommended_stage']}")
        
        # Step 2: Generate content
        print("2. Generating learning content...")
        content_request = {
            'student_id': demo_student_id,
            'topic': 'Python Programming',
            'difficulty_level': 'Intermediate',
            'student_stage': analysis['recommended_stage']
        }
        
        content = content_generator.generate_personalized_content(content_request)
        print(f"   Generated content for: {content['topic']}")
        
        # Step 3: Generate quiz
        print("3. Generating quiz...")
        quiz_request = {
            'student_id': demo_student_id,
            'topic': 'Python Programming',
            'difficulty_level': 'Intermediate',
            'student_stage': analysis['recommended_stage'],
            'question_count': 3
        }
        
        quiz = quiz_generator.generate_quiz(quiz_request)
        print(f"   Generated {quiz['total_questions']} quiz questions")
        
        # Step 4: Evaluate quiz (simulate answers)
        print("4. Evaluating quiz answers...")
        sample_answers = ['A', 'B', 'C']  # Sample answers
        
        evaluation_request = {
            'student_id': demo_student_id,
            'quiz_id': quiz['quiz_id'],
            'questions': quiz['questions'],
            'student_answers': sample_answers,
            'topic': quiz['topic'],
            'difficulty_level': quiz['difficulty_level']
        }
        
        results = evaluator.evaluate_quiz_answers(evaluation_request)
        print(f"   Quiz score: {results['score_percentage']:.1f}%")
        
        # Step 5: Generate recommendations
        print("5. Generating recommendations...")
        recommendation_request = {
            'student_id': demo_student_id,
            'current_performance': results,
            'performance_history': student_data['performance_history'],
            'learning_goals': ['Master Python Programming'],
            'weak_areas': student_data['weak_topics'],
            'current_stage': analysis['recommended_stage']
        }
        
        recommendations = recommendation_agent.generate_recommendations(recommendation_request)
        print(f"   Generated {len(recommendations.get('topic_recommendations', []))} recommendations")
        
        print("\n✅ LangGraph workflow demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in LangGraph demo: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="AI-Based Adaptive Learning System"
    )
    
    parser.add_argument(
        'command',
        choices=['run', 'init', 'demo', 'setup'],
        help='Command to run'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Port for Streamlit app (default: 8501)'
    )
    
    parser.add_argument(
        '--skip-sample-data',
        action='store_true',
        help='Skip sample data initialization'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    print("🎓 AI-Based Adaptive Learning System")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    if args.command == 'setup':
        print("🔧 Setting up the system...")
        
        # Initialize database
        if not initialize_database():
            sys.exit(1)
        
        # Initialize sample data
        if not args.skip_sample_data:
            if not initialize_sample_data():
                sys.exit(1)
        
        # Create sample student
        if not create_sample_student():
            sys.exit(1)
        
        print("\n✅ System setup completed successfully!")
        print("🚀 Run 'python main.py run' to start the application")
        
    elif args.command == 'init':
        print("🔄 Initializing database...")
        if initialize_database():
            print("✅ Database initialized successfully")
        else:
            sys.exit(1)
        
        if not args.skip_sample_data:
            print("🔄 Initializing sample data...")
            if initialize_sample_data():
                print("✅ Sample data initialized successfully")
            else:
                sys.exit(1)
        
        if not create_sample_student():
            sys.exit(1)
        
    elif args.command == 'demo':
        print("🎭 Running LangGraph workflow demonstration...")
        run_langgraph_demo()
        
    elif args.command == 'run':
        print("🚀 Starting the application...")
        
        # Check if database exists
        if not initialize_database():
            print("⚠️  Database initialization failed. Please run 'python main.py setup' first.")
            sys.exit(1)
        
        # Start Streamlit app
        run_streamlit_app()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
