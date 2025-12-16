#!/usr/bin/env python
"""
Pharma Agentic AI - Launcher Script
Run this file to start the application.

Usage:
    python run.py          # Launch Streamlit UI
    python run.py --api    # Launch FastAPI backend
    python run.py --test   # Run validation tests
"""
import sys
import os
import subprocess
from pathlib import Path

# Check Python version - need 3.11, not 3.14
if sys.version_info >= (3, 14):
    # Try to find Python 3.11
    python311_paths = [
        r"C:\Users\Akhil\AppData\Local\Programs\Python\Python311\python.exe",
        r"C:\Python311\python.exe",
    ]
    for py_path in python311_paths:
        if os.path.exists(py_path):
            print("⚠️  Python 3.14 detected, switching to Python 3.11...")
            os.execv(py_path, [py_path] + sys.argv)
    print("❌ Python 3.11 not found. Please install it or run with:")
    print("   C:\\Users\\Akhil\\AppData\\Local\\Programs\\Python\\Python311\\python.exe run.py")
    sys.exit(1)

# Set project root
PROJECT_ROOT = Path(__file__).parent.absolute()
os.chdir(PROJECT_ROOT)

# Add src to path
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def check_dependencies():
    """Check if required packages are installed."""
    required = ["crewai", "groq", "streamlit", "fastapi", "chromadb"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    return True


def check_env():
    """Check if .env file exists and has API key."""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your-groq-api-key-here":
        print("❌ GROQ_API_KEY not set in .env file")
        return False
    
    print(f"✅ Groq API key configured")
    print(f"✅ Model: {os.getenv('GROQ_MODEL', 'llama3-70b-8192')}")
    return True


def run_streamlit():
    """Launch the Streamlit UI."""
    print("\n" + "=" * 50)
    print("  🚀 Launching Pharma Agentic AI")
    print("=" * 50)
    
    if not check_dependencies():
        return
    if not check_env():
        return
    
    print("\n📊 Starting Streamlit server...")
    print("   URL: http://localhost:8501")
    print("   Press Ctrl+C to stop\n")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        str(PROJECT_ROOT / "app.py"),
        "--server.port", "8501",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])


def run_api():
    """Launch the FastAPI backend."""
    print("\n" + "=" * 50)
    print("  🚀 Launching Pharma Agentic AI API")
    print("=" * 50)
    
    if not check_dependencies():
        return
    if not check_env():
        return
    
    print("\n🔌 Starting FastAPI server...")
    print("   URL: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop\n")
    
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "src.api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])


def run_tests():
    """Run validation tests."""
    print("\n" + "=" * 50)
    print("  🧪 Running Validation Tests")
    print("=" * 50 + "\n")
    
    subprocess.run([sys.executable, str(PROJECT_ROOT / "test_golden_tasks.py")])


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if "--api" in args:
        run_api()
    elif "--test" in args:
        run_tests()
    else:
        run_streamlit()


if __name__ == "__main__":
    main()
