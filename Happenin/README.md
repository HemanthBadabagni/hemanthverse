# HemanthVerse Invitations 🎉

A beautiful Streamlit application for creating traditional Indian ceremony invitations with local file support and comprehensive testing.

## 🎯 Event Details

**Event Name:** Shubha Gruha Praveshah  
**Host Names:** Mounika, Hemanth & Viraj  
**Date:** November 13, 2025  
**Time:** 4:00 PM  
**Venue:** 3108 Honerywood Drive, Leander, TX -78641  
**Invocation:** ॐ श्री गणेशाय नमः  

## 📁 Project Structure

```
Happenin/
├── app.py                          # Main Streamlit application
├── IMG_7653.PNG                    # Background image for invitations
├── mridangam-tishra-33904.mp3      # Background music
├── requirements.txt                 # Python dependencies
├── test_invitations.py             # Comprehensive test suite
├── local_preview.py                # Local testing script
└── README.md                       # This file
```

## 🚀 Quick Start

### Option 1: Using Local Preview Script (Recommended)
```bash
python local_preview.py
```
Follow the interactive menu to:
1. Check files and dependencies
2. Install dependencies
3. Run tests
4. Start local preview

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_invitations.py

# Start the app
streamlit run app.py
```

## 🧪 Testing Features

### Local Testing Section
The app includes a dedicated testing section with:
- **Create Test Invitation**: Generates a test invitation using your local files
- **Load Test Data**: Pre-fills the form with the provided event data
- **Local Preview**: Shows the invitation without deployment
- **Test URL**: Provides a local URL for testing

### Test Suite
Comprehensive test coverage including:
- ✅ Data validation tests
- ✅ File handling tests
- ✅ Storage and retrieval tests
- ✅ Test data structure validation
- ✅ Error handling tests

Run tests with:
```bash
python test_invitations.py
```

## 🎨 Features

### Invitation Creation
- **Event Details**: Name, hosts, date, time, venue
- **Customization**: Themes, invocation, invitation message
- **Media Support**: Background images and music
- **Validation**: Comprehensive form validation

### Themes Available
- **Floral**: Warm floral design with red accents
- **Temple**: Traditional temple theme with gold accents
- **Simple Gold**: Clean gold theme
- **Classic Red**: Traditional red theme

### RSVP System
- Guest name and email collection
- Attendance confirmation (Yes/No/Maybe)
- Response tracking and display
- Timestamp recording

### Sharing Features
- WhatsApp sharing integration
- Email sharing integration
- Downloadable background images
- Shareable invitation links

## 🔧 Technical Details

### Dependencies
- `streamlit>=1.28.0`: Web application framework
- `Pillow>=10.0.0`: Image processing

### File Handling
- Local file loading with base64 encoding
- Image processing and optimization
- Audio file support (MP3/WAV)
- Error handling for missing files

### Data Storage
- JSON-based invitation storage
- UUID-based invitation IDs
- RSVP data persistence
- Local file system storage

## 🌐 Deployment

### Streamlit Cloud
1. Push code to GitHub repository
2. Connect to [Streamlit Cloud](https://share.streamlit.io)
3. Deploy with `app.py` as entrypoint
4. Share the public URL

### Local Development
- Use `local_preview.py` for easy local testing
- Test with local files before deployment
- Validate functionality with test suite

## 🎯 Usage Instructions

### Creating an Invitation
1. **Fill Form**: Enter event details, hosts, date, time, venue
2. **Add Media**: Upload background image and music (optional)
3. **Choose Theme**: Select from available themes
4. **Preview**: Review the invitation before generating
5. **Generate Link**: Create shareable invitation URL
6. **Share**: Use WhatsApp/Email sharing or direct link

### Testing Locally
1. **Use Test Data**: Click "Load Test Data" to pre-fill form
2. **Create Test Invitation**: Use local files for testing
3. **Preview**: See invitation with your local assets
4. **Test RSVP**: Validate RSVP functionality
5. **Share Test**: Use local URL for testing

### RSVP Management
- Guests can RSVP through the invitation link
- Responses are stored locally
- View all RSVPs on the invitation page
- Track attendance status and timestamps

## 🐛 Troubleshooting

### Common Issues
1. **Missing Files**: Ensure all required files are in the same directory
2. **Dependencies**: Run `pip install -r requirements.txt`
3. **Port Conflicts**: Ensure port 8501 is available
4. **File Permissions**: Check read permissions for image/audio files

### Error Messages
- **Validation Errors**: Check required fields are filled
- **File Errors**: Verify file formats and permissions
- **Storage Errors**: Check write permissions for invitations folder

## 📝 Development Notes

### Code Structure
- **Modular Design**: Separate functions for different features
- **Error Handling**: Comprehensive try-catch blocks
- **Logging**: Built-in logging for debugging
- **Validation**: Input validation at multiple levels

### Testing Strategy
- **Unit Tests**: Individual function testing
- **Integration Tests**: End-to-end workflow testing
- **Mock Testing**: Isolated testing with mocked dependencies
- **File Testing**: Local file handling validation

## 🎉 Event Information

This invitation system is specifically configured for:

**Shubha Gruha Praveshah** - A housewarming ceremony celebrating the divine blessings of Lord Venkateswara. The invitation includes traditional Sanskrit invocation and creates a beautiful, shareable digital invitation perfect for modern celebrations while maintaining cultural authenticity.

---

*Created with ❤️ for traditional Indian ceremonies*

