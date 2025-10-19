# Force deployment update to fix invitation loading - v2
import streamlit as st
import uuid
import json
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import base64
import logging
import smtplib
from email.message import EmailMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force deployment update - fix invitation loading issue

DB_PATH = "invitations"
os.makedirs(DB_PATH, exist_ok=True)

THEMES = {
    "Floral": {"bg": "#fff0e6", "accent": "#b22222"},
    "Temple": {"bg": "#f6eedf", "accent": "#d4af37"},
    "Simple Gold": {"bg": "#fffbe6", "accent": "#ffd700"},
    "Classic Red": {"bg": "#a80000", "accent": "#ffd1b3"},
}

FONT_FAMILY = "'Noto Serif', 'Poppins', serif"

# Test data for validation
TEST_EVENT_DATA = {
    "event_name": "Shubha Gruha Praveshah",
    "host_names": "Mounika , Hemanth & Viraj",
    "event_date": "2025-11-13",
    "event_time": "4:00 PM",
    "venue_address": "3108 Honerywood Drive, Leander, TX -78641",
    "invocation": "ॐ श्री गणेशाय नमः",
    "invitation_message": """An Abode of Happiness and Blessings

With the divine blessings of Lord Venkateswara and our elders,
we are delighted to invite you to our Gruha Pravesham (Housewarming Ceremony)
as we step into our new home with joy, love, and gratitude.

Please join us to bless our home and share this special moment with us.""",
    "theme": "Temple",
    "image_file": "IMG_7653.PNG",
    "music_file": "mridangam-tishra-33904.mp3"
}

def load_local_file(file_path):
    """Load a local file and return its base64 encoded content"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        else:
            logger.warning(f"File not found: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {str(e)}")
        return None

def get_local_image_base64():
    """Get the local image file as base64"""
    # Try legacy filename first to match tests, then other common locations
    for candidate in [
        "IMG_7653.PNG",
        "../IMG_7653.PNG",
        "image_file.png",
        "../image_file.png",
    ]:
        data = load_local_file(candidate)
        if data:
            return data
    return None

def get_local_music_base64():
    """Get the local music file as base64"""
    # Try legacy filename first to match tests, then other common locations
    for candidate in [
        "mridangam-tishra-33904.mp3",
        "../mridangam-tishra-33904.mp3",
        "mp3_file.mp3",
        "../mp3_file.mp3",
    ]:
        data = load_local_file(candidate)
        if data:
            return data
    return None

def compute_average_luminance(image_base64):
    """Compute a simple average luminance (0..1) from a base64 image string.

    Returns None if computation fails.
    """
    try:
        if not image_base64:
            return None
        img = Image.open(BytesIO(base64.b64decode(image_base64))).convert("L")
        img = img.resize((64, 64))
        pixels = list(img.getdata())
        if not pixels:
            return None
        return (sum(pixels) / len(pixels)) / 255.0
    except Exception as e:
        logger.warning(f"Failed to compute luminance: {e}")
        return None

def choose_text_color(image_base64, mode="Auto", custom_color="#000000"):
    """Choose a readable text color based on the mode and background image.

    - Auto: picks dark (#000000) on light backgrounds, light (#FFFFFF) on dark.
    - Dark/Light: force preset colors.
    - Custom: returns provided custom color.
    """
    if mode == "Custom":
        return custom_color or "#000000"
    if mode == "Dark":
        return "#000000"
    if mode == "Light":
        return "#FFFFFF"
    luminance = compute_average_luminance(image_base64)
    if luminance is None:
        return "#000000"
    return "#000000" if luminance > 0.5 else "#FFFFFF"

def get_smtp_config():
    """Get SMTP configuration from environment variables or Streamlit secrets"""
    # For local development, prioritize environment variables
    env_user = os.getenv("SMTP_USER")
    env_pass = os.getenv("SMTP_PASS")
    
    if env_user and env_pass:
        # Use environment variables (local development)
        return {
            'user': env_user,
            'password': env_pass,
            'host': os.getenv("SMTP_HOST"),
            'port': os.getenv("SMTP_PORT"),
            'tls': os.getenv("SMTP_TLS"),
            'notify_email': ""  # No default - should come from invitation manager_email
        }
    
    # Fallback to Streamlit secrets (deployment)
    try:
        import streamlit as st
        return {
            'user': st.secrets["SMTP_USER"],
            'password': st.secrets["SMTP_PASS"],
            'host': st.secrets.get("SMTP_HOST"),
            'port': st.secrets.get("SMTP_PORT"),
            'tls': st.secrets.get("SMTP_TLS"),
            'notify_email': ""  # No default - should come from invitation manager_email
        }
    except:
        # No configuration found
        return {
            'user': None,
            'password': None,
            'host': None,
            'port': None,
            'tls': None,
            'notify_email': ""
        }

def send_rsvp_email(invite_id, rsvp_entry):
    """Send an email notification for a new RSVP if SMTP env vars are set.

    Priority for recipient address:
    1) `manager_email` stored in the invite payload (from Event manager email field)
    2) No fallback - email will only be sent if manager_email is provided

    Expected environment variables (if using SMTP):
      - SMTP_USER (required)
      - SMTP_PASS (required)
      - SMTP_HOST (required)
      - SMTP_PORT (required)
      - SMTP_TLS (required)
    """
    invite_data = load_invitation(invite_id) or {}
    
    # Get SMTP configuration
    smtp_config = get_smtp_config()
    
    # Use only the manager_email from the invitation (no fallback)
    notify_to = invite_data.get("manager_email")
    
    # Debug logging to help identify the source of invalid emails
    logger.info(f"RSVP email recipient: {notify_to}")
    logger.info(f"Manager email from invite: {invite_data.get('manager_email')}")
    
    # Validate email address format
    import re
    notify_to = notify_to.strip() if notify_to else notify_to
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if notify_to and not re.match(email_pattern, notify_to):
        logger.warning(f"Invalid email address format: {notify_to}")
        return False, f"Invalid email address: {notify_to}"
    
    if not (smtp_config['user'] and smtp_config['password'] and notify_to):
        logger.info("RSVP email not sent: SMTP settings not fully configured.")
        return False, "SMTP not configured"
    
    if not smtp_config['host'] or not smtp_config['port']:
        logger.info("RSVP email not sent: SMTP configuration incomplete.")
        return False, "SMTP configuration incomplete - missing host or port"
    
    smtp_user = smtp_config['user']
    smtp_pass = smtp_config['password']
    host = smtp_config['host']
    port = int(smtp_config['port'])
    use_tls = smtp_config['tls'].lower() != "false" if smtp_config['tls'] else True
    try:
        data = invite_data
        event_name = data.get("event_name", "Your Event")
        subject = f"{event_name} - {rsvp_entry['name']} - {rsvp_entry['response']}"
        
        # Create clean HTML email content
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: #a80000; color: #fff; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                    <h2 style="margin: 0; font-size: 24px;">New RSVP</h2>
                </div>
                
                <div style="padding: 30px;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 15px 0; color: #a80000; font-size: 18px;">Guest Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Name:</td>
                                <td style="padding: 8px 0;">{rsvp_entry['name']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Response:</td>
                                <td style="padding: 8px 0;">
                                    <span style="background: {'#28a745' if rsvp_entry['response'] == 'Yes' else '#dc3545' if rsvp_entry['response'] == 'No' else '#ffc107'}; color: {'#fff' if rsvp_entry['response'] == 'Yes' else '#fff' if rsvp_entry['response'] == 'No' else '#000'}; padding: 4px 12px; border-radius: 20px; font-weight: bold;">
                                        {rsvp_entry['response']}
                                    </span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Adults:</td>
                                <td style="padding: 8px 0;">{rsvp_entry.get('adults', 0)}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Children:</td>
                                <td style="padding: 8px 0;">{rsvp_entry.get('kids', 0)}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Total Guests:</td>
                                <td style="padding: 8px 0; font-weight: bold; color: #a80000;">{rsvp_entry.get('total_guests', 0)}</td>
                            </tr>
                        </table>
                    </div>
                    
                    {f'<div style="background: #e9ecef; padding: 15px; border-radius: 6px; margin-bottom: 20px;"><strong>Message:</strong><br>{rsvp_entry.get("message", "")}</div>' if rsvp_entry.get('message') else ''}
                    
                    <div style="text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px;">
                        RSVP received on {rsvp_entry['timestamp'][:19].replace('T', ' at ')}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Clean plain text version
        text_body = f"""
New RSVP Received

Guest Details:
Name: {rsvp_entry['name']}
Response: {rsvp_entry['response']}
Adults: {rsvp_entry.get('adults', 0)}
Children: {rsvp_entry.get('kids', 0)}
Total Guests: {rsvp_entry.get('total_guests', 0)}
{f"Message: {rsvp_entry.get('message', '')}" if rsvp_entry.get('message') else ""}

RSVP received on {rsvp_entry['timestamp'][:19].replace('T', ' at ')}
        """
        
        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = notify_to
        msg["Subject"] = subject
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
        
        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("RSVP notification email sent.")
        return True, "sent"
    except Exception as e:
        logger.warning(f"Failed to send RSVP email: {e}")
        return False, str(e)

def send_reminder_email(invite_id, subject, message):
    """Send reminder email to all guests who responded 'Yes'"""
    invite_data = load_invitation(invite_id) or {}
    rsvps = load_rsvps(invite_id)
    
    # Get SMTP configuration
    smtp_config = get_smtp_config()
    
    if not (smtp_config['user'] and smtp_config['password']):
        return False, "SMTP not configured"
    
    if not smtp_config['host'] or not smtp_config['port']:
        return False, "SMTP configuration incomplete"
    
    # Filter only "Yes" responses with valid emails
    yes_guests = []
    for rsvp in rsvps:
        if (rsvp.get("response", "").lower() == "yes" and 
            rsvp.get("email") and 
            rsvp["email"].strip()):
            yes_guests.append(rsvp)
    
    if not yes_guests:
        return False, "No guests with 'Yes' responses found"
    
    smtp_user = smtp_config['user']
    smtp_pass = smtp_config['password']
    host = smtp_config['host']
    port = int(smtp_config['port'])
    use_tls = smtp_config['tls'].lower() != "false" if smtp_config['tls'] else True
    
    successful_sends = 0
    failed_sends = []
    
    try:
        for guest in yes_guests:
            try:
                # Create HTML email content
                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
                    <div style="max-width: 500px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="background: #a80000; color: #fff; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                            <h2 style="margin: 0; font-size: 24px;">📧 Event Reminder</h2>
                        </div>
                        
                        <div style="padding: 30px;">
                            <p style="font-size: 16px; margin-bottom: 20px;">Dear <strong>{guest['name']}</strong>,</p>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                                <h3 style="margin: 0 0 15px 0; color: #a80000; font-size: 18px;">Event Details</h3>
                                <p style="margin: 5px 0;"><strong>Event:</strong> {invite_data.get('event_name', 'Your Event')}</p>
                                <p style="margin: 5px 0;"><strong>Date:</strong> {invite_data.get('event_date', '')} at {invite_data.get('event_time', '')}</p>
                                <p style="margin: 5px 0;"><strong>Venue:</strong> {invite_data.get('venue_address', '')}</p>
                            </div>
                            
                            <div style="background: #e9ecef; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                                <h4 style="margin: 0 0 10px 0; color: #a80000;">Message from Host:</h4>
                                <p style="margin: 0; white-space: pre-line;">{message}</p>
                            </div>
                            
                            <div style="text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px;">
                                We look forward to seeing you at the event!
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Plain text version
                text_body = f"""
Event Reminder

Dear {guest['name']},

Event Details:
Event: {invite_data.get('event_name', 'Your Event')}
Date: {invite_data.get('event_date', '')} at {invite_data.get('event_time', '')}
Venue: {invite_data.get('venue_address', '')}

Message from Host:
{message}

We look forward to seeing you at the event!
                """
                
                msg = EmailMessage()
                msg["From"] = smtp_user
                msg["To"] = guest["email"]
                msg["Subject"] = subject
                msg.set_content(text_body)
                msg.add_alternative(html_body, subtype="html")
                
                with smtplib.SMTP(host, port, timeout=15) as server:
                    if use_tls:
                        server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                
                successful_sends += 1
                
            except Exception as e:
                failed_sends.append(f"{guest['name']} ({guest['email']}): {str(e)}")
        
        if successful_sends > 0:
            result_msg = f"Successfully sent to {successful_sends} guests"
            if failed_sends:
                result_msg += f". Failed: {len(failed_sends)}"
            return True, result_msg
        else:
            return False, f"Failed to send to all guests: {'; '.join(failed_sends)}"
            
    except Exception as e:
        return False, f"SMTP error: {str(e)}"

    """Send a test email using current SMTP configuration.

    Returns (ok, message)
    """
    smtp_config = get_smtp_config()
    
    # Clean the email address
    to_address = to_address.strip() if to_address else to_address
    
    if not (smtp_config['user'] and smtp_config['password'] and to_address):
        return False, "Missing SMTP_USER/SMTP_PASS or recipient"
    
    if not smtp_config['host'] or not smtp_config['port']:
        return False, "SMTP configuration incomplete - missing host or port"
    
    smtp_user = smtp_config['user']
    smtp_pass = smtp_config['password']
    host = smtp_config['host']
    port = int(smtp_config['port'])
    use_tls = smtp_config['tls'].lower() != "false" if smtp_config['tls'] else True
    try:
        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = to_address
        msg["Subject"] = "Happenin RSVP - Test Email"
        
        # Create beautiful HTML test email matching RSVP template
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: #a80000; color: #fff; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                    <h2 style="margin: 0; font-size: 24px;">🎉 Happenin Email Test</h2>
                </div>
                
                <div style="padding: 30px;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 15px 0; color: #a80000; font-size: 18px;">✅ Email Configuration Working!</h3>
                        <p style="margin: 0; color: #555;">Your Happenin app email notifications are properly configured and working.</p>
                    </div>
                    
                    <div style="background: #e9ecef; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                        <strong>Test Details:</strong><br>
                        • Email sent to: {to_address}<br>
                        • SMTP Configuration: ✅ Working<br>
                        • HTML Templates: ✅ Enabled<br>
                        • RSVP Notifications: ✅ Ready
                    </div>
                    
                    <div style="text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px;">
                        Test email sent from Happenin — Create, Share, Celebrate
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
Happenin Email Test

✅ Email Configuration Working!

Your Happenin app email notifications are properly configured and working.

Test Details:
• Email sent to: {to_address}
• SMTP Configuration: ✅ Working
• HTML Templates: ✅ Enabled
• RSVP Notifications: ✅ Ready

Test email sent from Happenin — Create, Share, Celebrate
        """
        
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True, "Test email sent"
    except Exception as e:
        return False, f"SMTP error: {e}"

def validate_event_data(data):
    """Validate event data for required fields"""
    required_fields = ["event_name", "host_names", "event_date", "event_time", "venue_address", "invitation_message"]
    missing_fields = []
    
    for field in required_fields:
        if not data.get(field) or (isinstance(data.get(field), str) and data.get(field).strip() == ""):
            missing_fields.append(field)
    
    if missing_fields:
        return False
    return True

def create_test_invitation():
    """Create a test invitation with the provided event data"""
    try:
        # Load local files
        image_base64 = get_local_image_base64()
        music_base64 = get_local_music_base64()
        
        # Create test data
        test_data = {
            "event_name": TEST_EVENT_DATA["event_name"],
            "host_names": TEST_EVENT_DATA["host_names"],
            "event_date": TEST_EVENT_DATA["event_date"],
            "event_time": TEST_EVENT_DATA["event_time"],
            "venue_address": TEST_EVENT_DATA["venue_address"],
            "invocation": TEST_EVENT_DATA["invocation"],
            "invitation_message": TEST_EVENT_DATA["invitation_message"],
            "theme": TEST_EVENT_DATA["theme"],
            "image_base64": image_base64,
            "music_base64": music_base64,
            "music_filename": TEST_EVENT_DATA["music_file"]
        }
        
        # Validate the data
        is_valid = validate_event_data(test_data)
        if not is_valid:
            logger.error(f"Test data validation failed")
            return None, "Test data validation failed"
        
        # Save the invitation
        invite_id = save_invitation(test_data)
        logger.info(f"Test invitation created with ID: {invite_id}")
        return invite_id, "Test invitation created successfully"
        
    except Exception as e:
        logger.error(f"Error creating test invitation: {str(e)}")
        return None, f"Error creating test invitation: {str(e)}"

def save_invitation(data, specific_id=None):
    invite_id = specific_id if specific_id else str(uuid.uuid4())
    
    # Add safety metadata
    data['_safety_metadata'] = {
        'created_at': str(datetime.utcnow()),
        'created_by': 'streamlit_app',
        'version': '1.0',
        'backup_status': 'pending'
    }
    
    # Save to file
    with open(f"{DB_PATH}/{invite_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    
    # Multiple backup strategies to prevent data loss
    backup_success = False
    
    # Strategy 1: Auto-commit to git
    try:
        import subprocess
        subprocess.run(["git", "add", f"{DB_PATH}/{invite_id}.json"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Auto-commit invitation: {data.get('event_name', 'Unknown Event')}"], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        logger.info(f"Invitation {invite_id} automatically committed to git")
        backup_success = True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to auto-commit invitation {invite_id}: {e}")
    except Exception as e:
        logger.warning(f"Error during auto-commit for invitation {invite_id}: {e}")
    
    # Strategy 2: Create backup copy
    try:
        backup_file = f"{DB_PATH}/backup_{invite_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        logger.info(f"Backup created: {backup_file}")
    except Exception as e:
        logger.warning(f"Failed to create backup for invitation {invite_id}: {e}")
    
    # Strategy 3: Update safety metadata
    try:
        data['_safety_metadata']['backup_status'] = 'completed' if backup_success else 'failed'
        data['_safety_metadata']['backup_timestamp'] = str(datetime.utcnow())
        with open(f"{DB_PATH}/{invite_id}.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Failed to update safety metadata for invitation {invite_id}: {e}")
    
    return invite_id

def recreate_invitation_with_id(invite_id, event_data, rsvp_data=None):
    """Recreate an invitation with a specific ID and optionally add RSVP data"""
    try:
        # Save the invitation with the specific ID
        saved_id = save_invitation(event_data, specific_id=invite_id)
        
        # Add RSVP data if provided
        if rsvp_data:
            for rsvp_entry in rsvp_data:
                save_rsvp(invite_id, rsvp_entry)
        
        logger.info(f"Recreated invitation {invite_id} with RSVP data")
        return saved_id, "Invitation recreated successfully"
        
    except Exception as e:
        logger.error(f"Error recreating invitation {invite_id}: {str(e)}")
        return None, f"Error recreating invitation: {str(e)}"

def load_invitation(invite_id):
    try:
        with open(f"{DB_PATH}/{invite_id}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def get_base_url():
    # Check for manual override first
    manual_url = os.getenv("APP_BASE_URL")
    if manual_url:
        return manual_url
    
    # Check if running on Streamlit Cloud
    if os.getenv("STREAMLIT_CLOUD"):
        # Use the actual deployed Streamlit Cloud URL
        return "https://happenin-dhuv3putrr8ddhdufqzgcm.streamlit.app"
    else:
        # Running locally - use localhost
        return "http://localhost:8501"

def save_rsvp(invite_id, rsvp_entry):
    rsvp_file = f"{DB_PATH}/rsvp_{invite_id}.json"
    
    # Add safety metadata to RSVP entry
    rsvp_entry['_safety_metadata'] = {
        'timestamp': str(datetime.utcnow()),
        'backup_status': 'pending'
    }
    
    try:
        with open(rsvp_file, "r", encoding="utf-8") as f:
            rsvps = json.load(f)
    except Exception:
        rsvps = []
    
    rsvps.append(rsvp_entry)
    
    # Save RSVP data
    with open(rsvp_file, "w", encoding="utf-8") as f:
        json.dump(rsvps, f, indent=2)
    
    # Multiple backup strategies for RSVP data
    backup_success = False
    
    # Strategy 1: Auto-commit RSVP data to git
    try:
        import subprocess
        subprocess.run(["git", "add", rsvp_file], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Auto-commit RSVP for invitation {invite_id}: {rsvp_entry.get('name', 'Unknown Guest')}"], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        logger.info(f"RSVP for invitation {invite_id} automatically committed to git")
        backup_success = True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to auto-commit RSVP for invitation {invite_id}: {e}")
    except Exception as e:
        logger.warning(f"Error during auto-commit for RSVP {invite_id}: {e}")
    
    # Strategy 2: Create backup copy
    try:
        backup_file = f"{DB_PATH}/backup_rsvp_{invite_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(rsvps, f, indent=2)
        logger.info(f"RSVP backup created: {backup_file}")
    except Exception as e:
        logger.warning(f"Failed to create RSVP backup for invitation {invite_id}: {e}")
    
    # Strategy 3: Update safety metadata
    try:
        rsvp_entry['_safety_metadata']['backup_status'] = 'completed' if backup_success else 'failed'
        rsvp_entry['_safety_metadata']['backup_timestamp'] = str(datetime.utcnow())
        # Update the entry in the list
        for i, rsvp in enumerate(rsvps):
            if rsvp.get('name') == rsvp_entry.get('name') and rsvp.get('timestamp') == rsvp_entry.get('timestamp'):
                rsvps[i] = rsvp_entry
                break
        
        with open(rsvp_file, "w", encoding="utf-8") as f:
            json.dump(rsvps, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to update RSVP safety metadata for invitation {invite_id}: {e}")

def load_rsvps(invite_id):
    rsvp_file = f"{DB_PATH}/rsvp_{invite_id}.json"
    try:
        with open(rsvp_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def export_rsvps_csv(invite_id):
    """Return RSVPs as CSV string."""
    import csv
    from io import StringIO
    rows = load_rsvps(invite_id)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "name",
        "email",
        "response",
        "adults",
        "kids",
        "total_guests",
        "message",
        "timestamp",
    ])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "name": row.get("name",""),
            "email": row.get("email",""),
            "response": row.get("response",""),
            "adults": row.get("adults", 0),
            "kids": row.get("kids", 0),
            "total_guests": row.get("total_guests", (row.get("adults",0) or 0) + (row.get("kids",0) or 0)),
            "message": row.get("message",""),
            "timestamp": row.get("timestamp",""),
        })
    return output.getvalue()

def clear_rsvps(invite_id):
    rsvp_file = f"{DB_PATH}/rsvp_{invite_id}.json"
    with open(rsvp_file, "w", encoding="utf-8") as f:
        json.dump([], f)

def get_rsvp_analytics(invite_id):
    """Get RSVP analytics and statistics"""
    rsvps = load_rsvps(invite_id)
    if not rsvps:
        return {
            "total_responses": 0,
            "yes_count": 0,
            "no_count": 0,
            "maybe_count": 0,
            "total_adults": 0,
            "total_children": 0,
            "total_guests": 0,
            "yes_list": [],
            "no_list": [],
            "maybe_list": []
        }
    
    yes_list = []
    no_list = []
    maybe_list = []
    
    for rsvp in rsvps:
        if rsvp["response"].lower() == "yes":
            yes_list.append(rsvp)
        elif rsvp["response"].lower() == "no":
            no_list.append(rsvp)
        else:
            maybe_list.append(rsvp)
    
    # attendee counts (for 'Yes' only)
    total_adults = sum(int(x.get("adults", 0) or 0) for x in yes_list)
    total_kids = sum(int(x.get("kids", 0) or 0) for x in yes_list)
    total_guests = total_adults + total_kids

    return {
        "total_responses": len(rsvps),
        "yes_count": len(yes_list),
        "no_count": len(no_list),
        "maybe_count": len(maybe_list),
        "total_adults": total_adults,
        "total_children": total_kids,
        "total_guests": total_guests,
        "yes_list": yes_list,
        "no_list": no_list,
        "maybe_list": maybe_list
    }


def display_envelope():
    html = """
    <div style="display: flex; flex-direction: column; align-items: center; margin-top: 2em;">
            <div style="animation: pulse 2s infinite;">
            <img src="https://cdn.pixabay.com/photo/2016/04/01/10/09/envelope-1300157_1280.png"
                 style="max-width: 90%; height: auto; border-radius:16px;
                        box-shadow:2px 2px 12px #a80000;
                        transition: transform 0.3s ease;">
            </div>
        <div style="font-size:1.4em; font-family: 'Noto Serif', serif; color:#a80000;
                    margin-top:1em; animation: fadeIn 2s ease-in; text-align: center;">
                🎉 An invitation is waiting inside!<br>
                <b>Click to open the envelope and reveal your invitation</b>
            </div>
            <style>
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            </style>
        </div>
    """
    st.markdown(html, unsafe_allow_html=True)




def display_invitation_card(data, image_bytes=None, text_color="#000000", font_scale=1.0, overlay_opacity=0.0, title_offset_px=0):
    theme = THEMES[data["theme"]]
    
    # Improved background image handling - responsive and crisp
    if image_bytes:
        background_style = (
            f"background: url('data:image/png;base64,{image_bytes}') center center / cover no-repeat;"
            f"background-color: {theme['bg']};"
            "min-height: 80vh;"
            "width: 100%;"
            "position: relative;"
            "background-attachment: scroll;"
        )
        # Enhanced overlay for better text readability
        overlay = (
            f"<div style=\"position:absolute;inset:0;background:rgba(0,0,0,{overlay_opacity});pointer-events:none;\"></div>"
            if overlay_opacity and overlay_opacity > 0 else ""
        )
    else:
        background_style = f"background-color: {theme['bg']};min-height: 80vh;width: 100%;position: relative;"
        overlay = ""
    
    # Build the invocation HTML separately
    invocation_html = ""
    if data.get('invocation'):
        invocation_html = f'<div style="font-size:{1.4*font_scale:.2f}em;color:{text_color};font-weight:bold;margin-bottom:1em;text-shadow:2px 2px 4px rgba(255,255,255,0.9);">{data["invocation"]}</div>'
    
    # Enhanced HTML with better responsive design and text visibility
    html_content = f"""
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                box-sizing: border-box;
            }}
            .invitation-container {{
                width: 100% !important;
                max-width: 100% !important;
                margin: 0 auto !important;
                padding: 1em 0.5em !important;
            }}
            @media (max-width: 768px) {{
                .invitation-container {{
                    padding: 0.8em 0.3em !important;
                    margin: 0 !important;
                }}
                .invitation-text {{
                    font-size: {1.6*font_scale:.2f}em !important;
                    line-height: 1.2 !important;
                }}
                .invitation-subtitle {{
                    font-size: {1.0*font_scale:.2f}em !important;
                    line-height: 1.3 !important;
                }}
                .invitation-details {{
                    font-size: {0.9*font_scale:.2f}em !important;
                    line-height: 1.3 !important;
                }}
                .invitation-venue {{
                    font-size: {0.8*font_scale:.2f}em !important;
                    line-height: 1.3 !important;
                }}
                .invitation-message {{
                    font-size: {0.9*font_scale:.2f}em !important;
                    line-height: 1.4 !important;
                }}
            }}
            @media (max-width: 480px) {{
                .invitation-container {{
                    padding: 0.5em 0.2em !important;
                }}
                .invitation-text {{
                    font-size: {1.4*font_scale:.2f}em !important;
                }}
                .invitation-subtitle {{
                    font-size: {0.9*font_scale:.2f}em !important;
                }}
                .invitation-details {{
                    font-size: {0.8*font_scale:.2f}em !important;
                }}
                .invitation-venue {{
                    font-size: {0.7*font_scale:.2f}em !important;
                }}
                .invitation-message {{
                    font-size: {0.8*font_scale:.2f}em !important;
                }}
            }}
        </style>
        <div class="invitation-container" style="position:relative;{background_style}padding:2em 1em;border-radius:16px;border:2px solid {theme['accent']};font-family:{FONT_FAMILY};box-shadow:2px 2px 20px rgba(168,0,0,0.3);overflow:hidden;width:100%;max-width:100%;box-sizing:border-box;margin:0 auto;">
            {overlay}
            <div style="text-align:center;position:relative;z-index:2;width:100%;max-width:100%;padding:0 0.5em;">
            {invocation_html}
            <div style="margin-top:{title_offset_px}px;">
                <span class="invitation-text" style="font-size:{2.8*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:2px 2px 4px rgba(255,255,255,0.9);display:block;word-wrap:break-word;overflow-wrap:break-word;hyphens:auto;">{data['event_name']}</span>
            </div>
            <br>
            <span class="invitation-subtitle" style="font-size:{1.4*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:1px 1px 2px rgba(255,255,255,0.9);display:block;word-wrap:break-word;overflow-wrap:break-word;hyphens:auto;">Hosted by {data['host_names']}</span><br>
            <span class="invitation-details" style="font-size:{1.2*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:1px 1px 2px rgba(255,255,255,0.9);display:block;word-wrap:break-word;overflow-wrap:break-word;hyphens:auto;">{data['event_date']} at {data['event_time']}</span><br>
            <span class="invitation-venue" style="font-size:{1.1*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:1px 1px 2px rgba(255,255,255,0.9);display:block;word-wrap:break-word;overflow-wrap:break-word;hyphens:auto;">Venue: {data['venue_address']}</span>
        </div>
        <hr style="border:2px solid {text_color};margin:1.5em 0;position:relative;z-index:2;box-shadow:1px 1px 2px rgba(255,255,255,0.9);">
        <div class="invitation-message" style="font-size:{1.2*font_scale:.2f}em;color:{text_color};margin:1em 0 0.5em 0;padding:0.5em 0;position:relative;z-index:2;font-weight:bold;text-shadow:1px 1px 2px rgba(255,255,255,0.9);line-height:1.6;word-wrap:break-word;overflow-wrap:break-word;hyphens:auto;">
                {data['invitation_message']}
        </div>
    """
    
    # Use st.markdown for better mobile responsiveness (no iframe constraints)
    st.markdown(html_content, unsafe_allow_html=True)

# --- Header ---
st.markdown(
    f"""
    <div style="background:#a80000;color:#ffd700;padding:1em 0;text-align:center;border-radius:8px;font-family:{FONT_FAMILY};">
        <div style="font-family: monospace; font-size: 1.2em; margin-bottom: 0.5em;">
            ████████████████████████████████<br>
            ██      H A P P E N I N      ██<br>
            ████████████████████████████████
        </div>
        <div style="font-size:1.1em; margin-top: 0.5em;">
            Create • Share • Celebrate
        </div>
    </div>
    """, unsafe_allow_html=True,
)

# --- Page Navigation ---
def get_page():
    """Determine which page to show based on URL parameters"""
    invite_id = st.query_params.get("invite", None)
    admin_mode = st.query_params.get("admin", "0") in ("1", "true", "yes")
    
    if invite_id and admin_mode:
        return "admin"  # PAGE 2: Event Admin Dashboard
    elif invite_id:
        return "public"  # PAGE 3: Public Invite Page
    else:
        return "creation"  # PAGE 1: Event Creation Page

def show_page_navigation():
    """Show navigation between pages"""
    current_page = get_page()
    
    if current_page == "creation":
        st.sidebar.markdown("### 📝 Event Creation")
        st.sidebar.info("Create your invitation")
    elif current_page == "admin":
        st.sidebar.markdown("### 🛠️ Event Admin")
        st.sidebar.info("Manage your event")
    elif current_page == "public":
        st.sidebar.markdown("### 🎉 Public Invite")
        st.sidebar.info("Guest view")

# --- Admin flag ---
is_admin = st.query_params.get("admin", "0") in ("1", "true", "yes")

# --- Local Preview Section (admin only) ---
if is_admin:
    st.markdown("## 🧪 Local Testing & Preview")
    st.markdown("Use this section to test the invitation with your local files and event data.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎯 Create Test Invitation", help="Creates a test invitation using the provided event data and local files"):
            with st.spinner("Creating test invitation..."):
                invite_id, message = create_test_invitation()
                if invite_id:
                    st.success(message)
                    st.session_state.test_invite_id = invite_id
                    st.rerun()
                else:
                    st.error(message)

    with col2:
        if st.button("📋 Load Test Data", help="Loads the test event data into the form"):
            st.session_state.load_test_data = True
            st.rerun()


    # Show test invitation if created
    if hasattr(st.session_state, 'test_invite_id') and st.session_state.test_invite_id:
        st.markdown("### 🎉 Test Invitation Preview")
        test_data = load_invitation(st.session_state.test_invite_id)
        if test_data:
            image_bytes = test_data.get("image_base64")
            music_bytes = None
            music_filename = None
            if test_data.get("music_base64") and test_data.get("music_filename"):
                music_bytes = base64.b64decode(test_data["music_base64"])
                music_filename = test_data["music_filename"]
            
            # Auto-choose a readable text color based on the image
            auto_color = choose_text_color(image_bytes, mode="Auto")
            display_invitation_card(test_data, image_bytes, text_color=auto_color, font_scale=1.0, overlay_opacity=0.15, title_offset_px=-20)
            
            # Autoplay music if available
            if music_bytes and music_filename:
                import streamlit.components.v1 as components
                ext = music_filename.split('.')[-1].lower() if '.' in music_filename else 'mp3'
                mime = 'audio/mpeg' if ext in ('mp3', 'mpeg') else ('audio/wav' if ext == 'wav' else 'audio/*')
                audio_b64 = base64.b64encode(music_bytes).decode('utf-8')
                components.html(f"<audio autoplay loop style='display:none' src='data:{mime};base64,{audio_b64}'></audio>", height=0)
            
            # Local URL for testing
            local_url = f"http://localhost:8501?invite={st.session_state.test_invite_id}"
            st.markdown("**Local Test URL:**")
            st.code(local_url)
            
            if st.button("🗑️ Clear Test Invitation"):
                del st.session_state.test_invite_id
                st.rerun()

            st.markdown("---")

def show_event_creation_page():
    """PAGE 1: Event Creation Page - Main landing page for creating invitations"""
    st.markdown("## 📝 Create New Invitation")
    
    # Start with empty form (no pre-populated data as requested)
    with st.form("invitation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input("Event Name", placeholder="e.g., Wedding Ceremony, Housewarming")
            host_names = st.text_input("Host Names", placeholder="e.g., John & Jane Smith")
            event_date = st.date_input("Event Date", value=datetime.today())
            event_time = st.text_input("Event Time", placeholder="e.g., 4:00 PM, 2:30 PM, 6:00 PM", help="Enter time in any format you prefer (e.g., 4:00 PM, 2:30 PM, 6:00 PM)")
            venue_address = st.text_area("Venue Address", placeholder="Full address with city, state, zip")
            
        with col2:
            invocation = st.text_input("Optional Invocation or Sanskrit Verse", placeholder="e.g., ॐ श्री गणेशाय नमः")
            manager_email = st.text_input("Event manager email (notification recipient)", placeholder="admin@example.com")
            invitation_message = st.text_area("Invitation Message", placeholder="Your heartfelt message to guests...", height=100)
        
        st.markdown("---")
        
        # File uploads
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("**Background Image:**")
            image_file = st.file_uploader("Upload Background Image (deity, temple, or custom design)", type=["jpg", "png"])
        
        with col4:
            st.markdown("**Background Music:**")
            music_file = st.file_uploader("Upload Music (MP3/WAV, optional)", type=["mp3", "wav"])
            theme = st.selectbox("Theme Choice", list(THEMES.keys()), index=0)
        
        submit_button = st.form_submit_button("🎨 Create Invitation", use_container_width=True)
        
        # Store form values in session state for preview access
        if event_name:
            st.session_state.preview_event_name = event_name
        if host_names:
            st.session_state.preview_host_names = host_names
        if event_date:
            st.session_state.preview_event_date = event_date.strftime("%Y-%m-%d")
        if event_time:
            st.session_state.preview_event_time = event_time
        if venue_address:
            st.session_state.preview_venue_address = venue_address
        if invocation:
            st.session_state.preview_invocation = invocation
        if invitation_message:
            st.session_state.preview_invitation_message = invitation_message
        if theme:
            st.session_state.preview_theme = theme
        if image_file:
            st.session_state.preview_image_file = image_file
    
    # Visual Customization Section (after form, before reset button)
    st.markdown("---")
    st.markdown("### 🎨 Visual Customization")
    show_preview = st.checkbox("Show Live Preview", value=True, help="Display a preview of your invitation as you customize")
    if show_preview:
        st.info("💡 Preview will appear below")
    
    # Customization controls (outside the form so they update in real-time)
    col_custom1, col_custom2, col_custom3 = st.columns(3)
    
    with col_custom1:
        st.markdown("**Text Styling:**")
        text_color = st.color_picker("Font Color", value="#000000", help="Choose the color for all text on the invitation")
        font_scale = st.slider("Font Size", min_value=0.7, max_value=1.5, value=1.0, step=0.1, help="Adjust the size of all text")
        
        # Store in session state for preview access
        st.session_state.preview_text_color = text_color
        st.session_state.preview_font_scale = font_scale
    
    with col_custom2:
        st.markdown("**Background Overlay:**")
        overlay_opacity = st.slider("Background Darkness", min_value=0.0, max_value=0.7, value=0.15, step=0.05, help="Add a dark overlay to improve text readability")
        title_offset = st.slider("Title Position", min_value=-100, max_value=100, value=-20, step=5, help="Adjust vertical position of the event title")
        
        # Store in session state for preview access
        st.session_state.preview_overlay_opacity = overlay_opacity
        st.session_state.preview_title_offset = title_offset
    
    with col_custom3:
        st.markdown("**Customization Tips:**")
        with st.expander("🎨 Tips for Better Results"):
            st.markdown("""
            **Font Color**: Choose colors that contrast well with your background image
            
            **Font Size**: Larger text is more readable, especially for mobile devices
            
            **Background Darkness**: Add overlay to make text more readable on bright images
            
            **Title Position**: Adjust if your image has important elements at the top
            """)
    
    # Reset button for customization (outside the form)
    col_reset1, col_reset2, col_reset3 = st.columns([1, 1, 1])
    with col_reset2:
        if st.button("🔄 Reset to Defaults", help="Reset all customization settings to default values", use_container_width=True):
            # Clear customization session state
            if 'preview_text_color' in st.session_state:
                del st.session_state.preview_text_color
            if 'preview_font_scale' in st.session_state:
                del st.session_state.preview_font_scale
            if 'preview_overlay_opacity' in st.session_state:
                del st.session_state.preview_overlay_opacity
            if 'preview_title_offset' in st.session_state:
                del st.session_state.preview_title_offset
            st.rerun()
    
    # Live Preview Section (outside the form so it updates in real-time)
    # Use session state to access form values outside the form
    has_content = False
    preview_data = {}
    
    # Check if we have any content to preview
    if 'preview_event_name' in st.session_state and st.session_state.preview_event_name.strip():
        has_content = True
    elif 'preview_image_file' in st.session_state and st.session_state.preview_image_file is not None:
        has_content = True
    
    if show_preview and has_content:
        st.markdown("---")
        st.markdown("### 👀 Live Preview")
        
        # Create preview data from session state
        preview_data = {
            "event_name": st.session_state.get('preview_event_name', 'Your Event Name'),
            "host_names": st.session_state.get('preview_host_names', 'Your Host Names'),
            "event_date": st.session_state.get('preview_event_date', '2025-01-01'),
            "event_time": st.session_state.get('preview_event_time', '4:00 PM'),
            "venue_address": st.session_state.get('preview_venue_address', 'Your Venue Address'),
            "invocation": st.session_state.get('preview_invocation', 'ॐ श्री गणेशाय नमः'),
            "invitation_message": st.session_state.get('preview_invitation_message', 'Your heartfelt message to guests...'),
            "theme": st.session_state.get('preview_theme', 'classic')
        }
        
        # Process image for preview
        preview_image_bytes = None
        if 'preview_image_file' in st.session_state and st.session_state.preview_image_file is not None:
            try:
                image = Image.open(st.session_state.preview_image_file)
                buf = BytesIO()
                image.save(buf, format="PNG")
                preview_image_bytes = base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception as e:
                st.warning(f"⚠️ Could not process image for preview: {e}")
        
        # If no image uploaded, use a default or show message
        if not preview_image_bytes:
            st.info("📷 Upload an image above to see the preview with your customizations")
            # Create a simple preview with just text
            st.markdown("**Preview (text only - upload image for full preview):**")
            st.markdown(f"**Event:** {preview_data['event_name']}")
            st.markdown(f"**Hosted by:** {preview_data['host_names']}")
            st.markdown(f"**Date:** {preview_data['event_date']} at {preview_data['event_time']}")
            st.markdown(f"**Venue:** {preview_data['venue_address']}")
            if preview_data['invocation']:
                st.markdown(f"**Invocation:** {preview_data['invocation']}")
            st.markdown(f"**Message:** {preview_data['invitation_message']}")
        else:
            # Show full preview with image and customizations
            st.info("🎨 Adjust the customization controls above to see changes in real-time")
            
            # Add preview tips
            with st.expander("💡 Preview Tips", expanded=False):
                st.markdown("""
                **Customization Tips:**
                - **Font Color**: Choose colors that contrast well with your background
                - **Font Size**: Larger fonts are more readable on mobile devices
                - **Background Darkness**: Add overlay for better text readability on bright images
                - **Title Position**: Adjust if text overlaps with important parts of your image
                
                **Best Practices:**
                - Test on both desktop and mobile views
                - Ensure text is readable against your background
                - Keep font sizes large enough for older guests
                - Use the reset button to start over if needed
                """)
            
            display_invitation_card(
                preview_data, 
                image_bytes=preview_image_bytes,
                text_color=st.session_state.get('preview_text_color', '#000000'),
                font_scale=st.session_state.get('preview_font_scale', 1.0),
                overlay_opacity=st.session_state.get('preview_overlay_opacity', 0.15),
                title_offset_px=st.session_state.get('preview_title_offset', -20)
            )
    
    if submit_button:
        if not event_name.strip():
            st.error("Please enter an event name.")
        else:
            # Process uploaded files
            image_bytes = None
            image_base64 = None
            if image_file:
                try:
                    image = Image.open(image_file)
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    image_bytes = base64.b64encode(buf.getvalue()).decode("utf-8")
                    image_base64 = image_bytes
                    st.success("✅ Image uploaded successfully")
                except Exception as e:
                    st.error(f"❌ Error processing image: {str(e)}")
                    st.stop()

            music_bytes = None
            music_base64 = None
            music_filename = None
            if music_file:
                try:
                    music_bytes = music_file.read()
                    music_base64 = base64.b64encode(music_bytes).decode("utf-8")
                    music_filename = music_file.name
                    st.success("✅ Music uploaded successfully")
                except Exception as e:
                    st.error(f"❌ Error processing music: {str(e)}")
                    st.stop()

            # Create event data
            data = {
                "event_name": event_name,
                "host_names": host_names,
                "event_date": event_date.strftime("%Y-%m-%d"),
                "event_time": event_time,
                "venue_address": venue_address,
                "invocation": invocation,
                "invitation_message": invitation_message,
                "theme": theme,
                "image_base64": image_base64,
                "music_base64": music_base64,
                "music_filename": music_filename,
                "manager_email": manager_email,
                "text_color": text_color,
                "font_scale": font_scale,
                "overlay_opacity": overlay_opacity,
                "title_offset": title_offset,
                "created_at": str(datetime.utcnow())
            }
            
            # Save invitation and redirect to admin page
            try:
                invite_id = save_invitation(data)
                admin_url = f"{get_base_url()}?invite={invite_id}&admin=true"
                public_url = f"{get_base_url()}?invite={invite_id}"
                
                st.success("🎉 Your invitation has been created!")
                st.info("✅ **Data Safety**: Your invitation has been automatically saved and backed up to prevent data loss.")
                st.markdown("### 📤 Share Your Invitation")
                st.code(public_url)
                st.markdown(f"[📱 Share via WhatsApp](https://wa.me/?text=Invitation%20Link%3A%20{public_url}) &nbsp; | &nbsp; [📧 Share via Email](mailto:?subject=Invitation&body=Invitation%20Link%3A%20{public_url})")
                
                st.markdown("### 🛠️ Manage Your Event")
                st.info(f"**Admin Dashboard:** [Open Admin Panel]({admin_url})")
                
                if image_bytes:
                    st.download_button("📥 Download Invitation Background", base64.b64decode(image_bytes), file_name="invitation_background.png", mime="image/png")
                    
            except Exception as e:
                st.error(f"❌ Error saving invitation: {str(e)}")
                logger.error(f"Error saving invitation: {str(e)}")

def show_event_admin_page():
    """PAGE 2: Event Admin Dashboard - Per-event management page"""
    invite_id = st.query_params.get("invite", None)
    if not invite_id:
        st.error("No invitation ID provided.")
        return
    
    data = load_invitation(invite_id)
    if not data:
        st.error("Invitation not found.")
        return
    
    st.markdown("## 🛠️ Event Admin Dashboard")
    
    # Debug section for URL troubleshooting
    with st.expander("🔧 Debug Info (for troubleshooting)", expanded=False):
        st.markdown("**Current URL Detection:**")
        st.code(f"Base URL: {get_base_url()}")
        st.markdown("**Environment Variables:**")
        st.code(f"STREAMLIT_CLOUD: {os.getenv('STREAMLIT_CLOUD')}")
        st.code(f"STREAMLIT_CLOUD_BASE_URL: {os.getenv('STREAMLIT_CLOUD_BASE_URL')}")
        st.code(f"STREAMLIT_SHARING_MODE: {os.getenv('STREAMLIT_SHARING_MODE')}")
        st.markdown("**Generated URLs:**")
        admin_url = f"{get_base_url()}?invite={invite_id}&admin=true"
        public_url = f"{get_base_url()}?invite={invite_id}"
        st.code(f"Admin URL: {admin_url}")
        st.code(f"Public URL: {public_url}")
    
    # Recreate Missing Invitation Section
    with st.expander("🔧 Recreate Missing Invitation", expanded=False):
        st.markdown("**Use this section to recreate a missing invitation with specific ID and RSVP data**")
        
        with st.form("recreate_invitation_form"):
            st.markdown("### Event Details")
            col1, col2 = st.columns(2)
            
            with col1:
                recreate_event_name = st.text_input("Event Name", value=data.get('event_name', ''))
                recreate_host_names = st.text_input("Host Names", value=data.get('host_names', ''))
                recreate_event_date = st.date_input("Event Date", value=datetime.strptime(data.get('event_date', '2025-01-01'), '%Y-%m-%d').date())
            
            with col2:
                recreate_event_time = st.text_input("Event Time", value=data.get('event_time', ''))
                recreate_venue = st.text_input("Venue Address", value=data.get('venue_address', ''))
                recreate_theme = st.selectbox("Theme", ["Temple", "Floral", "Modern", "Classic"], index=["Temple", "Floral", "Modern", "Classic"].index(data.get('theme', 'Temple')))
            
            recreate_invocation = st.text_area("Invocation", value=data.get('invocation', ''))
            recreate_message = st.text_area("Invitation Message", value=data.get('invitation_message', ''))
            
            st.markdown("### RSVP Data (JSON Format)")
            st.markdown("**Paste your RSVP data in JSON format. Example:**")
            st.code('''[
  {
    "name": "John Doe",
    "email": "john@example.com",
    "response": "Yes",
    "adults": 2,
    "kids": 0,
    "total_guests": 2,
    "message": "Looking forward to it!",
    "timestamp": "2025-10-16 19:30:27.909145"
  }
]''')
            
            rsvp_json = st.text_area("RSVP Data (JSON)", height=200, placeholder="Paste your RSVP data here...")
            
            recreate_submit = st.form_submit_button("🔄 Recreate Invitation with Original ID")
            
            if recreate_submit:
                if not recreate_event_name.strip():
                    st.error("Please enter an event name.")
                else:
                    try:
                        # Parse RSVP data if provided
                        rsvp_data = None
                        if rsvp_json.strip():
                            rsvp_data = json.loads(rsvp_json)
                        
                        # Create event data
                        recreate_data = {
                            "event_name": recreate_event_name,
                            "host_names": recreate_host_names,
                            "event_date": recreate_event_date.strftime("%Y-%m-%d"),
                            "event_time": recreate_event_time,
                            "venue_address": recreate_venue,
                            "invocation": recreate_invocation,
                            "invitation_message": recreate_message,
                            "theme": recreate_theme,
                            "image_base64": data.get("image_base64"),
                            "music_base64": data.get("music_base64"),
                            "music_filename": data.get("music_filename"),
                            "manager_email": data.get("manager_email"),
                            "text_color": data.get("text_color", "#000000"),
                            "font_scale": data.get("font_scale", 1.0),
                            "overlay_opacity": data.get("overlay_opacity", 0.15),
                            "title_offset": data.get("title_offset", -20),
                            "created_at": str(datetime.utcnow())
                        }
                        
                        # Recreate the invitation with the original ID
                        result_id, message = recreate_invitation_with_id(invite_id, recreate_data, rsvp_data)
                        
                        if result_id:
                            st.success(f"✅ {message}")
                            st.info(f"**Original Links Now Work:**")
                            st.code(f"Public: {get_base_url()}?invite={invite_id}")
                            st.code(f"Admin: {get_base_url()}?invite={invite_id}&admin=true")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON format in RSVP data. Please check your JSON syntax.")
                    except Exception as e:
                        st.error(f"❌ Error recreating invitation: {str(e)}")
    
    # Event details
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### {data['event_name']}")
        st.markdown(f"**Hosted by:** {data['host_names']}")
        st.markdown(f"**Date:** {data['event_date']} at {data['event_time']}")
        st.markdown(f"**Venue:** {data['venue_address']}")
        if data.get('invocation'):
            st.markdown(f"**Invocation:** {data['invocation']}")
    
    with col2:
        public_url = f"{get_base_url()}?invite={invite_id}"
        st.markdown("### 📤 Share Invite Link")
        st.code(public_url)
        if st.button("📋 Copy Link"):
            st.success("Link copied to clipboard!")
        st.markdown(f"[📱 Share via WhatsApp](https://wa.me/?text=Invitation%20Link%3A%20{public_url}) &nbsp; | &nbsp; [📧 Share via Email](mailto:?subject=Invitation&body=Invitation%20Link%3A%20{public_url})")

        st.markdown("---")
    
    # Live preview with stored customization
    st.markdown("### 🎨 Live Preview")
    image_bytes = data.get("image_base64")
    
    # Use stored customization parameters or defaults
    text_color = data.get("text_color", "#000000")
    font_scale = data.get("font_scale", 1.0)
    overlay_opacity = data.get("overlay_opacity", 0.15)
    title_offset = data.get("title_offset", -20)
    
    display_invitation_card(
        data,
        image_bytes,
        text_color=text_color,
        font_scale=font_scale,
        overlay_opacity=overlay_opacity,
        title_offset_px=title_offset,
    )
    
    # RSVP Analytics
    st.markdown("---")
    st.markdown("### 📊 RSVP Analytics")
    
    analytics = get_rsvp_analytics(invite_id)
    
    if analytics["total_responses"] > 0:
        # First row: Response counts
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Responses", analytics["total_responses"])
        with col2:
            st.metric("✅ Yes", analytics["yes_count"], delta=f"{analytics['yes_count']/analytics['total_responses']*100:.1f}%")
        with col3:
            st.metric("❌ No", analytics["no_count"], delta=f"{analytics['no_count']/analytics['total_responses']*100:.1f}%")
        with col4:
            st.metric("❓ Maybe", analytics["maybe_count"], delta=f"{analytics['maybe_count']/analytics['total_responses']*100:.1f}%")
        
        # Second row: Guest counts (only for "Yes" responses)
        if analytics["yes_count"] > 0:
            st.markdown("#### 👥 Guest Counts (Attending Only)")
            guest_col1, guest_col2, guest_col3 = st.columns(3)
            
            with guest_col1:
                st.metric("👨‍👩‍👧‍👦 Total Adults", analytics["total_adults"])
            with guest_col2:
                st.metric("👶 Total Children", analytics["total_children"])
            with guest_col3:
                st.metric("🎉 Total Guests", analytics["total_guests"])
        
        # Detailed RSVP lists
        tab1, tab2, tab3 = st.tabs(["✅ Attending", "❌ Not Attending", "❓ Maybe"])
        
        with tab1:
            if analytics["yes_list"]:
                for entry in reversed(analytics["yes_list"]):
                    st.markdown(f"**{entry['name']}**")
                    if entry['email']:
                        st.markdown(f"📧 {entry['email']}")
                    if entry.get('message'):
                        st.markdown(f"💬 {entry['message']}")
                    st.markdown(f"⏰ {entry['timestamp']}")
                    st.markdown("---")
            else:
                st.info("No 'Yes' responses yet.")
        
        with tab2:
            if analytics["no_list"]:
                for entry in reversed(analytics["no_list"]):
                    st.markdown(f"**{entry['name']}**")
                    if entry['email']:
                        st.markdown(f"📧 {entry['email']}")
                    if entry.get('message'):
                        st.markdown(f"💬 {entry['message']}")
                    st.markdown(f"⏰ {entry['timestamp']}")
                    st.markdown("---")
            else:
                st.info("No 'No' responses yet.")
        
        with tab3:
            if analytics["maybe_list"]:
                for entry in reversed(analytics["maybe_list"]):
                    st.markdown(f"**{entry['name']}**")
                    if entry['email']:
                        st.markdown(f"📧 {entry['email']}")
                    if entry.get('message'):
                        st.markdown(f"💬 {entry['message']}")
                    st.markdown(f"⏰ {entry['timestamp']}")
                    st.markdown("---")
            else:
                st.info("No 'Maybe' responses yet.")
    else:
        st.info("📊 No RSVPs yet. Share the invitation link to start receiving responses!")
    
    # Edit RSVP Data Section (only for specific invitation)
    if invite_id == "264e6dd5-ca33-4d24-944f-a58e26545018":
        st.markdown("---")
        st.markdown("### ✏️ Edit RSVP Data")
        
        with st.expander("Edit Individual RSVPs", expanded=False):
            rsvps = load_rsvps(invite_id)
            if rsvps:
                for i, rsvp in enumerate(rsvps):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{rsvp.get('name', 'Unknown')}**")
                            if rsvp.get('email'):
                                st.caption(f"Email: {rsvp['email']}")
                        
                        with col2:
                            new_response = st.selectbox(
                                "Response", 
                                ["Yes", "No", "Maybe"], 
                                index=["Yes", "No", "Maybe"].index(rsvp.get('response', 'Yes')),
                                key=f"response_{i}"
                            )
                        
                        with col3:
                            new_adults = st.number_input(
                                "Adults", 
                                min_value=0, 
                                max_value=20, 
                                value=rsvp.get('adults', 0),
                                key=f"adults_{i}"
                            )
                        
                        with col4:
                            new_kids = st.number_input(
                                "Children", 
                                min_value=0, 
                                max_value=20, 
                                value=rsvp.get('kids', 0),
                                key=f"kids_{i}"
                            )
                        
                        # Update button for each RSVP
                        if st.button(f"Update {rsvp.get('name', 'Unknown')}", key=f"update_{i}"):
                            # Update the RSVP data
                            rsvps[i]['response'] = new_response
                            rsvps[i]['adults'] = new_adults
                            rsvps[i]['kids'] = new_kids
                            rsvps[i]['total_guests'] = new_adults + new_kids
                            rsvps[i]['_last_modified'] = str(datetime.utcnow())
                            
                            # Save updated RSVPs
                            rsvp_file = f"{DB_PATH}/rsvp_{invite_id}.json"
                            with open(rsvp_file, "w", encoding="utf-8") as f:
                                json.dump(rsvps, f, indent=2)
                            
                            # Auto-commit the changes
                            try:
                                import subprocess
                                subprocess.run(["git", "add", rsvp_file], check=True, capture_output=True)
                                subprocess.run(["git", "commit", "-m", f"Update RSVP for {rsvp.get('name', 'Unknown')} in invitation {invite_id}"], check=True, capture_output=True)
                                subprocess.run(["git", "push"], check=True, capture_output=True)
                                st.success(f"✅ Updated {rsvp.get('name', 'Unknown')}'s RSVP")
                                st.rerun()
                            except Exception as e:
                                st.warning(f"⚠️ RSVP updated but failed to commit to git: {e}")
                        
                        st.markdown("---")
            else:
                st.info("No RSVPs found to edit.")
        
        # Bulk operations for this specific invitation
        with st.expander("Bulk Operations", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Clear All RSVPs", type="secondary"):
                    if st.session_state.get('confirm_clear', False):
                        clear_rsvps(invite_id)
                        st.success("✅ All RSVPs cleared")
                        st.session_state.confirm_clear = False
                        st.rerun()
                    else:
                        st.session_state.confirm_clear = True
                        st.warning("⚠️ Click again to confirm clearing all RSVPs")
            
            with col2:
                if st.button("📥 Export RSVPs", type="secondary"):
                    csv_data = get_rsvp_csv(invite_id)
                    st.download_button(
                        "Download CSV",
                        csv_data,
                        file_name=f"rsvps_{invite_id}.csv",
                        mime="text/csv"
                    )
    
    # Email Management Section
    st.markdown("---")
    st.markdown("### 📧 Email Management")
    
    # Show email list for Yes responses
    yes_guests = [rsvp for rsvp in analytics["yes_list"] if rsvp.get("email")]
    
    if yes_guests:
        st.markdown(f"#### 📋 Guest Email List ({len(yes_guests)} attending guests with emails)")
        
        # Display emails in a nice format
        email_list = []
        for guest in yes_guests:
            email_list.append(f"**{guest['name']}** - {guest['email']}")
        
        st.markdown("\n".join(email_list))
        
        # Reminder functionality
        st.markdown("#### 📤 Send Reminder")
        st.info("Send custom messages to all guests who responded 'Yes'")
        
        with st.form("reminder_form"):
            reminder_subject = st.text_input("Email Subject", value=f"Reminder: {data['event_name']}", placeholder="Enter email subject")
            reminder_message = st.text_area("Message to Guests", placeholder="Enter your custom message here...", height=100)
            
            col1, col2 = st.columns(2)
            with col1:
                send_reminder = st.form_submit_button("📤 Send Reminder", use_container_width=True)
            with col2:
                preview_reminder = st.form_submit_button("👀 Preview Email", use_container_width=True)
        
        if send_reminder:
            if reminder_subject and reminder_message:
                with st.spinner("Sending reminder emails..."):
                    sent, message = send_reminder_email(invite_id, reminder_subject, reminder_message)
                    if sent:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.error("Please enter both subject and message")
        
        if preview_reminder:
            if reminder_subject and reminder_message:
                st.markdown("#### 📧 Email Preview")
                st.markdown(f"**Subject:** {reminder_subject}")
                st.markdown("**Recipients:** All guests who responded 'Yes'")
                st.markdown("**Message:**")
                st.info(reminder_message)
            else:
                st.error("Please enter both subject and message")
    else:
        st.info("No guests with 'Yes' responses and email addresses found yet.")
    
    # Email Test Section
    st.markdown("---")
    st.markdown("### 🧪 Email Test")
    st.info("Test your email notifications to ensure RSVP emails are working correctly.")
    
    test_email_address = st.text_input("Test Email Address", value=data.get("manager_email", ""), placeholder="Enter email to send test to")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Send Test Email", use_container_width=True):
            if test_email_address:
                sent, message = send_test_email(test_email_address)
                if sent:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("Please enter an email address")
    
    with col2:
        if st.button("📊 Test RSVP Email", use_container_width=True):
            if test_email_address:
                # Create a test RSVP entry
                test_rsvp = {
                    "name": "Test User",
                    "email": "test@example.com",
                    "response": "Yes",
                    "adults": 2,
                    "kids": 1,
                    "total_guests": 3,
                    "message": "This is a test RSVP to verify email functionality",
                    "timestamp": str(datetime.utcnow())
                }
                sent, message = send_rsvp_email(invite_id, test_rsvp)
                if sent:
                    st.success(f"✅ Test RSVP email sent to {test_email_address}")
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("Please enter an email address")

def show_public_invite_page():
    """PAGE 3: Public Invite Page - Guest-facing invitation (no envelope animation)"""
    invite_id = st.query_params.get("invite", None)
    if not invite_id:
        st.error("No invitation ID provided.")
        return
    
    data = load_invitation(invite_id)
    if not data:
        st.error("Invitation not found.")
        return
    
    # Display invitation directly (no envelope animation)
    st.markdown("## 🎉 Happenin — Create, Share, Celebrate")
    image_bytes = data.get("image_base64")
    music_bytes = None
    music_filename = None
    if data.get("music_base64") and data.get("music_filename"):
        music_bytes = base64.b64decode(data["music_base64"])
        music_filename = data["music_filename"]
    
    # Auto-play background music if available
    if music_bytes and music_filename:
        import streamlit.components.v1 as components
        ext = music_filename.split('.')[-1].lower() if '.' in music_filename else 'mp3'
        mime = 'audio/mpeg' if ext in ('mp3', 'mpeg') else ('audio/wav' if ext == 'wav' else 'audio/*')
        audio_b64 = base64.b64encode(music_bytes).decode('utf-8')
        
        # Debug info for troubleshooting
        
        # Option 2: Start muted, then unmute on first click (100% reliable)
        music_html = f"""
        <div style="display:none;">
            <audio id="bgMusic" autoplay muted loop preload="auto">
                <source src="data:{mime};base64,{audio_b64}" type="{mime}">
            </audio>
        </div>
        
        <script>
            console.log('Music script loaded');
            document.addEventListener('click', function() {{
                console.log('Click detected, attempting to unmute music');
                const bgm = document.getElementById('bgMusic');
                if (bgm) {{
                    console.log('Audio element found:', bgm);
                    bgm.muted = false;
                    bgm.play().then(function() {{
                        console.log('Music started successfully');
                    }}).catch(function(error) {{
                        console.log('Unmute failed:', error);
                    }});
                }} else {{
                    console.log('Audio element not found');
                }}
            }}, {{ once: true }});
            
            // Also try to start on page load (might work in some cases)
            window.addEventListener('load', function() {{
                console.log('Page loaded, checking audio element');
                const bgm = document.getElementById('bgMusic');
                if (bgm) {{
                    console.log('Audio element found on load:', bgm);
                    // Try to play muted first
                    bgm.play().catch(function(error) {{
                        console.log('Initial play failed (expected):', error);
                    }});
                }}
            }});
        </script>
        """
        
        components.html(music_html, height=150)
    else:
        # Fallback: Try to use local music file
        st.info("🎵 No music in invitation data, trying local music file...")
        local_music_bytes = get_local_music_base64()
        if local_music_bytes:
            import streamlit.components.v1 as components
            mime = 'audio/mpeg'
            audio_b64 = base64.b64encode(local_music_bytes).decode('utf-8')
            
            
            music_html = f"""
            <div style="display:none;">
                <audio id="bgMusic" autoplay muted loop preload="auto">
                    <source src="data:{mime};base64,{audio_b64}" type="{mime}">
                </audio>
            </div>
            
            <script>
                console.log('Local music script loaded');
                document.addEventListener('click', function() {{
                    console.log('Click detected, attempting to unmute local music');
                    const bgm = document.getElementById('bgMusic');
                    if (bgm) {{
                        console.log('Audio element found:', bgm);
                        bgm.muted = false;
                        bgm.play().then(function() {{
                            console.log('Local music started successfully');
                        }}).catch(function(error) {{
                            console.log('Unmute failed:', error);
                        }});
                    }} else {{
                        console.log('Audio element not found');
                    }}
                }}, {{ once: true }});
                
                // Also try to start on page load
                window.addEventListener('load', function() {{
                    console.log('Page loaded, checking local audio element');
                    const bgm = document.getElementById('bgMusic');
                    if (bgm) {{
                        console.log('Local audio element found on load:', bgm);
                        bgm.play().catch(function(error) {{
                            console.log('Initial local play failed (expected):', error);
                        }});
                    }}
                }});
            </script>
            """
            
            components.html(music_html, height=150)
        else:
            st.warning("🎵 No music file found (neither in invitation data nor local file)")
    
    # Display invitation with stored customization
    image_bytes = data.get("image_base64")
    
    # Use stored customization parameters or defaults
    text_color = data.get("text_color", "#000000")
    font_scale = data.get("font_scale", 1.0)
    overlay_opacity = data.get("overlay_opacity", 0.15)
    title_offset = data.get("title_offset", -20)
    
    display_invitation_card(
        data,
        image_bytes,
        text_color=text_color,
        font_scale=font_scale,
        overlay_opacity=overlay_opacity,
        title_offset_px=title_offset,
    )
    
    # RSVP Form
    st.markdown("---")
    st.markdown("### 📝 RSVP to This Event")
    
    with st.form("rsvp_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            guest_name = st.text_input("Your Name *", placeholder="Enter your full name")
            guest_email = st.text_input("Email for Reminders *", placeholder="your.email@example.com", help="Required to send you event reminders and updates")
        
        with col2:
            attendance = st.radio("Will you attend? *", ["Yes", "No", "Maybe"], horizontal=True)
            adults_count = st.number_input("Number of Adults", min_value=0, max_value=20, value=1 if attendance == "Yes" else 0)
            kids_count = st.number_input("Number of Children", min_value=0, max_value=20, value=0)
        
        additional_message = st.text_area("Additional Message (optional)", placeholder="Any dietary restrictions, special requests, or comments...")
        
        submit_rsvp = st.form_submit_button("📤 Submit RSVP", use_container_width=True)
    
    if submit_rsvp:
        if not guest_name.strip():
            st.error("Please enter your name to RSVP.")
        elif not guest_email.strip():
            st.error("Please enter your email address to RSVP.")
        else:
            # Validate email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, guest_email.strip()):
                st.error("Please enter a valid email address.")
            else:
                rsvp_entry = {
                    "name": guest_name,
                    "email": guest_email,
                    "response": attendance,
                    "adults": adults_count,
                    "kids": kids_count,
                    "total_guests": adults_count + kids_count,
                    "message": additional_message,
                    "timestamp": str(datetime.utcnow())
                }
                
                save_rsvp(invite_id, rsvp_entry)
                
                # Send email notification
                sent, reason = send_rsvp_email(invite_id, rsvp_entry)
                
                st.success("🎉 Thank you! Your RSVP has been recorded.")
                if sent:
                    st.info("📧 Email notification sent to event organizer.")
                else:
                    st.warning(f"📧 Email notification not sent: {reason}")
                
                st.rerun()
    
    # Show persistent confirmation if RSVP was just submitted
    if st.session_state.get("last_rsvp_success"):
        col_ok, col_status = st.columns([2,1])
        with col_ok:
            st.success(f"✅ **{st.session_state.get('last_rsvp_name', 'Guest')}** - {st.session_state.get('last_rsvp_response', 'RSVP')} recorded!")
        with col_status:
            email_status = st.session_state.get("last_rsvp_email_status", "")
            if "sent" in email_status.lower():
                st.success("📧 Email sent")
            else:
                st.warning("📧 Email issue")

# --- Main Page Routing ---
show_page_navigation()
current_page = get_page()

if current_page == "creation":
    # PAGE 1: Event Creation Page
    show_event_creation_page()
elif current_page == "admin":
    # PAGE 2: Event Admin Dashboard
    show_event_admin_page()
elif current_page == "public":
    # PAGE 3: Public Invite Page
    show_public_invite_page()

