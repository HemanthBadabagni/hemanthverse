import streamlit as st
import uuid
import json
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import base64

# --- Configuration ---
DB_PATH = "invitations"
os.makedirs(DB_PATH, exist_ok=True)

THEMES = {
    "Floral": {"bg": "#fff0e6", "accent": "#b22222"},
    "Temple": {"bg": "#f6eedf", "accent": "#d4af37"},
    "Simple Gold": {"bg": "#fffbe6", "accent": "#ffd700"},
    "Classic Red": {"bg": "#a80000", "accent": "#ffd1b3"},
}

LANGUAGES = ["English", "Telugu", "Hindi"]
FONT_FAMILY = "'Noto Serif', 'Poppins', serif"

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
    # For Streamlit Cloud, URL is usually https://share.streamlit.io/<user>/<repo>/<file>
    # For local, return empty
    return "https://share.streamlit.io/HemanthBadabagni/hemanthverse/app.py"

def display_invitation(data, image_bytes=None):
    theme = THEMES[data["theme"]]
    st.markdown(
        f"""
        <div style="background:{theme['bg']};padding:2em;border-radius:16px;border:2px solid {theme['accent']};font-family:{FONT_FAMILY};">
            <div style="text-align:center;">
                <span style="font-size:2.3em;color:{theme['accent']};font-weight:bold;">{data['event_name']}</span><br>
                <span style="font-size:1em;color:#444;">Hosted by {data['host_names']}</span><br>
                <span style="font-size:1em;color:#444;">{data['event_date']} at {data['event_time']}</span><br>
                <span style="font-size:1em;color:#444;">Venue: {data['venue_address']}</span><br>
                <span style="font-size:1em;color:#444;">Language: {data['language']}</span>
            </div>
            <hr style="border:1px solid {theme['accent']};margin:2em 0;">
            {f"<div style='font-size:1.1em;color:#a80000;font-weight:bold;margin-bottom:1em;'>{data['invocation']}</div>" if data['invocation'] else ""}
            {f"<img src='data:image/png;base64,{image_bytes}' style='width:180px;border-radius:8px;margin-bottom:1em;'/>" if image_bytes else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Header ---
st.markdown(
    f"""
    <div style="background:#a80000;color:#ffd700;padding:1em 0;text-align:center;border-radius:8px;font-family:{FONT_FAMILY};">
        <h1 style="margin-bottom:0;">HemanthVerse Invitations</h1>
        <span style="font-size:1.2em;">Create beautiful invitations for traditional Indian ceremonies</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- RSVP Helper ---
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

# --- Main ---
invite_id = st.query_params.get("invite", None)

if invite_id:
    # Display invitation via unique URL
    data = load_invitation(invite_id)
    if data:
        image_bytes = data.get("image_base64")
        st.markdown("## Your Invitation")
        display_invitation(data, image_bytes)
        st.markdown("---")
        st.success("Share this link with friends via WhatsApp/email!")
        url = f"{get_base_url()}?invite={invite_id}"
        st.code(url)
        st.markdown(
            f"[Share via WhatsApp](https://wa.me/?text=Invitation%20Link%3A%20{url}) &nbsp; | &nbsp; [Share via Email](mailto:?subject=Invitation&body=Invitation%20Link%3A%20{url})"
        )
        # Bonus: Download as image
        if image_bytes:
            st.download_button("Download Invitation Image", base64.b64decode(image_bytes), file_name="invitation.png", mime="image/png")

        # --- RSVP Form ---
        st.markdown("### RSVP")
        with st.form("rsvp_form"):
            guest_name = st.text_input("Your Name")
            guest_email = st.text_input("Email (optional)")
            will_attend = st.radio("Will you attend?", ["Yes", "No", "Maybe"])
            submit_rsvp = st.form_submit_button("Submit RSVP")
        if submit_rsvp:
            rsvp_entry = {
                "name": guest_name,
                "email": guest_email,
                "response": will_attend,
                "timestamp": str(datetime.utcnow())
            }
            save_rsvp(invite_id, rsvp_entry)
            st.success("Thank you! Your RSVP has been recorded.")

        # Show RSVP responses (visible to all)
        st.markdown("#### RSVP Responses")
        rsvps = load_rsvps(invite_id)
        if rsvps:
            for entry in reversed(rsvps):
                st.markdown(f"- **{entry['name']}** ({entry['email']}) — {entry['response']} ({entry['timestamp']})")
        else:
            st.info("No RSVPs yet.")
    else:
        st.error("Invitation not found.")
else:
    # Invitation Form
    with st.form("invitation_form"):
        event_name = st.text_input("Event Name")
        host_names = st.text_input("Host Names")
        event_date = st.date_input("Event Date", value=datetime.today())
        event_time = st.time_input("Event Time", value=datetime.now().time())
        venue_address = st.text_area("Venue Address")
        language = st.selectbox("Language", LANGUAGES)
        invocation = st.text_area("Optional Invocation or Sanskrit Verse (e.g., ॐ श्री गणेशाय नमः)")
        image_file = st.file_uploader("Upload Image (deity, temple, or custom design)", type=["jpg", "png"])
        theme = st.selectbox("Theme Choice", list(THEMES.keys()))
        submit = st.form_submit_button("Preview & Generate Link")

    if submit:
        # Prepare image
        image_bytes = None
        image_base64 = None
        if image_file:
            image = Image.open(image_file)
            buf = BytesIO()
            image.save(buf, format="PNG")
            image_bytes = base64.b64encode(buf.getvalue()).decode("utf-8")
            image_base64 = image_bytes

        data = {
            "event_name": event_name,
            "host_names": host_names,
            "event_date": event_date.strftime("%d-%b-%Y"),
            "event_time": event_time.strftime("%I:%M %p"),
            "venue_address": venue_address,
            "language": language,
            "invocation": invocation,
            "theme": theme,
            "image_base64": image_base64,
        }

        st.markdown("### Invitation Preview")
        display_invitation(data, image_bytes)
        invite_id = save_invitation(data)
        url = f"{get_base_url()}?invite={invite_id}"

        st.markdown("---")
        st.success("Your invitation link is ready! Share it below.")
        st.code(url)
        st.markdown(
            f"[Share via WhatsApp](https://wa.me/?text=Invitation%20Link%3A%20{url}) &nbsp; | &nbsp; [Share via Email](mailto:?subject=Invitation&body=Invitation%20Link%3A%20{url})"
        )
        if image_bytes:
            st.download_button("Download Invitation Image", base64.b64decode(image_bytes), file_name="invitation.png", mime="image/png")

        st.markdown("##### RSVP (Native form now shown on the invite page)")

# --- Deployment Instructions ---
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
