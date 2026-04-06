import streamlit as st
import sys
import os
from datetime import datetime
import json

# Run setup (for Streamlit Cloud)
os.system("python simple_setup.py")

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# ✅ FIXED IMPORTS (MAIN FIX)
from models import create_tables, get_db
from db import DatabaseManager
from vector_store import VectorStore
from retriever import RAGRetriever
from student_analyzer import StudentAnalyzer
from content_generator import ContentGenerator
from assignments_generator import AssignmentGenerator
from quiz_generator import QuizGenerator
from evaluator import Evaluator
from recommendation_agent import RecommendationAgent
from report_generator import PDFReportGenerator


# ---------------- SESSION STATE ---------------- #
def init_session_state():
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


# ---------------- SYSTEM INIT ---------------- #
@st.cache_resource
def initialize_system():
    create_tables()

    vector_store = VectorStore()
    retriever = RAGRetriever(vector_store)

    try:
        retriever.initialize_sample_content()
    except Exception:
        pass

    groq_api_key = os.getenv('GROQ_API_KEY') or st.secrets.get('GROQ_API_KEY')

    if not groq_api_key:
        st.error("GROQ API key not found")
        st.stop()

    return {
        'db': DatabaseManager(next(get_db())),
        'vector_store': vector_store,
        'retriever': retriever,
        'student_analyzer': StudentAnalyzer(groq_api_key),
        'content_generator': ContentGenerator(groq_api_key, rag_retriever=retriever),
        'assignment_generator': AssignmentGenerator(groq_api_key),
        'quiz_generator': QuizGenerator(groq_api_key),
        'evaluator': Evaluator(groq_api_key),
        'recommendation_agent': RecommendationAgent(groq_api_key),
        'pdf_generator': PDFReportGenerator()
    }


# ---------------- LOGIN ---------------- #
def login_page(system):
    st.title("🎓 AI-Based Adaptive Learning System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        db = system['db']
        user = db.get_student_by_username(username)

        if user and user.password_hash == password:
            st.session_state.logged_in = True
            st.session_state.student_id = user.id
            st.session_state.username = user.username
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")


# ---------------- DASHBOARD ---------------- #
def dashboard(system):
    st.title(f"👋 Welcome {st.session_state.username}")

    db = system['db']
    perf = db.get_student_performance(st.session_state.student_id)

    st.metric("Total Records", len(perf))

    if st.button("Start Learning"):
        st.session_state.page = "topics"
        st.rerun()


# ---------------- TOPICS ---------------- #
def topics():
    st.title("📚 Select Topic")

    topic = st.text_input("Enter Topic")
    difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])

    if st.button("Continue"):
        st.session_state.current_topic = topic
        st.session_state.current_difficulty = difficulty
        st.session_state.page = "content"
        st.rerun()


# ---------------- CONTENT ---------------- #
def content(system):
    st.title("📖 Learning Content")

    if st.button("Generate Content"):
        generator = system['content_generator']

        data = {
            'student_id': st.session_state.student_id,
            'topic': st.session_state.current_topic,
            'difficulty_level': st.session_state.current_difficulty
        }

        try:
            result = generator.generate_personalized_content(data)
            st.write(result)
        except Exception as e:
            st.error(str(e))


# ---------------- QUIZ ---------------- #
def quiz(system):
    st.title("📝 Quiz")

    if st.button("Generate Quiz"):
        try:
            quiz_data = system['quiz_generator'].generate_quiz({
                'topic': st.session_state.current_topic
            })
            st.write(quiz_data)
        except Exception as e:
            st.error(str(e))


# ---------------- MAIN ---------------- #
def main():
    init_session_state()

    try:
        system = initialize_system()
    except Exception as e:
        st.error(f"System error: {e}")
        return

    if not st.session_state.logged_in:
        login_page(system)
        return

    page = st.session_state.get("page", "dashboard")

    if page == "dashboard":
        dashboard(system)
    elif page == "topics":
        topics()
    elif page == "content":
        content(system)
    elif page == "quiz":
        quiz(system)


if __name__ == "__main__":
    main()
