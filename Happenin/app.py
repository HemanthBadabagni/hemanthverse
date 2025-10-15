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
    return load_local_file("IMG_7653.PNG")

def get_local_music_base64():
    """Get the local music file as base64"""
    return load_local_file("mridangam-tishra-33904.mp3")

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

    - Auto: picks dark (#111111) on light backgrounds, light (#f8f8f8) on dark.
    - Dark/Light: force preset colors.
    - Custom: returns provided custom color.
    """
    if mode == "Custom":
        return custom_color or "#000000"
    if mode == "Dark":
        return "#111111"
    if mode == "Light":
        return "#f8f8f8"
    luminance = compute_average_luminance(image_base64)
    if luminance is None:
        return "#111111"
    return "#111111" if luminance > 0.5 else "#f8f8f8"

def send_rsvp_email(invite_id, rsvp_entry):
    """Send an email notification for a new RSVP if SMTP env vars are set.

    Expected environment variables:
      - SMTP_HOST (default: smtp.gmail.com)
      - SMTP_PORT (default: 587)
      - SMTP_USER
      - SMTP_PASS
      - SMTP_TLS (default: true)
      - RSVP_NOTIFY_EMAIL (comma-separated recipients; default provided)
    """
    notify_to = os.getenv("RSVP_NOTIFY_EMAIL", "hemanthb.0445@gmail.com")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    if not (smtp_user and smtp_pass and notify_to):
        logger.info("RSVP email not sent: SMTP settings not fully configured.")
        return
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    use_tls = os.getenv("SMTP_TLS", "true").lower() != "false"
    try:
        data = load_invitation(invite_id) or {}
        event_name = data.get("event_name", "Your Event")
        subject = f"RSVP: {event_name} — {rsvp_entry['name']} ({rsvp_entry['response']})"
        body = (
            f"Event: {event_name}\n"
            f"Invite ID: {invite_id}\n\n"
            f"Name: {rsvp_entry['name']}\n"
            f"Email: {rsvp_entry.get('email','')}\n"
            f"Response: {rsvp_entry['response']}\n"
            f"Message: {rsvp_entry.get('message','')}\n"
            f"Timestamp: {rsvp_entry['timestamp']}\n"
        )
        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = notify_to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("RSVP notification email sent.")
    except Exception as e:
        logger.warning(f"Failed to send RSVP email: {e}")

def validate_event_data(data):
    """Validate event data for required fields"""
    required_fields = ["event_name", "host_names", "event_date", "event_time", "venue_address", "invitation_message"]
    missing_fields = []
    
    for field in required_fields:
        if not data.get(field) or (isinstance(data.get(field), str) and data.get(field).strip() == ""):
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, "Valid"

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
        is_valid, message = validate_event_data(test_data)
        if not is_valid:
            logger.error(f"Test data validation failed: {message}")
            return None, message
        
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
    return "https://share.streamlit.io/HemanthBadabagni/hemanthverse/app.py"

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
    """Return RSVPs as CSV bytes."""
    import csv
    from io import StringIO
    rows = load_rsvps(invite_id)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["name","email","response","message","timestamp"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "name": row.get("name",""),
            "email": row.get("email",""),
            "response": row.get("response",""),
            "message": row.get("message",""),
            "timestamp": row.get("timestamp",""),
        })
    return output.getvalue().encode("utf-8")

def clear_rsvps(invite_id):
    rsvp_file = f"{DB_PATH}/rsvp_{invite_id}.json"
    with open(rsvp_file, "w", encoding="utf-8") as f:
        json.dump([], f)

def get_rsvp_analytics(invite_id):
    """Get RSVP analytics and statistics"""
    rsvps = load_rsvps(invite_id)
    if not rsvps:
        return {
            "total": 0,
            "yes": 0,
            "no": 0,
            "maybe": 0,
            "yes_list": [],
            "no_list": [],
            "maybe_list": []
        }
    
    yes_list = []
    no_list = []
    maybe_list = []
    
    for rsvp in rsvps:
        if rsvp["response"] == "Yes":
            yes_list.append(rsvp)
        elif rsvp["response"] == "No":
            no_list.append(rsvp)
        else:
            maybe_list.append(rsvp)
    
    return {
        "total": len(rsvps),
        "yes": len(yes_list),
        "no": len(no_list),
        "maybe": len(maybe_list),
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
    # Use background image with better positioning to show more of the image
    if image_bytes:
        background_style = (
            f"background: url('data:image/png;base64,{image_bytes}') center top / cover no-repeat;"
            f"background-color: {theme['bg']};"
            "min-height: 900px;"
            "position: relative;"
        )
        # Optional overlay to improve readability
        overlay = (
            f"<div style=\"position:absolute;inset:0;background:rgba(0,0,0,{overlay_opacity});\"></div\>"
            if overlay_opacity and overlay_opacity > 0 else ""
        )
    else:
        background_style = f"background-color: {theme['bg']};min-height: 900px;position: relative;"
        overlay = ""
    # Build the invocation HTML separately
    invocation_html = ""
    if data.get('invocation'):
        invocation_html = f'<div style="font-size:{1.4*font_scale:.2f}em;color:{text_color};font-weight:bold;margin-bottom:1em;text-shadow:2px 2px 4px rgba(255,255,255,0.8);">{data["invocation"]}</div>'
    
    # Build HTML using direct string concatenation to avoid formatting issues
    html_content = f"""
    <div style="position:relative;{background_style}padding:2em 2em 1em 2em;border-radius:16px;border:2px solid {theme['accent']};font-family:{FONT_FAMILY};box-shadow:2px 2px 20px #a80000;overflow:hidden;">
        {overlay}
        <div style="text-align:center;position:relative;z-index:1;">
            {invocation_html}
            <div style="margin-top:{title_offset_px}px;">
                <span style="font-size:{2.8*font_scale:.2f}em;color:{text_color};font-weight:bold;text-shadow:2px 2px 4px rgba(255,255,255,0.8);">{data['event_name']}</span>
            </div>
            <br>
            <span style="font-size:{1.4*font_scale:.2f}em;color:{text_color};font-weight:600;text-shadow:1px 1px 2px rgba(255,255,255,0.8);">Hosted by {data['host_names']}</span><br>
            <span style="font-size:{1.2*font_scale:.2f}em;color:{text_color};font-weight:500;text-shadow:1px 1px 2px rgba(255,255,255,0.8);">{data['event_date']} at {data['event_time']}</span><br>
            <span style="font-size:{1.1*font_scale:.2f}em;color:{text_color};font-weight:500;text-shadow:1px 1px 2px rgba(255,255,255,0.8);">Venue: {data['venue_address']}</span>
        </div>
        <hr style="border:2px solid {text_color};margin:2em 0;position:relative;z-index:1;box-shadow:1px 1px 2px rgba(255,255,255,0.8);">
        <div style="font-size:{1.2*font_scale:.2f}em;color:{text_color};margin:1em 0 0.5em 0;padding:1em 0;position:relative;z-index:1;font-weight:500;text-shadow:1px 1px 2px rgba(255,255,255,0.8);line-height:1.6;">
            {data['invitation_message']}
        </div>
    </div>
    """
    
    # Use st.components.v1.html for proper HTML rendering
    import streamlit.components.v1 as components
    components.html(html_content, height=900)

# --- Header ---
st.markdown(
    f"""
    <div style="background:#a80000;color:#ffd700;padding:1em 0;text-align:center;border-radius:8px;font-family:{FONT_FAMILY};">
        <h1 style="margin-bottom:0;">HemanthVerse Invitations</h1>
        <span style="font-size:1.2em;">Create beautiful invitations for traditional Indian ceremonies</span>
    </div>
    """, unsafe_allow_html=True,
)

# --- Local Preview Section ---
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
        
        # Play music if available
        if music_bytes and music_filename:
            st.audio(music_bytes, format=f"audio/{music_filename.split('.')[-1]}")
        
        # Local URL for testing
        local_url = f"http://localhost:8501?invite={st.session_state.test_invite_id}"
        st.markdown("**Local Test URL:**")
        st.code(local_url)
        
        if st.button("🗑️ Clear Test Invitation"):
            del st.session_state.test_invite_id
            st.rerun()

st.markdown("---")

invite_id = st.query_params.get("invite", None)

if invite_id:
    data = load_invitation(invite_id)
    if data:
        image_bytes = data.get("image_base64")
        music_bytes = None
        music_filename = None
        if data.get("music_base64") and data.get("music_filename"):
            music_bytes = base64.b64decode(data["music_base64"])
            music_filename = data["music_filename"]
        if "envelope_open" not in st.session_state:
            st.session_state["envelope_open"] = False

        if not st.session_state["envelope_open"]:
            display_envelope()
            if st.button("Open Envelope"):
                st.session_state["envelope_open"] = True
        else:
            st.markdown("## 🎉 Your Invitation")
            auto_color = choose_text_color(image_bytes, mode=st.session_state.get("text_color_mode", "Auto"), custom_color=st.session_state.get("custom_text_color", "#000000"))
            display_invitation_card(
                data,
                image_bytes,
                text_color=auto_color,
                font_scale=st.session_state.get("font_scale", 1.0),
                overlay_opacity=st.session_state.get("overlay_opacity", 0.15),
                title_offset_px=st.session_state.get("title_offset_px", -20),
            )
            # Manager Mode controls (enable with ?admin=1)
            is_admin = st.query_params.get("admin", "0") in ("1", "true", "yes")
            if is_admin:
                st.markdown("---")
                st.markdown("### 🛠️ Manager Mode")
                colA, colB, colC, colD = st.columns(4)
                with colA:
                    if st.button("Add sample RSVP"):
                        sample = {
                            "name": "Sample Guest",
                            "email": "sample@example.com",
                            "response": "Yes",
                            "message": "Looking forward!",
                            "timestamp": str(datetime.utcnow()),
                        }
                        save_rsvp(invite_id, sample)
                        st.success("Sample RSVP added.")
                        st.rerun()
                with colB:
                    csv_bytes = export_rsvps_csv(invite_id)
                    st.download_button("Export RSVPs CSV", csv_bytes, file_name=f"rsvps_{invite_id}.csv", mime="text/csv")
                with colC:
                    if st.button("Clear RSVPs"):
                        clear_rsvps(invite_id)
                        st.success("All RSVPs cleared.")
                        st.rerun()
                with colD:
                    if st.button("Reset Envelope"):
                        st.session_state["envelope_open"] = False
                        st.rerun()
            
            # Play music if available with better styling
            if music_bytes and music_filename:
                st.markdown("### 🎵 Background Music")
                st.audio(music_bytes, format=f"audio/{music_filename.split('.')[-1]}")
            
            st.markdown("---")
            
            # Enhanced sharing section
            st.markdown("### 📤 Share Your Invitation")
            st.success("Share this link with friends via WhatsApp/email!")
            url = f"{get_base_url()}?invite={invite_id}"
            st.code(url)
            st.markdown(
                f"[📱 Share via WhatsApp](https://wa.me/?text=Invitation%20Link%3A%20{url}) &nbsp; | &nbsp; [📧 Share via Email](mailto:?subject=Invitation&body=Invitation%20Link%3A%20{url})"
            )
            
            # Download options
            if image_bytes:
                st.download_button("📥 Download Invitation Background", base64.b64decode(image_bytes), file_name="invitation_background.png", mime="image/png")

            # --- Enhanced RSVP Section ---
            st.markdown("---")
            st.markdown("### 📝 RSVP to This Event")
            
            with st.form("rsvp_form"):
                col1, col2 = st.columns(2)
                with col1:
                    guest_name = st.text_input("Your Name *", placeholder="Enter your full name")
                with col2:
                    guest_email = st.text_input("Email (optional)", placeholder="your.email@example.com")
                
                will_attend = st.radio("Will you attend?", ["Yes", "No", "Maybe"], horizontal=True)
                
                additional_message = st.text_area("Additional Message (optional)", placeholder="Any dietary restrictions, special requests, or comments...")
                
                submit_rsvp = st.form_submit_button("📤 Submit RSVP", use_container_width=True)
            
            if submit_rsvp:
                if not guest_name.strip():
                    st.error("Please enter your name to RSVP.")
                else:
                    rsvp_entry = {
                        "name": guest_name,
                        "email": guest_email,
                        "response": will_attend,
                        "message": additional_message,
                        "timestamp": str(datetime.utcnow())
                    }
                    save_rsvp(invite_id, rsvp_entry)
                    # Optional email notification
                    send_rsvp_email(invite_id, rsvp_entry)
                    st.success("🎉 Thank you! Your RSVP has been recorded.")
                    st.rerun()

            # --- RSVP Analytics Dashboard ---
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
    else:
        st.error("Invitation not found.")
else:
    st.markdown("## 📝 Create New Invitation")
    
    # Always load default values automatically
    default_values = {
        'event_name': TEST_EVENT_DATA["event_name"],
        'host_names': TEST_EVENT_DATA["host_names"],
        'event_date': datetime.strptime(TEST_EVENT_DATA["event_date"], "%Y-%m-%d").date(),
        'event_time': datetime.strptime(TEST_EVENT_DATA["event_time"], "%I:%M %p").time(),
        'venue_address': TEST_EVENT_DATA["venue_address"],
        'invocation': TEST_EVENT_DATA["invocation"],
        'invitation_message': TEST_EVENT_DATA["invitation_message"],
        'theme': TEST_EVENT_DATA["theme"]
    }
    
    # Load test data if requested (for manual override)
    if hasattr(st.session_state, 'load_test_data') and st.session_state.load_test_data:
        st.success("✅ Test data loaded! You can modify the fields below.")
        del st.session_state.load_test_data
    else:
        st.info("🎯 Default values loaded automatically. Modify any fields as needed.")
    
    with st.form("invitation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input("Event Name", value=default_values.get('event_name', ''))
            host_names = st.text_input("Host Names", value=default_values.get('host_names', ''))
            event_date = st.date_input("Event Date", value=default_values.get('event_date', datetime.today()))
            event_time = st.time_input("Event Time", value=default_values.get('event_time', datetime.now().time()))
        
        with col2:
            venue_address = st.text_area("Venue Address", value=default_values.get('venue_address', ''))
            invocation = st.text_area("Optional Invocation or Sanskrit Verse", value=default_values.get('invocation', ''))
        
        invitation_message = st.text_area("Invitation Message", value=default_values.get('invitation_message', ''), height=150)
        
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Background Image:**")
            if os.path.exists("IMG_7653.PNG"):
                st.success("✅ IMG_7653.PNG found - will be used automatically")
                st.info("💡 You can upload a different image below if desired")
            else:
                st.warning("⚠️ IMG_7653.PNG not found")
            image_file = st.file_uploader("Upload Background Image (deity, temple, or custom design)", type=["jpg", "png"])
            
            st.markdown("**Background Music:**")
            if os.path.exists("mridangam-tishra-33904.mp3"):
                st.success("✅ mridangam-tishra-33904.mp3 found - will be used automatically")
                st.info("💡 You can upload different music below if desired")
            else:
                st.warning("⚠️ mridangam-tishra-33904.mp3 not found")
            music_file = st.file_uploader("Upload Music (MP3/WAV, optional)", type=["mp3", "wav"])
        with col4:
            theme = st.selectbox("Theme Choice", list(THEMES.keys()), index=list(THEMES.keys()).index(default_values.get('theme', 'Temple')))
            st.markdown("**Appearance:**")
            text_color_mode = st.selectbox("Text color", ["Auto", "Dark", "Light", "Custom"], index=0)
            custom_text_color = "#000000"
            if text_color_mode == "Custom":
                custom_text_color = st.color_picker("Pick custom text color", value="#111111")
            font_scale = st.slider("Font scale", min_value=0.8, max_value=1.6, value=1.0, step=0.05)
            overlay_opacity = st.slider("Overlay dimmer", min_value=0.0, max_value=0.6, value=0.15, step=0.05)
            title_offset_px = st.slider("Title vertical offset (px)", min_value=-200, max_value=200, value=-20, step=5)
        
        submit = st.form_submit_button("🎨 Preview & Generate Link")

    if submit:
        # Validate form data
        form_data = {
            "event_name": event_name,
            "host_names": host_names,
            "event_date": event_date.strftime("%d-%b-%Y"),
            "event_time": event_time.strftime("%I:%M %p"),
            "venue_address": venue_address,
            "invitation_message": invitation_message,
        }
        
        is_valid, validation_message = validate_event_data(form_data)
        if not is_valid:
            st.error(f"❌ Validation Error: {validation_message}")
            st.stop()
        
        # Process uploaded files or use local files
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
        else:
            # Use local image file
            image_base64 = get_local_image_base64()
            if image_base64:
                image_bytes = image_base64
                st.success("✅ Using local image: IMG_7653.PNG")
            else:
                st.warning("⚠️ No image file available")

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
        else:
            # Use local music file
            music_base64 = get_local_music_base64()
            if music_base64:
                music_bytes = base64.b64decode(music_base64)
                music_filename = "mridangam-tishra-33904.mp3"
                st.success("✅ Using local music: mridangam-tishra-33904.mp3")
            else:
                st.info("ℹ️ No music file available")

        # Create invitation data
        data = {
            "event_name": event_name,
            "host_names": host_names,
            "event_date": event_date.strftime("%d-%b-%Y"),
            "event_time": event_time.strftime("%I:%M %p"),
            "venue_address": venue_address,
            "invocation": invocation,
            "invitation_message": invitation_message,
            "theme": theme,
            "image_base64": image_base64,
            "music_base64": music_base64,
            "music_filename": music_filename,
        }

        # Persist appearance controls in session for invite view as well
        st.session_state["text_color_mode"] = text_color_mode
        st.session_state["custom_text_color"] = custom_text_color
        st.session_state["font_scale"] = font_scale
        st.session_state["overlay_opacity"] = overlay_opacity
        st.session_state["title_offset_px"] = title_offset_px

        st.markdown("### 🎨 Invitation Preview")
        preview_color = choose_text_color(image_bytes, mode=text_color_mode, custom_color=custom_text_color)
        display_invitation_card(
            data,
            image_bytes,
            text_color=preview_color,
            font_scale=font_scale,
            overlay_opacity=overlay_opacity,
            title_offset_px=title_offset_px,
        )
        if music_bytes and music_filename:
            st.audio(music_bytes, format=f"audio/{music_filename.split('.')[-1]}")
        
        # Save invitation
        try:
            invite_id = save_invitation(data)
            url = f"{get_base_url()}?invite={invite_id}"
            
            st.markdown("---")
            st.success("🎉 Your invitation link is ready! Share it below.")
            st.code(url)
            st.markdown(
                f"[Share via WhatsApp](https://wa.me/?text=Invitation%20Link%3A%20{url}) &nbsp; | &nbsp; [Share via Email](mailto:?subject=Invitation&body=Invitation%20Link%3A%20{url})"
            )
            if image_bytes:
                st.download_button("📥 Download Invitation Background", base64.b64decode(image_bytes), file_name="invitation_background.png", mime="image/png")

            st.markdown("##### 📝 RSVP (Native form now shown on the invite page)")
        except Exception as e:
            st.error(f"❌ Error saving invitation: {str(e)}")
            logger.error(f"Error saving invitation: {str(e)}")

# --- Deployment Instru  ctions ---
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
    - Copy and share the deployed app's URL!
""")
