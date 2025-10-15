#!/usr/bin/env python3
"""
Local Preview Script for HemanthVerse Invitations
This script helps you test the invitation system locally without deployment
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_files():
    """Check if required files exist"""
    required_files = [
        "app.py",
        "IMG_7653.PNG", 
        "mridangam-tishra-33904.mp3",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files found")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def run_streamlit():
    """Run Streamlit app"""
    print("🚀 Starting Streamlit app...")
    print("📱 The app will open in your browser automatically")
    print("🔗 Local URL: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"], 
                      check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        return False
    
    return True

def run_tests():
    """Run test suite"""
    print("🧪 Running test suite...")
    try:
        result = subprocess.run([sys.executable, "test_invitations.py"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed!")
            return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def show_usage_instructions():
    """Show usage instructions"""
    print("""
🎯 HemanthVerse Invitations - Local Preview Guide
================================================

📋 Available Commands:
1. Check files and dependencies
2. Install dependencies  
3. Run tests
4. Start local preview
5. Show usage instructions
6. Exit

💡 Quick Start:
   - Run command 1 to check everything is ready
   - Run command 2 to install dependencies
   - Run command 4 to start the local preview
   - Open http://localhost:8501 in your browser

🧪 Testing:
   - Use the "Create Test Invitation" button in the app
   - This will create an invitation using your local files
   - Test the RSVP functionality
   - Validate the invitation display

📁 File Structure:
   - app.py: Main Streamlit application
   - IMG_7653.PNG: Background image for invitations
   - mridangam-tishra-33904.mp3: Background music
   - requirements.txt: Python dependencies
   - test_invitations.py: Test suite

🔧 Troubleshooting:
   - Make sure all files are in the same directory
   - Check that Python and pip are installed
   - Ensure port 8501 is available
   - Check console output for error messages
""")

def main():
    """Main function"""
    print("🎉 Welcome to HemanthVerse Invitations Local Preview!")
    print("=" * 60)
    
    while True:
        print("\n📋 Choose an option:")
        print("1. Check files and dependencies")
        print("2. Install dependencies")
        print("3. Run tests")
        print("4. Start local preview")
        print("5. Show usage instructions")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            check_files()
            
        elif choice == "2":
            if not check_files():
                continue
            install_dependencies()
            
        elif choice == "3":
            if not check_files():
                continue
            run_tests()
            
        elif choice == "4":
            if not check_files():
                continue
            if not install_dependencies():
                continue
            run_streamlit()
            
        elif choice == "5":
            show_usage_instructions()
            
        elif choice == "6":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()

