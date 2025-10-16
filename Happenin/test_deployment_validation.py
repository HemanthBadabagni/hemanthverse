#!/usr/bin/env python3
"""
Comprehensive Deployment Validation Tests for Happenin App
==========================================================

This script validates all critical functionality before deployment:
- App startup and basic functionality
- Event creation and data persistence
- RSVP functionality and email notifications
- File handling and image processing
- URL generation and routing
- Error handling and edge cases

Run this before every deployment to ensure everything works correctly.
"""

import os
import sys
import json
import base64
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, time
import io
from PIL import Image

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app functions
from app import (
    load_local_file, get_local_image_base64, get_local_music_base64,
    compute_average_luminance, choose_text_color, get_smtp_config,
    send_test_email, validate_event_data, create_test_invitation,
    save_invitation, load_invitation, get_base_url, save_rsvp,
    load_rsvps, get_rsvp_analytics, export_rsvps_csv, clear_rsvps,
    display_invitation_card, get_page, show_event_creation_page,
    show_event_admin_page, show_public_invite_page, TEST_EVENT_DATA
)

class DeploymentValidationTests(unittest.TestCase):
    """Comprehensive tests to validate deployment readiness"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_db_path = os.getenv('DB_PATH', 'invitations')
        
        # Create test directories
        os.makedirs(os.path.join(self.test_dir, 'invitations'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'rsvps'), exist_ok=True)
        
        # Create a test image
        self.test_image = Image.new('RGB', (800, 600), color='red')
        self.test_image_path = os.path.join(self.test_dir, 'test_image.png')
        self.test_image.save(self.test_image_path)
        
        # Create test music file (dummy)
        self.test_music_path = os.path.join(self.test_dir, 'test_music.mp3')
        with open(self.test_music_path, 'wb') as f:
            f.write(b'dummy music content')
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_app_imports(self):
        """Test that all required modules can be imported"""
        try:
            import streamlit as st
            import PIL
            from PIL import Image
            import smtplib
            from email.message import EmailMessage
            import base64
            import uuid
            import logging
            print("✅ All required imports successful")
        except ImportError as e:
            self.fail(f"❌ Import error: {e}")
    
    def test_local_file_handling(self):
        """Test local file loading functionality"""
        with patch('app.DB_PATH', self.test_dir):
            # Test image loading
            image_data = load_local_file(self.test_image_path)
            self.assertIsNotNone(image_data)
            self.assertIsInstance(image_data, str)
            
            # Test music loading
            music_data = load_local_file(self.test_music_path)
            self.assertIsNotNone(music_data)
            self.assertIsInstance(music_data, str)
            
            print("✅ Local file handling working correctly")
    
    def test_image_processing(self):
        """Test image processing and color analysis"""
        with patch('app.DB_PATH', self.test_dir):
            # Test luminance computation
            image_bytes = base64.b64encode(open(self.test_image_path, 'rb').read()).decode('utf-8')
            luminance = compute_average_luminance(image_bytes)
            self.assertIsInstance(luminance, float)
            self.assertGreaterEqual(luminance, 0)
            self.assertLessEqual(luminance, 255)
            
            # Test text color selection
            text_color = choose_text_color(image_bytes, mode="Auto")
            self.assertIn(text_color, ["#000000", "#FFFFFF"])
            
            print("✅ Image processing working correctly")
    
    def test_smtp_configuration(self):
        """Test SMTP configuration retrieval"""
        # Test with environment variables
        with patch.dict(os.environ, {
            'SMTP_USER': 'test@example.com',
            'SMTP_PASS': 'testpass',
            'SMTP_HOST': 'smtp.gmail.com',
            'SMTP_PORT': '587',
            'SMTP_TLS': 'true',
            'RSVP_NOTIFY_EMAIL': 'notify@example.com'
        }):
            config = get_smtp_config()
            self.assertEqual(config['user'], 'test@example.com')
            self.assertEqual(config['password'], 'testpass')
            self.assertEqual(config['host'], 'smtp.gmail.com')
            self.assertEqual(config['port'], '587')
            self.assertEqual(config['tls'], 'true')
            self.assertEqual(config['notify_email'], 'notify@example.com')
        
        print("✅ SMTP configuration working correctly")
    
    @patch('smtplib.SMTP')
    def test_email_functionality(self, mock_smtp):
        """Test email sending functionality"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        with patch.dict(os.environ, {
            'SMTP_USER': 'test@example.com',
            'SMTP_PASS': 'testpass',
            'SMTP_HOST': 'smtp.gmail.com',
            'SMTP_PORT': '587',
            'SMTP_TLS': 'true'
        }):
            # Test test email
            success, message = send_test_email('recipient@example.com')
            self.assertTrue(success)
            self.assertIn('sent', message.lower())
            
            # Verify SMTP was called correctly
            mock_smtp.assert_called_once_with('smtp.gmail.com', 587, timeout=15)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('test@example.com', 'testpass')
            mock_server.send_message.assert_called_once()
        
        print("✅ Email functionality working correctly")
    
    def test_event_data_validation(self):
        """Test event data validation"""
        # Valid data
        valid_data = {
            'event_name': 'Test Event',
            'host_names': 'Test Host',
            'event_date': '2025-01-01',
            'event_time': '4:00 PM',
            'venue_address': 'Test Venue',
            'invitation_message': 'Test message'
        }
        self.assertTrue(validate_event_data(valid_data))
        
        # Invalid data (missing required fields)
        invalid_data = {
            'event_name': '',
            'host_names': 'Test Host'
        }
        self.assertFalse(validate_event_data(invalid_data))
        
        print("✅ Event data validation working correctly")
    
    def test_invitation_persistence(self):
        """Test invitation saving and loading"""
        with patch('app.DB_PATH', self.test_dir):
            # Test data
            test_data = {
                'event_name': 'Test Event',
                'host_names': 'Test Host',
                'event_date': '2025-01-01',
                'event_time': '4:00 PM',
                'venue_address': 'Test Venue',
                'invitation_message': 'Test message',
                'image_base64': 'dummy_image_data',
                'music_base64': 'dummy_music_data',
                'created_at': str(datetime.utcnow())
            }
            
            # Save invitation
            invite_id = save_invitation(test_data)
            self.assertIsNotNone(invite_id)
            self.assertIsInstance(invite_id, str)
            
            # Load invitation
            loaded_data = load_invitation(invite_id)
            self.assertIsNotNone(loaded_data)
            self.assertEqual(loaded_data['event_name'], 'Test Event')
            self.assertEqual(loaded_data['host_names'], 'Test Host')
            
            print("✅ Invitation persistence working correctly")
    
    def test_rsvp_functionality(self):
        """Test RSVP saving, loading, and analytics"""
        with patch('app.DB_PATH', self.test_dir):
            # Create test invitation first
            test_data = {
                'event_name': 'Test Event',
                'host_names': 'Test Host',
                'event_date': '2025-01-01',
                'event_time': '4:00 PM',
                'venue_address': 'Test Venue',
                'invitation_message': 'Test message',
                'created_at': str(datetime.utcnow())
            }
            invite_id = save_invitation(test_data)
            
            # Test RSVP entries
            rsvp_entries = [
                {
                    'name': 'John Doe',
                    'response': 'yes',
                    'adults': 2,
                    'kids': 1,
                    'comments': 'Looking forward to it!',
                    'timestamp': str(datetime.utcnow())
                },
                {
                    'name': 'Jane Smith',
                    'response': 'no',
                    'adults': 0,
                    'kids': 0,
                    'comments': 'Sorry, can\'t make it',
                    'timestamp': str(datetime.utcnow())
                }
            ]
            
            # Save RSVPs
            for rsvp in rsvp_entries:
                save_rsvp(invite_id, rsvp)
            
            # Load RSVPs
            loaded_rsvps = load_rsvps(invite_id)
            self.assertEqual(len(loaded_rsvps), 2)
            
            # Test analytics
            analytics = get_rsvp_analytics(invite_id)
            self.assertEqual(analytics['total_responses'], 2)
            self.assertEqual(analytics['yes_count'], 1)
            self.assertEqual(analytics['no_count'], 1)
            self.assertEqual(analytics['total_adults'], 2)
            self.assertEqual(analytics['total_children'], 1)
            
            print("✅ RSVP functionality working correctly")
    
    def test_csv_export(self):
        """Test CSV export functionality"""
        with patch('app.DB_PATH', self.test_dir):
            # Create test invitation and RSVPs
            test_data = {
                'event_name': 'Test Event',
                'host_names': 'Test Host',
                'event_date': '2025-01-01',
                'event_time': '4:00 PM',
                'venue_address': 'Test Venue',
                'invitation_message': 'Test message',
                'created_at': str(datetime.utcnow())
            }
            invite_id = save_invitation(test_data)
            
            rsvp_entry = {
                'name': 'John Doe',
                'response': 'yes',
                'adults': 2,
                'kids': 1,
                'comments': 'Looking forward to it!',
                'timestamp': str(datetime.utcnow())
            }
            save_rsvp(invite_id, rsvp_entry)
            
            # Test CSV export
            csv_data = export_rsvps_csv(invite_id)
            self.assertIsNotNone(csv_data)
            self.assertIn('John Doe', csv_data)
            self.assertIn('yes', csv_data)
            
            print("✅ CSV export working correctly")
    
    def test_url_generation(self):
        """Test URL generation for different pages"""
        base_url = get_base_url()
        self.assertIsNotNone(base_url)
        self.assertIn('http', base_url)
        
        # Test page routing
        with patch('streamlit.query_params') as mock_params:
            # Test creation page
            mock_params.get.side_effect = lambda key, default=None: None if key == 'invite' else default
            page = get_page()
            self.assertEqual(page, 'creation')
            
            # Test admin page
            mock_params.get.side_effect = lambda key, default=None: 'test-id' if key == 'invite' else ('true' if key == 'admin' else default)
            page = get_page()
            self.assertEqual(page, 'admin')
            
            # Test public page
            mock_params.get.side_effect = lambda key, default=None: 'test-id' if key == 'invite' else ('false' if key == 'admin' else default)
            page = get_page()
            self.assertEqual(page, 'public')
        
        print("✅ URL generation and routing working correctly")
    
    def test_test_data_creation(self):
        """Test test invitation creation"""
        with patch('app.DB_PATH', self.test_dir):
            # Mock local file functions
            with patch('app.get_local_image_base64') as mock_img, \
                 patch('app.get_local_music_base64') as mock_music:
                
                mock_img.return_value = 'dummy_image_data'
                mock_music.return_value = ('dummy_music_data', 'test.mp3')
                
                invite_id, message = create_test_invitation()
                self.assertIsNotNone(invite_id)
                self.assertIn('success', message.lower())
                
                # Verify test data was saved
                loaded_data = load_invitation(invite_id)
                self.assertEqual(loaded_data['event_name'], TEST_EVENT_DATA['event_name'])
                self.assertEqual(loaded_data['host_names'], TEST_EVENT_DATA['host_names'])
        
        print("✅ Test data creation working correctly")
    
    def test_error_handling(self):
        """Test error handling for edge cases"""
        with patch('app.DB_PATH', self.test_dir):
            # Test loading non-existent invitation
            result = load_invitation('non-existent-id')
            self.assertIsNone(result)
            
            # Test loading RSVPs for non-existent invitation
            rsvps = load_rsvps('non-existent-id')
            self.assertEqual(rsvps, [])
            
            # Test analytics for non-existent invitation
            analytics = get_rsvp_analytics('non-existent-id')
            self.assertEqual(analytics['total_responses'], 0)
            
            # Test invalid file loading
            result = load_local_file('non-existent-file.txt')
            self.assertIsNone(result)
        
        print("✅ Error handling working correctly")
    
    def test_clear_rsvps(self):
        """Test RSVP clearing functionality"""
        with patch('app.DB_PATH', self.test_dir):
            # Create test invitation and RSVPs
            test_data = {
                'event_name': 'Test Event',
                'host_names': 'Test Host',
                'event_date': '2025-01-01',
                'event_time': '4:00 PM',
                'venue_address': 'Test Venue',
                'invitation_message': 'Test message',
                'created_at': str(datetime.utcnow())
            }
            invite_id = save_invitation(test_data)
            
            rsvp_entry = {
                'name': 'John Doe',
                'response': 'yes',
                'adults': 2,
                'kids': 1,
                'comments': 'Looking forward to it!',
                'timestamp': str(datetime.utcnow())
            }
            save_rsvp(invite_id, rsvp_entry)
            
            # Verify RSVP exists
            rsvps = load_rsvps(invite_id)
            self.assertEqual(len(rsvps), 1)
            
            # Clear RSVPs
            clear_rsvps(invite_id)
            
            # Verify RSVPs are cleared
            rsvps = load_rsvps(invite_id)
            self.assertEqual(len(rsvps), 0)
        
        print("✅ RSVP clearing working correctly")


def run_deployment_validation():
    """Run all deployment validation tests"""
    print("🚀 Starting Happenin Deployment Validation Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(DeploymentValidationTests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests) * 100
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {total_tests - failures - errors}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if failures > 0:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED! Ready for deployment!")
        return True
    else:
        print(f"\n⚠️  {failures + errors} test(s) failed. Fix issues before deployment.")
        return False


def check_environment_setup():
    """Check if environment is properly set up for testing"""
    print("🔍 Checking Environment Setup...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check required packages
    required_packages = ['streamlit', 'PIL', 'smtplib']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                __import__(package)
            print(f"✅ {package}: Available")
        except ImportError:
            print(f"❌ {package}: Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ Environment setup complete!")
    return True


if __name__ == "__main__":
    print("🎯 Happenin Deployment Validation Suite")
    print("=====================================")
    
    # Check environment first
    if not check_environment_setup():
        print("❌ Environment setup incomplete. Please install missing packages.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Run validation tests
    success = run_deployment_validation()
    
    if success:
        print("\n🚀 DEPLOYMENT READY!")
        print("Your Happenin app is ready for deployment to Streamlit Cloud.")
        sys.exit(0)
    else:
        print("\n🛑 DEPLOYMENT BLOCKED!")
        print("Please fix the failing tests before deploying.")
        sys.exit(1)
