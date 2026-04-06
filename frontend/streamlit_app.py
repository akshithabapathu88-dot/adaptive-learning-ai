import streamlit as st
import sys
import os
from datetime import datetime
import json

# Add parent directory to path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from database.models import create_tables, get_db
from database.db import DatabaseManager
from rag.vector_store import VectorStore
from rag.retriever import RAGRetriever
from agents.student_analyzer import StudentAnalyzer
from agents.content_generator import ContentGenerator
from agents.assignment_generator import AssignmentGenerator
from agents.quiz_generator import QuizGenerator
from agents.evaluator import Evaluator
from agents.recommendation_agent import RecommendationAgent
from pdf_generator.report_generator import PDFReportGenerator

# Initialize session state variables
def init_session_state():
    """Initialize session state variables."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'student_id' not in st.session_state:
        st.session_state.student_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_topic' not in st.session_state:
        st.session_state.current_topic = None
    if 'current_difficulty' not in st.session_state:
        st.session_state.current_difficulty = 'Intermediate'
    if 'learning_content' not in st.session_state:
        st.session_state.learning_content = None
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = []

# Initialize database and agents
@st.cache_resource
def initialize_system():
    """Initialize the system components."""
    # Create database tables
    create_tables()
    
    # Initialize vector store and RAG
    vector_store = VectorStore()
    retriever = RAGRetriever(vector_store)
    
    # Initialize sample content if needed
    try:
        retriever.initialize_sample_content()
    except Exception as e:
        st.warning(f"Could not initialize sample content: {e}")
    
    # Get Groq API key from environment or secrets
    groq_api_key = os.getenv('GROQ_API_KEY') or st.secrets.get('GROQ_API_KEY')
    
    if not groq_api_key:
        st.error("Groq API key not found. Please set GROQ_API_KEY environment variable or Streamlit secret.")
        st.stop()
    
    # Initialize agents
    student_analyzer = StudentAnalyzer(groq_api_key)
    content_generator = ContentGenerator(groq_api_key, rag_retriever=retriever)
    assignment_generator = AssignmentGenerator(groq_api_key)
    quiz_generator = QuizGenerator(groq_api_key)
    evaluator = Evaluator(groq_api_key)
    recommendation_agent = RecommendationAgent(groq_api_key)
    
    # Initialize PDF generator
    pdf_generator = PDFReportGenerator()
    
    return {
        'db': DatabaseManager(next(get_db())),
        'vector_store': vector_store,
        'retriever': retriever,
        'student_analyzer': student_analyzer,
        'content_generator': content_generator,
        'assignment_generator': assignment_generator,
        'quiz_generator': quiz_generator,
        'evaluator': evaluator,
        'recommendation_agent': recommendation_agent,
        'pdf_generator': pdf_generator
    }

def login_page(system_components):
    """Display login page."""
    st.title("🎓 AI-Based Adaptive Learning System")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_btn"):
            if username and password:
                db = system_components['db']
                student = db.get_student_by_username(username)
                
                # Simple password check (in production, use proper hashing)
                if student and student.password_hash == password:  # Simplified for demo
                    st.session_state.logged_in = True
                    st.session_state.student_id = student.id
                    st.session_state.username = student.username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")
    
    with col2:
        st.subheader("Sign Up")
        new_username = st.text_input("Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Sign Up", key="signup_btn"):
            if new_username and new_email and new_password:
                if new_password == confirm_password:
                    db = system_components['db']
                    
                    try:
                        # Check if username already exists
                        existing_student = db.get_student_by_username(new_username)
                        if existing_student:
                            st.error("Username already exists")
                        else:
                            # Check if email already exists
                            existing_email = db.get_student_by_email(new_email)
                            if existing_email:
                                st.error("Email already exists")
                            else:
                                # Create new student (simplified password handling)
                                student = db.create_student(new_username, new_email, new_password)
                                st.success("Account created successfully! Please login.")
                    except ValueError as ve:
                        st.error(f"Error: {str(ve)}")
                    except Exception as e:
                        st.error(f"Database error: {str(e)}")
                else:
                    st.error("Passwords do not match")
            else:
                st.error("Please fill all fields")

def dashboard_page(system_components):
    """Display student dashboard."""
    st.title(f"👋 Welcome, {st.session_state.username}!")
    st.markdown("---")
    
    db = system_components['db']
    
    # Force refresh data on each visit
    if 'last_refresh' not in st.session_state or st.session_state.get('force_refresh', False):
        st.session_state.last_refresh = datetime.now()
        st.session_state.force_refresh = False
    
    # Get fresh analytics - force database refresh
    recent_performances = db.get_student_performance(st.session_state.student_id)
    quiz_results = db.get_quiz_results(st.session_state.student_id)
    assignments = db.get_student_assignments(st.session_state.student_id)
    
    # Calculate real-time metrics
    # Get all unique topics from all activities
    all_topics = set()
    
    # Topics from performances
    if recent_performances:
        all_topics.update(p.topic for p in recent_performances)
    
    # Topics from quiz results
    if quiz_results:
        all_topics.update(q.topic for q in quiz_results)
    
    # Topics from assignments
    if assignments:
        all_topics.update(a.topic for a in assignments)
    
    total_topics = len(all_topics)
    total_quizzes_taken = len(quiz_results)
    total_assignments_completed = len([a for a in assignments if a.completed])
    
    # Calculate real-time average performance
    all_scores = []
    if recent_performances:
        all_scores = [p.score for p in recent_performances]
    if quiz_results:
        all_scores.extend([q.score for q in quiz_results])
    if assignments:
        all_scores.extend([a.score for a in assignments if a.score])
    
    avg_performance = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # Display overview cards with real-time data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Topics", total_topics)
    
    with col2:
        st.metric("Avg Performance", f"{avg_performance:.1f}%")
    
    with col3:
        st.metric("Quizzes Taken", total_quizzes_taken)
    
    with col4:
        st.metric("Assignments Done", total_assignments_completed)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📖 Start Learning", use_container_width=True):
            st.session_state.page = 'topics'
            st.rerun()
    
    with col2:
        if st.button("📝 Take Quiz", use_container_width=True):
            st.session_state.page = 'topics'
            st.rerun()
    
    with col3:
        if st.button("📋 View Assignments", use_container_width=True):
            st.session_state.page = 'assignments'
            st.rerun()
    
    # Weak areas (fresh data)
    weak_topics = db.get_weak_topics(st.session_state.student_id)
    if weak_topics:
        st.markdown("---")
        st.subheader("⚠️ Areas for Improvement")
        for topic in weak_topics:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📌 {topic}")
            with col2:
                if st.button(f"Practice {topic}", key=f"practice_{topic}"):
                    st.session_state.current_topic = topic
                    st.session_state.page = 'content'
                    st.rerun()

def topic_selection_page(system_components):
    """Display topic selection page."""
    st.title("📚 Select Topic and Difficulty")
    st.markdown("---")
    
    # Topic selection - allow custom input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic_option = st.selectbox(
            "Choose a topic or enter custom topic:",
            [
                "Python Programming",
                "Data Structures", 
                "Algorithms",
                "Machine Learning",
                "Web Development",
                "Database Management",
                "Computer Networks",
                "Operating Systems",
                "Custom Topic..."
            ],
            key="topic_selector"
        )
        
        if topic_option == "Custom Topic...":
            custom_topic = st.text_input(
                "Enter your custom topic:",
                placeholder="e.g., Artificial Intelligence, Data Science, etc.",
                key="custom_topic"
            )
            selected_topic = custom_topic if custom_topic else ""
        else:
            selected_topic = topic_option
    
    with col2:
        difficulty_levels = ["Beginner", "Intermediate", "Advanced"]
        selected_difficulty = st.selectbox("Difficulty Level:", difficulty_levels, key="difficulty_selector")
    
    # Store selections
    if selected_topic and selected_difficulty:
        st.session_state.current_topic = selected_topic
        st.session_state.current_difficulty = selected_difficulty
        
        # Show selections
        st.success(f"✅ Selected: {selected_topic} ({selected_difficulty})")
    
    st.markdown("---")
    
    # Action buttons (only enable if topic is selected)
    if selected_topic and selected_difficulty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📖 Generate Learning Content", use_container_width=True, key="gen_content"):
                st.session_state.page = 'content'
                st.rerun()
        
        with col2:
            if st.button("📝 Generate Quiz", use_container_width=True, key="gen_quiz"):
                st.session_state.page = 'quiz'
                st.rerun()
        
        with col3:
            if st.button("📋 Generate Assignments", use_container_width=True, key="gen_assignments"):
                st.session_state.page = 'assignments'
                st.rerun()
    else:
        st.info("👆 Please select a topic and difficulty level to continue")

def learning_content_page(system_components):
    """Display learning content page."""
    st.title("📖 Learning Content")
    st.markdown("---")
    
    if not st.session_state.current_topic:
        st.warning("Please select a topic first.")
        if st.button("Go to Topic Selection"):
            st.session_state.page = 'topics'
            st.rerun()
        return
    
    # Get student's current performance to determine actual level
    db = system_components['db']
    student_performances = db.get_student_performance(st.session_state.student_id)
    if student_performances:
        # Calculate student's actual performance level
        avg_score = sum(p.score for p in student_performances) / len(student_performances)
        if avg_score >= 70:
            actual_student_stage = 3  # Advanced
        elif avg_score >= 40:
            actual_student_stage = 2  # Intermediate
        else:
            actual_student_stage = 1  # Beginner
    else:
        actual_student_stage = 1  # Default to Beginner
    
    # Generate content
    if st.button("� Generate Learning Content", use_container_width=True, key="gen_content"):
        with st.spinner("Generating personalized learning content..."):
            try:
                # Get student analyzer to determine learning stage
                student_analyzer = system_components['student_analyzer']
                
                # Create student data for analysis
                student_data = {
                    'student_id': st.session_state.student_id,
                    'performance_history': [
                        {
                            'score': p.score,
                            'topic': p.topic,
                            'difficulty': p.difficulty_level
                        }
                        for p in student_performances
                    ] if student_performances else [],
                    'current_stage': actual_student_stage,
                    'quiz_results': [],
                    'weak_topics': []
                }
                
                # Analyze student performance
                analysis = student_analyzer.analyze_student_performance(student_data)
                recommended_stage = analysis.get('recommended_stage', actual_student_stage)
                
                # Generate content using student's actual level
                content_generator = system_components['content_generator']
                content = content_generator.generate_personalized_content({
                    'student_id': st.session_state.student_id,
                    'topic': st.session_state.current_topic,
                    'difficulty_level': st.session_state.current_difficulty,
                    'student_stage': recommended_stage,  # Use recommended stage
                    'content_type': 'learning_materials'
                })
                
                st.session_state.learning_content = content
                st.success("Content generated successfully!")
                
                # Debug: Print content keys
                st.write("Debug - Content keys:", list(content.keys()))
                st.write(f"Debug - Student actual stage: {actual_student_stage}, Recommended stage: {recommended_stage}")
                
            except Exception as e:
                st.error(f"Error generating content: {str(e)}")
    
    # Display content
    if st.session_state.learning_content:
        content = st.session_state.learning_content
        
        # Content header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader(f"Topic: {content['topic']}")
        with col2:
            st.metric("Difficulty", content['difficulty_level'])
        with col3:
            if 'student_stage' in content:
                st.metric("Stage", content['student_stage'])
            else:
                st.metric("Stage", "N/A")
        
        st.markdown("---")
        
        # Learning objectives
        if content.get('learning_objectives'):
            st.subheader("🎯 Learning Objectives")
            for obj in content['learning_objectives']:
                st.write(f"• {obj}")
            st.markdown("---")
        
        # Main content
        if content.get('content'):
            st.subheader("📚 Content")
            st.write(content['content'])
            st.markdown("---")
        
        # Key concepts
        if content.get('key_concepts'):
            st.subheader("🔑 Key Concepts")
            if isinstance(content['key_concepts'], list) and content['key_concepts']:
                for concept in content['key_concepts']:
                    if concept:  # Ensure concept is not empty/None
                        if isinstance(concept, dict):
                            # Handle new format with concept and explanation
                            concept_name = concept.get('concept', '')
                            explanation = concept.get('explanation', '')
                            if concept_name:
                                st.write(f"**{concept_name}**")
                                if explanation:
                                    st.write(f"   {explanation}")
                        else:
                            # Handle old format (simple string)
                            st.write(f"• {concept}")
            else:
                st.write("Key concepts will be available after content generation.")
            st.markdown("---")
        
        # Examples
        if content.get('examples'):
            st.subheader("💡 Examples")
            if isinstance(content['examples'], list) and content['examples']:
                for i, example in enumerate(content['examples'], 1):
                    with st.expander(f"Example {i}"):
                        if isinstance(example, dict):
                            title = example.get('title', f'Example {i}')
                            description = example.get('description', '')
                            code = example.get('code')
                            explanation = example.get('explanation', '')
                            
                            st.write(f"**{title}**")
                            if description:
                                st.write(description)
                            if code and code != 'null':
                                # Display code as regular text instead of code block
                                st.write("**Code:**")
                                st.write(code)
                            if explanation:
                                st.write(explanation)
                        else:
                            st.write(str(example))  # Handle non-dict examples
            else:
                st.write("Examples will be available after content generation.")
            st.markdown("---")
        
        # Exercises
        if content.get('exercises'):
            st.subheader("🏋️ Practice Exercises")
            if isinstance(content['exercises'], list) and content['exercises']:
                for i, exercise in enumerate(content['exercises'], 1):
                    with st.expander(f"Exercise {i}"):
                        if isinstance(exercise, dict):
                            question = exercise.get('question', exercise.get('description', ''))
                            description = exercise.get('description', '')
                            hints = exercise.get('hints', [])
                            solution = exercise.get('solution', '')
                            
                            if question:
                                st.write(f"**Question:** {question}")
                            if description:
                                st.write(description)
                            if hints:
                                st.info(f"💡 Hints: {', '.join(hints)}")
                            if solution:
                                with st.expander("💡 Solution"):
                                    if solution and solution != 'null':
                                        # Display solution as regular text instead of code block
                                        st.write(solution)
                        else:
                            st.write(str(exercise))  # Handle non-dict exercises
            else:
                st.write("Practice exercises will be available after content generation.")
            st.markdown("---")
        
        # Summary
        if content.get('summary'):
            st.subheader("📝 Summary")
            st.write(content['summary'])
        
        # Action buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 Take Quiz on This Topic"):
                st.session_state.page = 'quiz'
                st.rerun()
        
        with col2:
            if st.button("📋 View Assignments"):
                st.session_state.page = 'assignments'
                st.rerun()

def quiz_page(system_components):
    """Display quiz page."""
    st.title("📝 Quiz")
    st.markdown("---")
    
    if not st.session_state.current_topic:
        st.warning("Please select a topic first.")
        if st.button("Go to Topic Selection"):
            st.session_state.page = 'topics'
            st.rerun()
        return
    
    # Generate quiz button
    if st.button("🔄 Generate New Quiz", key="generate_quiz"):
        with st.spinner("Generating personalized quiz..."):
            try:
                db = system_components['db']
                student = db.get_student_by_id(st.session_state.student_id)
                
                quiz_request = {
                    'student_id': st.session_state.student_id,
                    'topic': st.session_state.current_topic,
                    'difficulty_level': st.session_state.current_difficulty,
                    'student_stage': student.current_stage,
                    'question_count': 5,
                    'question_types': ['MCQ'],
                    'focus_areas': db.get_weak_topics(st.session_state.student_id)
                }
                
                quiz = system_components['quiz_generator'].generate_quiz(quiz_request)
                st.session_state.current_quiz = quiz
                st.session_state.quiz_answers = [''] * len(quiz['questions'])
                st.success("Quiz generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating quiz: {str(e)}")
    
    # Display quiz
    if st.session_state.current_quiz:
        quiz = st.session_state.current_quiz
        
        # Quiz header
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.subheader(f"Topic: {quiz['topic']}")
        with col2:
            # Use correct key or provide default
            total_questions = quiz.get('total_questions', len(quiz.get('questions', [])))
            st.metric("Questions", total_questions)
        with col3:
            # Use correct key or provide default
            time_limit = quiz.get('time_limit', 'N/A')
            if time_limit != 'N/A':
                st.metric("Time Limit", f"{time_limit} min")
            else:
                st.metric("Time Limit", "N/A")
        with col4:
            # Use correct key or provide default
            passing_score = quiz.get('passing_score', 70)
            st.metric("Passing Score", f"{passing_score}%")
        
        st.markdown("---")
        
        # Instructions
        st.info(quiz.get('instructions', 'Read each question carefully and select the best answer.'))
        
        # Questions
        answers = []
        for i, question in enumerate(quiz['questions']):
            st.subheader(f"Question {i+1}")
            st.write(question.get('question', 'Question text not available'))
            
            if question.get('type') == 'MCQ':
                options = [opt['text'] for opt in question.get('options', [])]
                selected_option = st.radio(
                    f"Select your answer:",
                    options,
                    key=f"q_{i}",
                    index=None
                )
                
                # Store answer
                if selected_option:
                    # Find the letter corresponding to selected option
                    for opt in question.get('options', []):
                        if opt['text'] == selected_option:
                            answers.append(opt.get('letter', ''))
                            break
                else:
                    answers.append('')
            else:
                answers.append('')
        
        # Submit button
        if st.button("📤 Submit Quiz", type="primary"):
            if all(answers):
                with st.spinner("Evaluating your answers..."):
                    try:
                        evaluation_request = {
                            'student_id': st.session_state.student_id,
                            'quiz_id': quiz.get('quiz_id', f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                            'questions': quiz['questions'],
                            'student_answers': answers,
                            'topic': quiz['topic'],
                            'difficulty_level': quiz['difficulty_level']
                        }
                        
                        results = system_components['evaluator'].evaluate_quiz_answers(evaluation_request)
                        
                        # Save results to database
                        db = system_components['db']
                        db.save_quiz_result(
                            st.session_state.student_id,
                            quiz['topic'],
                            quiz['questions'],
                            answers,
                            [q['correct_answer'] for q in quiz['questions']],
                            results['score_percentage'],
                            0  # time_taken
                        )
                        
                        # Display results
                        st.session_state.quiz_results = results
                        st.session_state.page = 'quiz_results'
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error evaluating quiz: {str(e)}")
            else:
                st.error("Please answer all questions before submitting.")

def quiz_results_page(system_components):
    """Display quiz results page."""
    st.title("📊 Quiz Results")
    st.markdown("---")
    
    if not st.session_state.get('quiz_results'):
        st.warning("No quiz results available.")
        st.session_state.page = 'quiz'
        st.rerun()
        return
    
    results = st.session_state.quiz_results
    
    # Score summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Score", f"{results['score_percentage']:.1f}%")
    with col2:
        st.metric("Grade", results['grade'])
    with col3:
        st.metric("Correct", f"{results['correct_answers']}/{results['total_questions']}")
    with col4:
        st.metric("Result", "✅ Passed" if results['passed'] else "❌ Failed")
    
    st.markdown("---")
    
    # Feedback
    if results.get('detailed_feedback'):
        st.subheader("📝 Feedback")
        st.write(results['detailed_feedback'])
        st.markdown("---")
    
    # Strengths and improvements
    col1, col2 = st.columns(2)
    
    with col1:
        if results.get('strengths'):
            st.subheader("💪 Strengths")
            for strength in results['strengths']:
                st.write(f"✅ {strength}")
    
    with col2:
        if results.get('improvement_areas'):
            st.subheader("🎯 Areas for Improvement")
            for area in results['improvement_areas']:
                st.write(f"📌 {area}")
    
    st.markdown("---")
    
    # Question analysis
    st.subheader("📋 Question Analysis")
    for i, q_analysis in enumerate(results['question_analysis']):
        with st.expander(f"Question {q_analysis['question_id']} - {'✅ Correct' if q_analysis['is_correct'] else '❌ Incorrect'}"):
            st.write(f"**Question:** {q_analysis['question_text']}")
            st.write(f"**Your Answer:** {q_analysis['student_answer']}")
            st.write(f"**Correct Answer:** {q_analysis['correct_answer']}")
            if q_analysis.get('explanation'):
                st.write(f"**Explanation:** {q_analysis['explanation']}")
    
    st.markdown("---")
    
    # Recommendations
    if results.get('recommendations'):
        st.subheader("🚀 Recommendations")
        for rec in results['recommendations']:
            st.write(f"• {rec}")
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📖 Study More"):
            st.session_state.page = 'content'
            st.rerun()
    
    with col2:
        if st.button("📝 Try Another Quiz"):
            st.session_state.current_quiz = None
            st.session_state.quiz_results = None
            st.session_state.page = 'quiz'
            st.rerun()
    
    with col3:
        if st.button("📊 View Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()

def assignments_page(system_components):
    """Display assignments page."""
    st.title("📋 Assignments")
    st.markdown("---")
    
    if not st.session_state.current_topic:
        st.warning("Please select a topic first.")
        if st.button("Go to Topic Selection"):
            st.session_state.page = 'topics'
            st.rerun()
        return
    
    # Generate assignments button
    if st.button("🔄 Generate Assignments", key="generate_assignments"):
        with st.spinner("Generating personalized assignments..."):
            try:
                db = system_components['db']
                student = db.get_student_by_id(st.session_state.student_id)
                
                assignment_request = {
                    'student_id': st.session_state.student_id,
                    'topic': st.session_state.current_topic,
                    'difficulty_level': st.session_state.current_difficulty,
                    'student_stage': student.current_stage,
                    'assignment_count': 4,
                    'focus_areas': db.get_weak_topics(st.session_state.student_id),
                    'assignment_types': ['mixed']
                }
                
                assignments = system_components['assignment_generator'].generate_assignments(assignment_request)
                st.session_state.current_assignments = assignments
                st.success("Assignments generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating assignments: {str(e)}")
    
    # Display assignments
    if st.session_state.get('current_assignments'):
        assignments = st.session_state.current_assignments
        
        # Assignments header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader(f"Topic: {assignments['topic']}")
        with col2:
            # Use the correct key for total assignments
            total_assignments = len(assignments.get('assignments', []))
            st.metric("Total", total_assignments)
        with col3:
            # Use the correct key or provide default
            est_time = assignments.get('estimated_completion_time', 'N/A')
            st.metric("Est. Time", est_time)
        
        st.markdown("---")
        
        # Learning objectives
        if assignments.get('learning_objectives'):
            st.subheader("🎯 Learning Objectives")
            for obj in assignments['learning_objectives']:
                st.write(f"• {obj}")
            st.markdown("---")
        
        # Individual assignments
        for i, assignment in enumerate(assignments['assignments'], 1):
            with st.expander(f"Assignment {i}: {assignment['title']}"):
                st.write(f"**Type:** {assignment['type']}")
                st.write(f"**Difficulty:** {assignment['difficulty']}")
                st.write(f"**Estimated Time:** {assignment['estimated_time']}")
                
                description = assignment.get('description', '')
                if description:
                    st.write("**Description:**")
                    st.write(description)
                
                instructions = assignment.get('instructions', [])
                if instructions:
                    st.write("**Instructions:**")
                    for j, instruction in enumerate(instructions, 1):
                        st.write(f"{j}. {instruction}")
                
                deliverables = assignment.get('deliverables', [])
                if deliverables:
                    st.write("**Deliverables:**")
                    for deliverable in deliverables:
                        st.write(f"• {deliverable}")
                
                # Assignment submission
                st.write("**Submit Your Work:**")
                submission = st.text_area(
                    "Enter your assignment submission here:",
                    height=200,
                    key=f"assignment_submission_{i}"
                )
                
                if st.button(f"Submit Assignment {i}", key=f"submit_{i}"):
                    if submission.strip():
                        # Save submission to database
                        db = system_components['db']
                        try:
                            # Create assignment record first
                            assignment_record = db.create_assignment(
                                st.session_state.student_id,
                                assignments['topic'],
                                assignments['difficulty_level'],
                                assignment['description']
                            )
                            
                            # Enhanced validation and scoring
                            word_count = len(submission.split())
                            char_count = len(submission)
                            sentences = len([s for s in submission.split('.') if s.strip()])
                            
                            # Quality assessment
                            quality_score = 0
                            
                            # Word count scoring
                            if word_count >= 100:
                                quality_score += 40
                            elif word_count >= 50:
                                quality_score += 30
                            elif word_count >= 25:
                                quality_score += 20
                            elif word_count >= 10:
                                quality_score += 10
                            
                            # Sentence structure scoring
                            if sentences >= 5:
                                quality_score += 20
                            elif sentences >= 3:
                                quality_score += 15
                            elif sentences >= 2:
                                quality_score += 10
                            elif sentences >= 1:
                                quality_score += 5
                            
                            # Content length scoring
                            if char_count >= 500:
                                quality_score += 20
                            elif char_count >= 300:
                                quality_score += 15
                            elif char_count >= 150:
                                quality_score += 10
                            elif char_count >= 50:
                                quality_score += 5
                            
                            # Technical content bonus for programming topics
                            if any(tech in assignments['topic'].lower() for tech in ['python', 'programming', 'code', 'algorithm', 'data structure']):
                                if any(keyword in submission.lower() for keyword in ['function', 'variable', 'loop', 'class', 'method', 'import', 'def']):
                                    quality_score += 10
                            
                            # Cap score at 100
                            score = min(100, quality_score)
                            
                            # Mark assignment as completed
                            completed_assignment = db.complete_assignment(assignment_record.id, score)
                            
                            if completed_assignment and completed_assignment.score:
                                st.success(f"✅ Assignment {i} submitted successfully!")
                                st.info(f"📊 Score: {score}/100 (Words: {word_count}, Sentences: {sentences})")
                                
                                # Provide feedback based on score
                                if score >= 80:
                                    st.success("🌟 Excellent work! Comprehensive submission.")
                                elif score >= 60:
                                    st.info("👍 Good work! Consider adding more details.")
                                elif score >= 40:
                                    st.warning("📝 Acceptable. Try to elaborate more on concepts.")
                                else:
                                    st.error("⚠️ Needs improvement. Please provide more detailed response.")
                                
                                # Update session state to refresh data (but don't rerun immediately)
                                st.session_state.assignments_submitted = True
                            else:
                                st.error("❌ Failed to save assignment score to database")
                            
                        except Exception as e:
                            st.error(f"❌ Error submitting assignment: {str(e)}")
                    else:
                        st.warning("⚠️ Please enter your assignment submission before submitting.")
                
                st.markdown("---")
                
                evaluation_criteria = assignment.get('evaluation_criteria')
                if evaluation_criteria:
                    st.write("**Evaluation Criteria:**")
                    for criteria in evaluation_criteria:
                        st.write(f"• {criteria.get('criterion', '')}: {criteria.get('weight', '')}")
        
        st.markdown("---")
        
        # Download assignments
        if st.button("📄 Download Assignments as PDF"):
            try:
                # Generate PDF report
                report_data = {
                    'student_info': {
                        'username': st.session_state.username,
                        'student_id': st.session_state.student_id
                    },
                    'assignments': assignments,
                    'topic': assignments['topic'],
                    'report_id': f"ASSIGN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
                
                pdf_path = system_components['pdf_generator'].generate_student_report(report_data)
                
                # Provide download link
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_file.read(),
                        file_name=f"assignments_{assignments['topic']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")

def performance_analytics_page(system_components):
    """Display performance analytics page."""
    st.title("📊 Performance Analytics")
    st.markdown("---")
    
    db = system_components['db']
    
    # Get comprehensive analytics
    analytics = db.get_student_analytics(st.session_state.student_id)
    
    # Performance overview
    st.subheader("📈 Performance Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Topics", analytics['total_topics'])
    with col2:
        st.metric("Avg Performance", f"{analytics['average_performance_score']:.1f}%")
    with col3:
        st.metric("Quizzes Taken", analytics['total_quizzes_taken'])
    with col4:
        st.metric("Assignments Done", analytics['total_assignments_completed'])
    
    st.markdown("---")
    
    # Performance visualization
    if analytics['topic_averages']:
        st.subheader("📊 Topic Performance Analysis")
        
        import plotly.express as px
        import pandas as pd
        
        # Create performance chart
        df = pd.DataFrame(list(analytics['topic_averages'].items()), 
                         columns=['Topic', 'Average Score'])
        
        fig = px.bar(df, x='Topic', y='Average Score', 
                    title="Performance by Topic",
                    labels={'Average Score': 'Score (%)'},
                    color='Average Score',
                    color_continuous_scale='viridis')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance summary
        st.subheader("📋 Performance Summary")
        
        # Calculate performance categories
        scores = list(analytics['topic_averages'].values())
        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score >= 70:
                performance_level = "Excellent Performance 🌟"
                color = "green"
            elif avg_score >= 50:
                performance_level = "Good Performance 👍"
                color = "blue"
            else:
                performance_level = "Needs Improvement 📈"
                color = "orange"
            
            st.markdown(f"**Overall Performance Level:** <span style='color:{color};font-weight:bold'>{performance_level}</span>", 
                       unsafe_allow_html=True)
            st.write(f"**Average Score Across All Topics:** {avg_score:.1f}%")
            
            # Best and worst performing topics
            if len(scores) > 1:
                best_topic = max(analytics['topic_averages'].items(), key=lambda x: x[1])
                worst_topic = min(analytics['topic_averages'].items(), key=lambda x: x[1])
                
                st.write(f"**Best Performing Topic:** {best_topic[0]} ({best_topic[1]:.1f}%)")
                st.write(f"**Topic Needing Focus:** {worst_topic[0]} ({worst_topic[1]:.1f}%)")
    
    st.markdown("---")
    
    # Weak areas
    if analytics['weak_topics']:
        st.subheader("⚠️ Areas Needing Attention")
        for topic in analytics['weak_topics']:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📌 {topic}")
            with col2:
                if st.button(f"Practice {topic}", key=f"practice_{topic}"):
                    st.session_state.current_topic = topic
                    st.session_state.page = 'content'
                    st.rerun()
    
    st.markdown("---")
    
    # Recent performance history
    st.subheader("📜 Recent Performance")
    
    recent_performances = db.get_student_performance(st.session_state.student_id)
    if recent_performances:
        for perf in recent_performances[:10]:
            with st.expander(f"{perf.topic} - {perf.score:.1f}% ({perf.created_at.strftime('%Y-%m-%d %H:%M')})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Difficulty:** {perf.difficulty_level}")
                with col2:
                    st.write(f"**Stage:** {perf.stage}")
                with col3:
                    st.write(f"**Attempts:** {perf.attempts}")
                
                if perf.weak_topics:
                    weak_topics = json.loads(perf.weak_topics) if isinstance(perf.weak_topics, str) else perf.weak_topics
                    st.write("**Weak Areas Identified:**")
                    for topic in weak_topics:
                        st.write(f"• {topic}")
    
    # Generate full report button
    st.markdown("---")
    if st.button("📄 Generate Full Performance Report", type="primary"):
        with st.spinner("Generating comprehensive report..."):
            try:
                # Collect all data for the report
                report_data = {
                    'student_info': {
                        'username': st.session_state.username,
                        'student_id': st.session_state.student_id,
                        'total_topics': analytics['total_topics']
                    },
                    'performance_analytics': analytics,
                    'topic': st.session_state.current_topic or 'General',
                    'report_id': f"PERF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
                
                pdf_path = system_components['pdf_generator'].generate_student_report(report_data)
                
                # Provide download link
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Download Performance Report",
                        data=pdf_file.read(),
                        file_name=f"performance_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                
                st.success("Performance report generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

def main():
    """Main application function."""
    # Initialize session state
    init_session_state()
    
    # Initialize system
    try:
        system_components = initialize_system()
    except Exception as e:
        st.error(f"Error initializing system: {str(e)}")
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🎓 Navigation")
        
        if st.session_state.logged_in:
            st.write(f"👤 **{st.session_state.username}**")
            st.markdown("---")
            
            pages = {
                'dashboard': '🏠 Dashboard',
                'topics': '📚 Topics',
                'content': '📖 Learning Content',
                'quiz': '📝 Quiz',
                'assignments': '📋 Assignments'
            }
            
            for page_key, page_name in pages.items():
                if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.page = page_key
                    st.rerun()
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                # Clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                init_session_state()
                st.rerun()
        else:
            st.info("Please login to access the system.")
    
    # Main content area
    if not st.session_state.logged_in:
        login_page(system_components)
    else:
        # Determine current page
        current_page = st.session_state.get('page', 'dashboard')
        
        if current_page == 'dashboard':
            dashboard_page(system_components)
        elif current_page == 'topics':
            topic_selection_page(system_components)
        elif current_page == 'content':
            learning_content_page(system_components)
        elif current_page == 'quiz':
            quiz_page(system_components)
        elif current_page == 'quiz_results':
            quiz_results_page(system_components)
        elif current_page == 'assignments':
            assignments_page(system_components)
        elif current_page == 'analytics':
            performance_analytics_page(system_components)
        else:
            dashboard_page(system_components)

if __name__ == "__main__":
    main()
