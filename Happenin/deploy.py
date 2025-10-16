#!/usr/bin/env python3
"""
Happenin Deployment Script
==========================

This script handles the complete deployment process:
1. Runs comprehensive validation tests
2. Checks environment setup
3. Validates all functionality
4. Provides deployment instructions
5. Monitors deployment status

Usage:
    python deploy.py [--skip-tests] [--force]
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime

def print_banner():
    """Print deployment banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🚀 HAPPENIN DEPLOYMENT                    ║
║                Create, Share, Celebrate                      ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_git_status():
    """Check git status and ensure clean working directory"""
    print("🔍 Checking Git Status...")
    
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("⚠️  Uncommitted changes detected:")
            print(result.stdout)
            
            response = input("\n❓ Do you want to commit these changes? (y/n): ").lower()
            if response == 'y':
                commit_message = input("Enter commit message (or press Enter for auto-message): ").strip()
                if not commit_message:
                    commit_message = f"Deployment preparation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                print("✅ Changes committed successfully")
            else:
                print("❌ Please commit or stash changes before deployment")
                return False
        
        # Check if we're on main branch
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()
        
        if current_branch != 'main':
            print(f"⚠️  Currently on branch '{current_branch}', not 'main'")
            response = input("❓ Switch to main branch? (y/n): ").lower()
            if response == 'y':
                subprocess.run(['git', 'checkout', 'main'], check=True)
                print("✅ Switched to main branch")
            else:
                print("❌ Please switch to main branch before deployment")
                return False
        
        print("✅ Git status clean")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return False
    except FileNotFoundError:
        print("❌ Git not found. Please install Git.")
        return False

def run_validation_tests():
    """Run comprehensive validation tests"""
    print("\n🧪 Running Deployment Validation Tests...")
    print("=" * 50)
    
    try:
        result = subprocess.run([sys.executable, 'test_deployment_validation.py'], 
                              capture_output=True, text=True, check=True)
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        print("✅ All validation tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Validation tests failed:")
        print(e.stdout)
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("❌ Python not found. Please check your Python installation.")
        return False

def check_requirements():
    """Check if requirements.txt exists and is valid"""
    print("\n📋 Checking Requirements...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip()
        
        if not requirements:
            print("❌ requirements.txt is empty")
            return False
        
        print("✅ requirements.txt found and valid")
        print(f"📦 Dependencies: {len(requirements.splitlines())} packages")
        return True
        
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def check_app_structure():
    """Check if app.py exists and has required structure"""
    print("\n🏗️  Checking App Structure...")
    
    if not os.path.exists('app.py'):
        print("❌ app.py not found")
        return False
    
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check for critical functions
        critical_functions = [
            'show_event_creation_page',
            'show_event_admin_page', 
            'show_public_invite_page',
            'get_page',
            'save_invitation',
            'load_invitation',
            'save_rsvp',
            'send_test_email'
        ]
        
        missing_functions = []
        for func in critical_functions:
            if f'def {func}(' not in app_content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing critical functions: {', '.join(missing_functions)}")
            return False
        
        print("✅ App structure valid")
        return True
        
    except Exception as e:
        print(f"❌ Error checking app.py: {e}")
        return False

def check_secrets_template():
    """Check if secrets template exists"""
    print("\n🔐 Checking Security Configuration...")
    
    # Check if there's a secrets template or documentation
    secrets_files = [
        '.streamlit/secrets.toml.example',
        'secrets.toml.example',
        'DEPLOYMENT_GUIDE.md'
    ]
    
    found_template = False
    for file in secrets_files:
        if os.path.exists(file):
            print(f"✅ Found secrets template: {file}")
            found_template = True
            break
    
    if not found_template:
        print("⚠️  No secrets template found")
        print("💡 Consider creating a secrets.toml.example file")
    
    return True

def push_to_github():
    """Push changes to GitHub"""
    print("\n📤 Pushing to GitHub...")
    
    try:
        # Check if remote exists
        result = subprocess.run(['git', 'remote', '-v'], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("❌ No Git remote configured")
            print("💡 Add a remote with: git remote add origin <your-repo-url>")
            return False
        
        # Push to main branch
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Successfully pushed to GitHub")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to push to GitHub: {e}")
        return False

def show_deployment_instructions():
    """Show deployment instructions for Streamlit Cloud"""
    print("\n🚀 STREAMLIT CLOUD DEPLOYMENT INSTRUCTIONS")
    print("=" * 50)
    
    print("""
1. 📱 Go to https://share.streamlit.io
2. 🔗 Connect your GitHub repository
3. ⚙️  Configure your app:
   - App URL: Your chosen URL
   - Branch: main
   - Main file: app.py
4. 🔐 Add secrets in Settings → Secrets:
   
   [secrets]
   SMTP_USER = "your-email@gmail.com"
   SMTP_PASS = "your-app-password"
   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = "587"
   SMTP_TLS = "true"
   RSVP_NOTIFY_EMAIL = "your-notification-email@gmail.com"

5. 🚀 Click "Deploy!"
6. ⏳ Wait for deployment to complete
7. 🎉 Your app will be live at: https://your-app-name.streamlit.app

📧 Gmail Setup (if using Gmail):
   - Enable 2FA on your Gmail account
   - Generate App Password: Google Account → Security → App passwords
   - Use the App Password (not your regular password)
    """)

def show_post_deployment_checklist():
    """Show post-deployment checklist"""
    print("\n✅ POST-DEPLOYMENT CHECKLIST")
    print("=" * 30)
    
    print("""
□ Test app loads correctly
□ Test event creation
□ Test invitation preview
□ Test RSVP submission
□ Test email notifications
□ Test admin dashboard
□ Test public invite page
□ Test file uploads (image/music)
□ Test responsive design
□ Test error handling
□ Verify all URLs work
□ Check logs for errors
□ Test with different browsers
□ Test on mobile devices
    """)

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Deploy Happenin app to Streamlit Cloud')
    parser.add_argument('--skip-tests', action='store_true', 
                       help='Skip validation tests (not recommended)')
    parser.add_argument('--force', action='store_true',
                       help='Force deployment even if tests fail')
    parser.add_argument('--no-push', action='store_true',
                       help='Skip pushing to GitHub')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Pre-deployment checks
    print("🔍 PRE-DEPLOYMENT CHECKS")
    print("=" * 30)
    
    checks_passed = 0
    total_checks = 5
    
    # Check 1: Git status
    if check_git_status():
        checks_passed += 1
    
    # Check 2: Requirements
    if check_requirements():
        checks_passed += 1
    
    # Check 3: App structure
    if check_app_structure():
        checks_passed += 1
    
    # Check 4: Secrets template
    if check_secrets_template():
        checks_passed += 1
    
    # Check 5: Validation tests
    if args.skip_tests:
        print("\n⚠️  Skipping validation tests (not recommended)")
        checks_passed += 1
    else:
        if run_validation_tests():
            checks_passed += 1
    
    print(f"\n📊 Pre-deployment checks: {checks_passed}/{total_checks} passed")
    
    if checks_passed < total_checks and not args.force:
        print("\n❌ DEPLOYMENT BLOCKED!")
        print("Please fix the failing checks before deployment.")
        print("Use --force to deploy anyway (not recommended)")
        return False
    
    # Push to GitHub
    if not args.no_push:
        if not push_to_github():
            print("\n❌ Failed to push to GitHub")
            return False
    
    # Show deployment instructions
    show_deployment_instructions()
    
    # Show post-deployment checklist
    show_post_deployment_checklist()
    
    print("\n🎉 DEPLOYMENT PREPARATION COMPLETE!")
    print("Your Happenin app is ready for Streamlit Cloud deployment.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
