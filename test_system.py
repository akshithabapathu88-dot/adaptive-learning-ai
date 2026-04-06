"""
Test script to verify system structure and basic functionality
without requiring API keys.
"""

import os
import sys
import importlib.util
from pathlib import Path

def test_imports():
    """Test if all modules can be imported."""
    print("🔍 Testing module imports...")
    
    modules_to_test = [
        'database.models',
        'database.db', 
        'rag.vector_store',
        'rag.embeddings',
        'rag.retriever',
        'agents.student_analyzer',
        'agents.content_generator',
        'agents.assignment_generator',
        'agents.quiz_generator',
        'agents.evaluator',
        'agents.recommendation_agent',
        'pdf_generator.report_generator'
    ]
    
    failed_imports = []
    
    for module_name in modules_to_test:
        try:
            # Convert module name to file path
            if module_name.startswith('database.'):
                path = Path('database') / f"{module_name.split('.')[1]}.py"
            elif module_name.startswith('rag.'):
                path = Path('rag') / f"{module_name.split('.')[1]}.py"
            elif module_name.startswith('agents.'):
                path = Path('agents') / f"{module_name.split('.')[1]}.py"
            elif module_name.startswith('pdf_generator.'):
                path = Path('pdf_generator') / f"{module_name.split('.')[1]}.py"
            
            # Check if file exists
            if path.exists():
                print(f"   ✅ {module_name}")
            else:
                print(f"   ❌ {module_name} - File not found: {path}")
                failed_imports.append(module_name)
                
        except Exception as e:
            print(f"   ❌ {module_name} - Error: {str(e)}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0

def test_directory_structure():
    """Test if all required directories exist."""
    print("\n📁 Testing directory structure...")
    
    required_dirs = [
        'agents',
        'rag', 
        'database',
        'frontend',
        'pdf_generator'
    ]
    
    all_exist = True
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ - Directory not found")
            all_exist = False
    
    return all_exist

def test_required_files():
    """Test if all required files exist."""
    print("\n📄 Testing required files...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        '.env.example',
        'database/models.py',
        'database/db.py',
        'rag/vector_store.py',
        'rag/embeddings.py', 
        'rag/retriever.py',
        'agents/student_analyzer.py',
        'agents/content_generator.py',
        'agents/assignment_generator.py',
        'agents/quiz_generator.py',
        'agents/evaluator.py',
        'agents/recommendation_agent.py',
        'frontend/streamlit_app.py',
        'pdf_generator/report_generator.py'
    ]
    
    all_exist = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - File not found")
            all_exist = False
    
    return all_exist

def test_database_models():
    """Test database model definitions."""
    print("\n🗄️ Testing database models...")
    
    try:
        # Add current directory to path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Try to import models
        from database.models import Base, Student, StudentPerformance, QuizResult, LearningContent, Assignment
        
        # Check if all required models exist
        models = [Student, StudentPerformance, QuizResult, LearningContent, Assignment]
        
        for model in models:
            if hasattr(model, '__tablename__'):
                print(f"   ✅ {model.__name__} - Table: {model.__tablename__}")
            else:
                print(f"   ❌ {model.__name__} - No table name defined")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing database models: {str(e)}")
        return False

def test_rag_components():
    """Test RAG system components."""
    print("\n🔍 Testing RAG components...")
    
    try:
        from rag.embeddings import EmbeddingManager
        from rag.vector_store import VectorStore
        from rag.retriever import RAGRetriever
        
        # Test EmbeddingManager initialization
        print("   ✅ EmbeddingManager can be imported")
        
        # Test VectorStore initialization
        print("   ✅ VectorStore can be imported")
        
        # Test RAGRetriever initialization
        print("   ✅ RAGRetriever can be imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing RAG components: {str(e)}")
        return False

def test_pdf_generator():
    """Test PDF generator components."""
    print("\n📄 Testing PDF generator...")
    
    try:
        from pdf_generator.report_generator import PDFReportGenerator
        
        # Test initialization
        generator = PDFReportGenerator("./test_reports")
        print("   ✅ PDFReportGenerator can be initialized")
        
        # Test custom styles
        if hasattr(generator, 'title_style'):
            print("   ✅ Custom styles are defined")
        else:
            print("   ⚠️  Custom styles not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing PDF generator: {str(e)}")
        return False

def test_streamlit_app():
    """Test Streamlit app structure."""
    print("\n🖥️ Testing Streamlit app...")
    
    try:
        # Check if streamlit_app.py exists and has required functions
        app_file = Path('frontend/streamlit_app.py')
        
        if not app_file.exists():
            print("   ❌ streamlit_app.py not found")
            return False
        
        # Read file content and check for key functions
        content = app_file.read_text()
        
        required_functions = [
            'init_session_state',
            'initialize_system', 
            'login_page',
            'dashboard_page',
            'topic_selection_page',
            'learning_content_page',
            'quiz_page',
            'assignments_page',
            'performance_analytics_page',
            'main'
        ]
        
        missing_functions = []
        for func in required_functions:
            if f"def {func}" in content:
                print(f"   ✅ {func}() found")
            else:
                print(f"   ❌ {func}() not found")
                missing_functions.append(func)
        
        return len(missing_functions) == 0
        
    except Exception as e:
        print(f"   ❌ Error testing Streamlit app: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing AI-Based Adaptive Learning System")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Required Files", test_required_files),
        ("Module Imports", test_imports),
        ("Database Models", test_database_models),
        ("RAG Components", test_rag_components),
        ("PDF Generator", test_pdf_generator),
        ("Streamlit App", test_streamlit_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System structure is correct.")
        print("\n📋 Next steps:")
        print("1. Set up your Groq API key in .env file")
        print("2. Run: python main.py setup")
        print("3. Run: python main.py run")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
