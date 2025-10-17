# 🎉 Happenin — Create, Share, Celebrate

A beautiful, modern web application for creating and sharing traditional Indian ceremony invitations with RSVP functionality.

```
████████████████████████████████
██      H A P P E N I N      ██
████████████████████████████████

Create • Share • Celebrate
```

## ✨ Features

### 🎨 **Beautiful Invitations**
- **Customizable Design**: Font colors, sizes, background overlays
- **Responsive Images**: Perfect fit, no cropping, crisp display
- **Traditional Themes**: Temple, Wedding, Festival themes
- **Background Music**: Auto-play music for enhanced experience

### 📧 **Email Notifications & Reminders**
- **HTML Email Templates**: Professional, clean design
- **Real-time Notifications**: Instant RSVP alerts to event managers
- **Custom Reminders**: Send personalized messages to "Yes" respondents
- **Individual Emails**: Privacy-focused, no group emails
- **Fault-tolerant**: Continues sending even if some emails fail
- **Test Email Function**: Verify email functionality
- **SMTP Configuration**: Works on all deployment platforms

### 📊 **RSVP Management**
- **Live Analytics**: Real-time RSVP counts and statistics
- **Guest Details**: Name, email, attendance, guest counts
- **Email Collection**: Mandatory email for reminder functionality
- **Persistent Data**: Links work forever, data never lost
- **Export Options**: CSV download for guest lists
- **Reminder System**: Send custom messages to confirmed attendees

### 🌐 **3-Page Architecture**
- **Page 1**: Event Creation - Design your invitation
- **Page 2**: Admin Dashboard - Manage RSVPs and analytics
- **Page 3**: Public Invite - Guest-facing invitation with RSVP

## 🚀 Quick Start

### **Local Development**

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Happenin
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up email configuration (optional)**
   ```bash
   export SMTP_USER="your-email@gmail.com"
   export SMTP_PASS="your-app-password"
   export SMTP_HOST="smtp.gmail.com"
   export SMTP_PORT="587"
   export SMTP_TLS="true"
   ```
   **Note**: Email notifications are optional. The app works without SMTP configuration.

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - Go to `http://localhost:8501`
   - Start creating beautiful invitations!

### **Deployment (Streamlit Cloud)**

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy Happenin app"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Deploy your app

3. **Configure Secrets (optional)**
   - Go to Settings → Secrets
   - Add SMTP configuration for email notifications:
   ```toml
   [secrets]
   SMTP_USER = "your-email@gmail.com"
   SMTP_PASS = "your-app-password"
   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = "587"
   SMTP_TLS = "true"
   ```
   **Note**: Email notifications are optional. The app works without SMTP configuration.

## 📁 Project Structure

```
📁 Happenin/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── happenin_logo.svg         # Logo (SVG format)
├── happenin_logo.txt         # Logo (ASCII art)
├── DEPLOYMENT_GUIDE.md       # Detailed deployment instructions
├── README.md                 # This file
├── invitations/              # Auto-created data folder
│   ├── {invite_id}.json     # Invitation data
│   └── rsvp_{invite_id}.json # RSVP data
└── test_invitations.py       # Unit tests
```

## 🎯 How to Use

### **1. Create an Invitation**
- Fill in event details (name, date, venue, etc.)
- Upload background image and music
- Customize fonts and colors
- Generate your invitation link

### **2. Share Your Invitation**
- Copy the public link
- Share via WhatsApp, email, or social media
- Guests can RSVP directly on the link

### **3. Manage RSVPs**
- Use the admin dashboard to view analytics
- See real-time RSVP counts
- Send custom reminders to confirmed attendees
- Export guest lists to CSV
- Test email notifications

## 📧 Email Setup

### **Gmail Configuration**
1. **Enable 2FA** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account → Security → App passwords
   - Generate password for "Mail"
   - Use this password (not your regular password)

### **Email Features**
- **RSVP Notifications**: `Event Name - Guest Name - Yes/No`
- **Custom Reminders**: Send personalized messages to confirmed attendees
- **HTML Templates**: Professional, responsive design
- **Individual Delivery**: Privacy-focused, no group emails
- **Real-time Delivery**: Instant notifications to event manager email
- **Fault-tolerant**: Continues sending even if some emails fail
- **Test Functions**: Verify email functionality
- **Graceful Handling**: App works without SMTP configuration

## 🔧 Technical Details

### **Built With**
- **Streamlit**: Web application framework
- **Python**: Backend logic
- **HTML/CSS**: Custom styling and templates
- **JavaScript**: Music playback and interactive features
- **SMTP**: Email notifications and reminders
- **JSON**: Data persistence
- **UUID**: Unique invitation IDs

### **Data Persistence**
- **File-based Storage**: JSON files for invitations and RSVPs
- **Persistent Links**: Invitation URLs work forever
- **Real-time Updates**: RSVP counts update immediately
- **Historical Data**: All RSVPs saved with timestamps

### **Music System**
- **Auto-play Support**: Background music starts automatically
- **Browser Compatibility**: Works across all modern browsers
- **Multiple Formats**: Supports MP3, WAV, M4A, OGG, FLAC, AAC
- **Dynamic Detection**: Automatically finds music files in project directory
- **User Interaction**: Music starts on first user click (browser policy compliance)
- **Seamless Experience**: No visible controls, pure background audio

### **Deployment Platforms**
- ✅ **Streamlit Cloud** (Recommended)
- ✅ **Heroku**
- ✅ **Railway**
- ✅ **DigitalOcean**
- ✅ **AWS/GCP/Azure**

## 🧪 Testing

Run the test suite:
```bash
python test_invitations.py
```

Tests include:
- Invitation creation and storage
- RSVP functionality
- Email sending and reminders
- Music file detection and playback
- Data persistence
- File handling
- SMTP configuration validation

## 📊 Features Overview

| Feature | Status | Description |
|---------|--------|-------------|
| 🎨 Custom Invitations | ✅ | Beautiful, customizable designs |
| 📧 Email Notifications | ✅ | HTML emails with real-time delivery |
| 📧 Custom Reminders | ✅ | Send personalized messages to confirmed attendees |
| 📊 RSVP Analytics | ✅ | Live counts and detailed statistics |
| 💾 Data Persistence | ✅ | Links work forever, data never lost |
| 🌐 Multi-page UI | ✅ | Clean 3-page architecture |
| 📱 Responsive Design | ✅ | Works on all devices |
| 🎵 Background Music | ✅ | Auto-play music support |
| 📤 Export Options | ✅ | CSV download for guest lists |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🌐 Live Demo

**Try Happenin now**: [https://happenin-dhuv3putrr8ddhdufqzgcm.streamlit.app](https://happenin-dhuv3putrr8ddhdufqzgcm.streamlit.app)

## 🆘 Support

For support or questions:
- Check the [Deployment Guide](DEPLOYMENT_GUIDE.md)
- Open an issue on GitHub
- Review the test files for examples

## 🎊 Acknowledgments

Built with ❤️ for creating beautiful, memorable invitations for traditional Indian ceremonies.

---

**Happenin** — Where every celebration begins with a beautiful invitation! 🎉