# 🎓 QR Attendance System with Face & Speech Verification

A modern attendance tracking system using QR codes, face recognition, and speech verification.

## ✨ Features

- **📱 QR Code Check-In**: Students scan QR codes to access check-in page
- **👤 Face Verification**: Real-time face detection and verification using face-api.js
- **🎤 Speech Verification**: Browser-based speech-to-text verification (no server processing!)
- **👨‍🏫 Teacher Dashboard**: Manage sessions, view attendance, export to CSV
- **🔒 Secure**: Dual biometric verification (face + speech)
- **📊 Export Data**: Download attendance records as CSV

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/qr-attendance.git
cd qr-attendance
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Open in browser**
```
http://localhost:5000
```

### Deploy to Render

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## 📖 Usage

### For Teachers

1. **Login**: Navigate to `/teacher/login` (default password: `admin`)
2. **Start Session**: Click "Start New Session" to generate QR code
3. **Share QR Code**: Display QR code for students to scan
4. **View Attendance**: See real-time attendance list
5. **Export**: Download attendance as CSV

### For Students

1. **Enroll**: First-time users go to `/enroll`
   - Enter name and student ID
   - Allow camera access
   - Position face for detection
   - Allow microphone access
   - Speak the phrase shown
   - Submit enrollment

2. **Check-In**: Scan teacher's QR code or use link
   - Enter student ID
   - Verify face
   - Speak the phrase shown
   - Submit attendance

## 🛠️ Technology Stack

### Backend
- **Flask** - Python web framework
- **Gunicorn** - WSGI HTTP server

### Frontend
- **face-api.js** - Face detection and recognition
- **Web Speech API** - Browser speech recognition
- **Vanilla JavaScript** - No frameworks needed!

### Storage
- **JSON files** - Simple file-based storage (upgrade to database for production)

## 🔒 Security Features

- Dual biometric verification (face + speech)
- Session-based QR codes
- Teacher authentication
- HTTPS required for camera/microphone access

## 📱 Browser Compatibility

| Feature | Chrome | Edge | Safari | Firefox |
|---------|--------|------|--------|---------|
| Face Recognition | ✅ | ✅ | ✅ | ✅ |
| Speech Recognition | ✅ | ✅ | ✅ | ⚠️ Limited |
| Camera Access | ✅ | ✅ | ✅ | ✅ |

**Note**: Speech recognition works best on Chrome and Edge.

## 🌐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TEACHER_PASSWORD` | Password for teacher login | `admin` |
| `PORT` | Server port | `5000` |

## 📂 Project Structure

```
qr-attendance/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── .gitignore            # Git ignore rules
├── attendance.json       # Attendance records (auto-created)
├── students.json         # Student data (auto-created)
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   ├── js/
│   │   ├── face-api.min.js
│   │   ├── face-verification.js
│   │   └── voice-recorder.js  # Speech verification
│   └── models/           # face-api.js models
└── templates/
    ├── index.html        # Landing page
    ├── enroll.html       # Student enrollment
    ├── checkin.html      # Student check-in
    ├── teacher_login.html
    └── teacher_panel.html
```

## 🐛 Troubleshooting

### Camera not working
- Ensure HTTPS is enabled
- Grant camera permissions in browser
- Check browser console for errors

### Speech recognition not working
- Use Chrome or Edge browser
- Ensure HTTPS is enabled
- Grant microphone permissions
- Speak clearly and at normal volume

### Face not detected
- Ensure good lighting
- Position face in center of frame
- Remove glasses or masks if possible

## 📝 License

MIT License - feel free to use for your projects!

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📧 Support

For issues and questions, please open a GitHub issue.

---

Made with ❤️ for modern attendance tracking
