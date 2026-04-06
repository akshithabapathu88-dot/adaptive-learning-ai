"""
Simple setup script to verify system structure without full dependency installation.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from template."""
    env_example = Path('.env.example')
    env_file = Path('.env')
    
    if env_example.exists() and not env_file.exists():
        content = env_example.read_text()
        # Replace placeholder with instruction
        content = content.replace('your_groq_api_key_here', 'YOUR_ACTUAL_GROQ_API_KEY_HERE')
        env_file.write_text(content)
        print("✅ Created .env file from template")
        print("   Please edit .env and add your Groq API key")
        return True
    elif env_file.exists():
        print("ℹ️  .env file already exists")
        return True
    else:
        print("❌ .env.example not found")
        return False

def verify_structure():
    """Verify the project structure."""
    print("🔍 Verifying project structure...")
    
    required_structure = {
        'agents': [
            'student_analyzer.py',
            'content_generator.py', 
            'assignment_generator.py',
            'quiz_generator.py',
            'evaluator.py',
            'recommendation_agent.py'
        ],
        'rag': [
            'vector_store.py',
            'embeddings.py',
            'retriever.py'
        ],
        'database': [
            'models.py',
            'db.py'
        ],
        'frontend': [
            'streamlit_app.py'
        ],
        'pdf_generator': [
            'report_generator.py'
        ]
    }
    
    all_good = True
    
    for dir_name, files in required_structure.items():
        dir_path = Path(dir_name)
        if not dir_path.exists():
            print(f"   ❌ Directory {dir_name}/ not found")
            all_good = False
            continue
            
        print(f"   📁 {dir_name}/")
        for file_name in files:
            file_path = dir_path / file_name
            if file_path.exists():
                print(f"      ✅ {file_name}")
            else:
                print(f"      ❌ {file_name} - MISSING")
                all_good = False
    
    # Check root files
    root_files = ['main.py', 'requirements.txt', 'README.md', '.env.example']
    print("   📁 Root directory:")
    for file_name in root_files:
        if Path(file_name).exists():
            print(f"      ✅ {file_name}")
        else:
            print(f"      ❌ {file_name} - MISSING")
            all_good = False
    
    return all_good

def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def show_next_steps():
    """Show next steps for setup."""
    print("\n📋 Next Steps:")
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print("")
    print("2. Set up your Groq API key:")
    print("   - Edit .env file")
    print("   - Replace YOUR_ACTUAL_GROQ_API_KEY_HERE with your actual API key")
    print("")
    print("3. Initialize the system:")
    print("   python main.py setup")
    print("")
    print("4. Run the application:")
    print("   python main.py run")
    print("")
    print("5. Access the application:")
    print("   Open http://localhost:8501 in your browser")

def main():
    """Main setup function."""
    print("🎓 AI-Based Adaptive Learning System - Simple Setup")
    print("=" * 55)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Verify structure
    structure_ok = verify_structure()
    
    # Create .env file
    env_ok = create_env_file()
    
    print("\n" + "=" * 55)
    print("📊 Setup Results:")
    
    results = [
        ("Python Version", python_ok),
        ("Project Structure", structure_ok),
        ("Environment File", env_ok)
    ]
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Basic setup verification passed!")
        show_next_steps()
    else:
        print("\n⚠️  Some setup checks failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
