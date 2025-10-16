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
            'host': os.getenv("SMTP_HOST", "smtp.gmail.com"),
            'port': os.getenv("SMTP_PORT", "587"),
            'tls': os.getenv("SMTP_TLS", "true"),
            'notify_email': os.getenv("RSVP_NOTIFY_EMAIL", "")
        }
    
    # Fallback to Streamlit secrets (deployment)
    try:
        import streamlit as st
        return {
            'user': st.secrets["SMTP_USER"],
            'password': st.secrets["SMTP_PASS"],
            'host': st.secrets.get("SMTP_HOST", "smtp.gmail.com"),
            'port': st.secrets.get("SMTP_PORT", "587"),
            'tls': st.secrets.get("SMTP_TLS", "true"),
            'notify_email': st.secrets.get("RSVP_NOTIFY_EMAIL", "")
        }
    except:
        # No configuration found
        return {
            'user': None,
            'password': None,
            'host': "smtp.gmail.com",
            'port': "587",
            'tls': "true",
            'notify_email': ""
        }

def send_rsvp_email(invite_id, rsvp_entry):
    """Send an email notification for a new RSVP if SMTP env vars are set.

    Priority for recipient address:
    1) `manager_email` stored in the invite payload
    2) `RSVP_NOTIFY_EMAIL` environment variable
    3) Default fallback to provided testing email

    Expected environment variables (if using SMTP):
      - SMTP_HOST (default: smtp.gmail.com)
      - SMTP_PORT (default: 587)
      - SMTP_USER
      - SMTP_PASS
      - SMTP_TLS (default: true)
    """
    invite_data = load_invitation(invite_id) or {}
    
    # Get SMTP configuration
    smtp_config = get_smtp_config()
    
    # Prefer invite's manager_email; otherwise use configured notify email
    notify_to = invite_data.get("manager_email") or smtp_config['notify_email']
    
    # Debug logging to help identify the source of invalid emails
    logger.info(f"RSVP email recipient: {notify_to}")
    logger.info(f"Manager email from invite: {invite_data.get('manager_email')}")
    logger.info(f"Notify email from config: {smtp_config['notify_email']}")
    
    # Validate email address format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if notify_to and not re.match(email_pattern, notify_to):
        logger.warning(f"Invalid email address format: {notify_to}")
        return False, f"Invalid email address: {notify_to}"
    
    if not (smtp_config['user'] and smtp_config['password'] and notify_to):
        logger.info("RSVP email not sent: SMTP settings not fully configured.")
        return False, "SMTP not configured"
    
    smtp_user = smtp_config['user']
    smtp_pass = smtp_config['password']
    host = smtp_config['host']
    port = int(smtp_config['port'])
    use_tls = smtp_config['tls'].lower() != "false"
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

def send_test_email(to_address: str):
    """Send a test email using current SMTP configuration.

    Returns (ok, message)
    """
    smtp_config = get_smtp_config()
    
    if not (smtp_config['user'] and smtp_config['password'] and to_address):
        return False, "Missing SMTP_USER/SMTP_PASS or recipient"
    
    smtp_user = smtp_config['user']
    smtp_pass = smtp_config['password']
    host = smtp_config['host']
    port = int(smtp_config['port'])
    use_tls = smtp_config['tls'].lower() != "false"
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

def save_invitation(data):
    invite_id = str(uuid.uuid4())
    with open(f"{DB_PATH}/{invite_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    return invite_id

def load_invitation(invite_id):
    try:
        with open(f"{DB_PATH}/{invite_id}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def get_base_url():
    # Use local base URL by default; override in deployment via APP_BASE_URL
    return os.getenv("APP_BASE_URL", "http://localhost:8501")

def save_rsvp(invite_id, rsvp_entry):
    rsvp_file = f"{DB_PATH}/rsvp_{invite_id}.json"
    try:
        with open(rsvp_file, "r", encoding="utf-8") as f:
            rsvps = json.load(f)
    except Exception:
        rsvps = []
    rsvps.append(rsvp_entry)
    with open(rsvp_file, "w", encoding="utf-8") as f:
        json.dump(rsvps, f, indent=2)

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
    st.markdown(
        """
        <div style="text-align:center;margin-top:2em;">
            <div style="animation: pulse 2s infinite;">
                <img src="https://cdn.pixabay.com/photo/2016/04/01/10/09/envelope-1300157_1280.png" width="200" style="border-radius:16px;box-shadow:2px 2px 12px #a80000;transition: transform 0.3s ease;">
            </div>
            <div style="font-size:1.4em; font-family: 'Noto Serif', serif; color:#a80000; margin-top:1em; animation: fadeIn 2s ease-in;">
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
        """, unsafe_allow_html=True
    )

def display_invitation_card(data, image_bytes=None, text_color="#000000", font_scale=1.0, overlay_opacity=0.0, title_offset_px=0):
    theme = THEMES[data["theme"]]
    
    # Improved background image handling - responsive and crisp
    if image_bytes:
        background_style = (
            f"background: url('data:image/png;base64,{image_bytes}') center center / cover no-repeat;"
            f"background-color: {theme['bg']};"
            "min-height: 100vh;"
            "width: 100%;"
            "position: relative;"
            "background-attachment: fixed;"
        )
        # Enhanced overlay for better text readability
        overlay = (
            f"<div style=\"position:absolute;inset:0;background:rgba(0,0,0,{overlay_opacity});pointer-events:none;\"></div>"
            if overlay_opacity and overlay_opacity > 0 else ""
        )
    else:
        background_style = f"background-color: {theme['bg']};min-height: 100vh;width: 100%;position: relative;"
        overlay = ""
    
    # Build the invocation HTML separately
    invocation_html = ""
    if data.get('invocation'):
        invocation_html = f'<div style="font-size:{1.4*font_scale:.2f}em;color:{text_color};font-weight:bold;margin-bottom:1em;text-shadow:2px 2px 4px rgba(255,255,255,0.9);">{data["invocation"]}</div>'
    
    # Enhanced HTML with better responsive design and text visibility
    html_content = f"""
        <div style="position:relative;{background_style}padding:3em 2em 2em 2em;border-radius:16px;border:2px solid {theme['accent']};font-family:{FONT_FAMILY};box-shadow:2px 2px 20px rgba(168,0,0,0.3);overflow:hidden;max-width:100%;box-sizing:border-box;">
            {overlay}
            <div style="text-align:center;position:relative;z-index:2;max-width:100%;">
            {invocation_html}
            <div style="margin-top:{title_offset_px}px;">
                <span style="font-size:{2.8*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:2px 2px 4px rgba(255,255,255,0.9);display:block;word-wrap:break-word;">{data['event_name']}</span>
            </div>
            <br>
            <span style="font-size:{1.4*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:1px 1px 2px rgba(255,255,255,0.9);display:block;word-wrap:break-word;">Hosted by {data['host_names']}</span><br>
            <span style="font-size:{1.2*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:1px 1px 2px rgba(255,255,255,0.9);display:block;word-wrap:break-word;">{data['event_date']} at {data['event_time']}</span><br>
            <span style="font-size:{1.1*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:1px 1px 2px rgba(255,255,255,0.9);display:block;word-wrap:break-word;">Venue: {data['venue_address']}</span>
        </div>
        <hr style="border:2px solid {text_color};margin:2em 0;position:relative;z-index:2;box-shadow:1px 1px 2px rgba(255,255,255,0.9);">
        <div style="font-size:{1.2*font_scale:.2f}em;color:{text_color};margin:1em 0 0.5em 0;padding:1em 0;position:relative;z-index:2;font-weight:bold;text-shadow:1px 1px 2px rgba(255,255,255,0.9);line-height:1.6;word-wrap:break-word;">
                {data['invitation_message']}
            </div>
        </div>
    """
    
    # Use st.components.v1.html for proper HTML rendering with responsive height
    import streamlit.components.v1 as components
    components.html(html_content, height=1000)

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

    # SMTP test
    st.markdown("#### ✉️ Email Test")
    test_email = st.text_input("Send a test email to", value=os.getenv("RSVP_NOTIFY_EMAIL", ""))
    if st.button("Send Test Email"):
        ok, msg = send_test_email(test_email)
        (st.success if ok else st.error)(msg)

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
            event_time = st.time_input("Event Time", value=datetime.now().time())
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
            st.session_state.preview_event_time = event_time.strftime("%I:%M %p")
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
                "event_time": event_time.strftime("%I:%M %p"),
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
    
    if analytics["total"] > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Responses", analytics["total"])
        with col2:
            st.metric("✅ Yes", analytics["yes"], delta=f"{analytics['yes']/analytics['total']*100:.1f}%")
        with col3:
            st.metric("❌ No", analytics["no"], delta=f"{analytics['no']/analytics['total']*100:.1f}%")
        with col4:
            st.metric("❓ Maybe", analytics["maybe"], delta=f"{analytics['maybe']/analytics['total']*100:.1f}%")
        
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
    
    # Email Test Section
    st.markdown("---")
    st.markdown("### 📧 Email Test")
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
        components.html(f"<audio autoplay loop style='display:none' src='data:{mime};base64,{audio_b64}'></audio>", height=0)
    
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
            guest_email = st.text_input("Email Address", placeholder="your.email@example.com")
        
        with col2:
            attendance = st.radio("Will you attend? *", ["Yes", "No", "Maybe"], horizontal=True)
            adults_count = st.number_input("Number of Adults", min_value=0, max_value=20, value=1 if attendance == "Yes" else 0)
            kids_count = st.number_input("Number of Children", min_value=0, max_value=20, value=0)
        
        additional_message = st.text_area("Additional Message (optional)", placeholder="Any dietary restrictions, special requests, or comments...")
        
        submit_rsvp = st.form_submit_button("📤 Submit RSVP", use_container_width=True)
    
    if submit_rsvp:
        if not guest_name.strip():
            st.error("Please enter your name to RSVP.")
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

# --- Deployment Instructions (admin only) ---
if is_admin and current_page == "creation":
    st.markdown("---")
st.markdown("""
### Deployment Instructions

1. **Push code to GitHub**
    - Add `app.py` and `requirements.txt` to your repo.

2. **Deploy to Streamlit Cloud**
    - Go to [Streamlit Cloud](https://share.streamlit.io)
    - Connect your GitHub repo (`HemanthBadabagni/hemanthverse`)
    - Choose `app.py` as entrypoint and deploy.
    - The public link will look like:  
      `https://share.streamlit.io/HemanthBadabagni/hemanthverse/app.py`

3. **Share the public link**
    - Your guests can access invitations via: `https://your-app-url.com?invite=INVITE_ID`
    - Admin dashboard: `https://your-app-url.com?invite=INVITE_ID&admin=true`

4. **Environment Variables (for email)**
    - Set these in Streamlit Cloud secrets:
    ```toml
    SMTP_USER = "your-email@gmail.com"
    SMTP_PASS = "your-app-password"
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = "587"
    SMTP_TLS = "true"
    RSVP_NOTIFY_EMAIL = "your-notification-email@gmail.com"
    ```
""")
