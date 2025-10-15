#!/usr/bin/env python3
"""
Test cases for HemanthVerse Invitations App
Run this file to validate the invitation system functionality
"""

import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, mock_open
import sys
import base64

# Add the current directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import functions from app.py
from app import (
    validate_event_data,
    save_invitation,
    load_invitation,
    create_test_invitation,
    TEST_EVENT_DATA,
    get_local_image_base64,
    get_local_music_base64,
    load_local_file,
    save_rsvp,
    load_rsvps,
    get_rsvp_analytics
)

class TestInvitationValidation(unittest.TestCase):
    """Test cases for invitation data validation"""
    
    def test_valid_event_data(self):
        """Test validation with complete valid data"""
        valid_data = {
            "event_name": "Test Event",
            "host_names": "Test Host",
            "event_date": "2025-11-13",
            "event_time": "4:00 PM",
            "venue_address": "Test Venue",
            "invitation_message": "Test message"
        }
        
        is_valid, message = validate_event_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid")
    
    def test_missing_event_name(self):
        """Test validation with missing event name"""
        invalid_data = {
            "host_names": "Test Host",
            "event_date": "2025-11-13",
            "event_time": "4:00 PM",
            "venue_address": "Test Venue",
            "invitation_message": "Test message"
        }
        
        is_valid, message = validate_event_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("event_name", message)
    
    def test_empty_event_name(self):
        """Test validation with empty event name"""
        invalid_data = {
            "event_name": "",
            "host_names": "Test Host",
            "event_date": "2025-11-13",
            "event_time": "4:00 PM",
            "venue_address": "Test Venue",
            "invitation_message": "Test message"
        }
        
        is_valid, message = validate_event_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("event_name", message)
    
    def test_multiple_missing_fields(self):
        """Test validation with multiple missing fields"""
        invalid_data = {
            "event_name": "Test Event",
            "host_names": "",
            "event_date": "2025-11-13",
            "event_time": "",
            "venue_address": "Test Venue",
            "invitation_message": ""
        }
        
        is_valid, message = validate_event_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("host_names", message)
        self.assertIn("event_time", message)
        self.assertIn("invitation_message", message)

class TestInvitationStorage(unittest.TestCase):
    """Test cases for invitation storage and retrieval"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_db_path = "invitations"
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('app.DB_PATH', new_callable=lambda: "invitations")
    def test_save_invitation(self, mock_db_path):
        """Test saving invitation data"""
        # Create the directory for testing
        os.makedirs("invitations", exist_ok=True)
        
        test_data = {
            "event_name": "Test Event",
            "host_names": "Test Host",
            "event_date": "2025-11-13",
            "event_time": "4:00 PM",
            "venue_address": "Test Venue",
            "invitation_message": "Test message",
            "theme": "Temple"
        }
        
        invite_id = save_invitation(test_data)
        
        # Check that invite_id is generated
        self.assertIsNotNone(invite_id)
        self.assertIsInstance(invite_id, str)
        
        # Check that file was created
        file_path = os.path.join("invitations", f"{invite_id}.json")
        self.assertTrue(os.path.exists(file_path))
        
        # Check file contents
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["event_name"], "Test Event")
        self.assertEqual(saved_data["host_names"], "Test Host")
    
    @patch('app.DB_PATH', new_callable=lambda: "invitations")
    def test_load_invitation(self, mock_db_path):
        """Test loading invitation data"""
        # Create the directory for testing
        os.makedirs("invitations", exist_ok=True)
        
        test_data = {
            "event_name": "Test Event",
            "host_names": "Test Host",
            "event_date": "2025-11-13",
            "event_time": "4:00 PM",
            "venue_address": "Test Venue",
            "invitation_message": "Test message",
            "theme": "Temple"
        }
        
        # Save invitation first
        invite_id = save_invitation(test_data)
        
        # Load invitation
        loaded_data = load_invitation(invite_id)
        
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data["event_name"], "Test Event")
        self.assertEqual(loaded_data["host_names"], "Test Host")
    
    @patch('app.DB_PATH', new_callable=lambda: "invitations")
    def test_load_nonexistent_invitation(self, mock_db_path):
        """Test loading non-existent invitation"""
        loaded_data = load_invitation("nonexistent-id")
        self.assertIsNone(loaded_data)

class TestLocalFileHandling(unittest.TestCase):
    """Test cases for local file handling"""
    
    def setUp(self):
        """Set up test files"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test image file
        self.test_image_path = os.path.join(self.test_dir, "test_image.png")
        with open(self.test_image_path, 'wb') as f:
            f.write(b"fake_image_data")
        
        # Create test music file
        self.test_music_path = os.path.join(self.test_dir, "test_music.mp3")
        with open(self.test_music_path, 'wb') as f:
            f.write(b"fake_music_data")
    
    def tearDown(self):
        """Clean up test files"""
        shutil.rmtree(self.test_dir)
    
    def test_load_local_file_exists(self):
        """Test loading existing local file"""
        result = load_local_file(self.test_image_path)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        # Decode and verify content
        decoded = base64.b64decode(result)
        self.assertEqual(decoded, b"fake_image_data")
    
    def test_load_local_file_not_exists(self):
        """Test loading non-existent local file"""
        result = load_local_file(os.path.join(self.test_dir, "nonexistent.png"))
        self.assertIsNone(result)
    
    @patch('app.load_local_file')
    def test_get_local_image_base64(self, mock_load_file):
        """Test getting local image as base64"""
        mock_load_file.return_value = "base64_encoded_image"
        
        result = get_local_image_base64()
        
        self.assertEqual(result, "base64_encoded_image")
        mock_load_file.assert_called_once_with("IMG_7653.PNG")
    
    @patch('app.load_local_file')
    def test_get_local_music_base64(self, mock_load_file):
        """Test getting local music as base64"""
        mock_load_file.return_value = "base64_encoded_music"
        
        result = get_local_music_base64()
        
        self.assertEqual(result, "base64_encoded_music")
        mock_load_file.assert_called_once_with("mridangam-tishra-33904.mp3")

class TestTestData(unittest.TestCase):
    """Test cases for test data structure"""
    
    def test_test_event_data_structure(self):
        """Test that test event data has all required fields"""
        required_fields = [
            "event_name", "host_names", "event_date", "event_time",
            "venue_address", "invocation", "invitation_message", "theme",
            "image_file", "music_file"
        ]
        
        for field in required_fields:
            self.assertIn(field, TEST_EVENT_DATA)
            self.assertIsNotNone(TEST_EVENT_DATA[field])
    
    def test_test_event_data_values(self):
        """Test specific values in test event data"""
        self.assertEqual(TEST_EVENT_DATA["event_name"], "Shubha Gruha Praveshah")
        self.assertEqual(TEST_EVENT_DATA["host_names"], "Mounika , Hemanth & Viraj")
        self.assertEqual(TEST_EVENT_DATA["event_date"], "2025-11-13")
        self.assertEqual(TEST_EVENT_DATA["event_time"], "4:00 PM")
        self.assertEqual(TEST_EVENT_DATA["venue_address"], "3108 Honerywood Drive, Leander, TX -78641")
        self.assertEqual(TEST_EVENT_DATA["invocation"], "ॐ श्री गणेशाय नमः")
        self.assertEqual(TEST_EVENT_DATA["theme"], "Temple")
        self.assertEqual(TEST_EVENT_DATA["image_file"], "IMG_7653.PNG")
        self.assertEqual(TEST_EVENT_DATA["music_file"], "mridangam-tishra-33904.mp3")
    
    def test_test_event_data_validation(self):
        """Test that test event data passes validation"""
        test_data = {
            "event_name": TEST_EVENT_DATA["event_name"],
            "host_names": TEST_EVENT_DATA["host_names"],
            "event_date": TEST_EVENT_DATA["event_date"],
            "event_time": TEST_EVENT_DATA["event_time"],
            "venue_address": TEST_EVENT_DATA["venue_address"],
            "invitation_message": TEST_EVENT_DATA["invitation_message"]
        }
        
        is_valid, message = validate_event_data(test_data)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid")

class TestCreateTestInvitation(unittest.TestCase):
    """Test cases for creating test invitations"""
    
    @patch('app.get_local_image_base64')
    @patch('app.get_local_music_base64')
    @patch('app.save_invitation')
    def test_create_test_invitation_success(self, mock_save, mock_music, mock_image):
        """Test successful creation of test invitation"""
        mock_image.return_value = "base64_image"
        mock_music.return_value = "base64_music"
        mock_save.return_value = "test_invite_id"
        
        invite_id, message = create_test_invitation()
        
        self.assertEqual(invite_id, "test_invite_id")
        self.assertEqual(message, "Test invitation created successfully")
        
        # Verify save_invitation was called with correct data
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        
        self.assertEqual(saved_data["event_name"], TEST_EVENT_DATA["event_name"])
        self.assertEqual(saved_data["host_names"], TEST_EVENT_DATA["host_names"])
        self.assertEqual(saved_data["image_base64"], "base64_image")
        self.assertEqual(saved_data["music_base64"], "base64_music")
    
    @patch('app.validate_event_data')
    def test_create_test_invitation_validation_failure(self, mock_validate):
        """Test test invitation creation with validation failure"""
        mock_validate.return_value = (False, "Validation failed")
        
        invite_id, message = create_test_invitation()
        
        self.assertIsNone(invite_id)
        self.assertEqual(message, "Validation failed")

class TestRSVPFunctionality(unittest.TestCase):
    """Test cases for RSVP functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('app.DB_PATH', new_callable=lambda: "invitations")
    def test_save_rsvp(self, mock_db_path):
        """Test saving RSVP data"""
        os.makedirs("invitations", exist_ok=True)
        
        invite_id = "test-invite-123"
        rsvp_entry = {
            "name": "John Doe",
            "email": "john@example.com",
            "response": "Yes",
            "message": "Looking forward to it!",
            "timestamp": "2025-10-15T00:00:00"
        }
        
        save_rsvp(invite_id, rsvp_entry)
        
        # Check that RSVP file was created
        rsvp_file = f"invitations/rsvp_{invite_id}.json"
        self.assertTrue(os.path.exists(rsvp_file))
        
        # Check file contents
        with open(rsvp_file, 'r') as f:
            saved_rsvps = json.load(f)
        
        self.assertEqual(len(saved_rsvps), 1)
        self.assertEqual(saved_rsvps[0]["name"], "John Doe")
        self.assertEqual(saved_rsvps[0]["response"], "Yes")
    
    @patch('app.DB_PATH', new_callable=lambda: "invitations")
    def test_load_rsvps(self, mock_db_path):
        """Test loading RSVP data"""
        os.makedirs("invitations", exist_ok=True)
        
        invite_id = "test-invite-123"
        rsvp_entry = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "response": "No",
            "message": "Sorry, can't make it",
            "timestamp": "2025-10-15T00:00:00"
        }
        
        # Save RSVP first
        save_rsvp(invite_id, rsvp_entry)
        
        # Load RSVPs
        loaded_rsvps = load_rsvps(invite_id)
        
        self.assertEqual(len(loaded_rsvps), 1)
        self.assertEqual(loaded_rsvps[0]["name"], "Jane Smith")
        self.assertEqual(loaded_rsvps[0]["response"], "No")
    
    @patch('app.DB_PATH', new_callable=lambda: "invitations")
    def test_get_rsvp_analytics(self, mock_db_path):
        """Test RSVP analytics calculation"""
        os.makedirs("invitations", exist_ok=True)
        
        invite_id = "test-invite-123"
        
        # Add multiple RSVPs
        rsvps = [
            {"name": "Alice", "email": "alice@example.com", "response": "Yes", "message": "", "timestamp": "2025-10-15T00:00:00"},
            {"name": "Bob", "email": "bob@example.com", "response": "Yes", "message": "Excited!", "timestamp": "2025-10-15T00:01:00"},
            {"name": "Charlie", "email": "charlie@example.com", "response": "No", "message": "Out of town", "timestamp": "2025-10-15T00:02:00"},
            {"name": "Diana", "email": "diana@example.com", "response": "Maybe", "message": "Will confirm later", "timestamp": "2025-10-15T00:03:00"},
            {"name": "Eve", "email": "eve@example.com", "response": "Yes", "message": "", "timestamp": "2025-10-15T00:04:00"}
        ]
        
        for rsvp in rsvps:
            save_rsvp(invite_id, rsvp)
        
        # Get analytics
        analytics = get_rsvp_analytics(invite_id)
        
        self.assertEqual(analytics["total"], 5)
        self.assertEqual(analytics["yes"], 3)
        self.assertEqual(analytics["no"], 1)
        self.assertEqual(analytics["maybe"], 1)
        self.assertEqual(len(analytics["yes_list"]), 3)
        self.assertEqual(len(analytics["no_list"]), 1)
        self.assertEqual(len(analytics["maybe_list"]), 1)

def run_tests():
    """Run all test cases"""
    print("🧪 Running HemanthVerse Invitations Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestInvitationValidation,
        TestInvitationStorage,
        TestLocalFileHandling,
        TestTestData,
        TestCreateTestInvitation,
        TestRSVPFunctionality
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
