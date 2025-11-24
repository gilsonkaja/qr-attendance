import os
import json
import csv
import uuid
import threading
from datetime import datetime
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect, url_for,
    send_file, flash, jsonify, make_response
)
import qrcode

# -----------------------
# Configurable settings
# -----------------------
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin")  # change for production
ATTENDANCE_FILE = "attendance.json"
STUDENTS_FILE = "students.json"  # Store student face data
HOSTNAME = None  # If you want to force a particular URL prefix (e.g. "https://example.com/"), set here.
# -----------------------

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "replace-this-secret-in-prod")
lock = threading.Lock()

# Fix for running behind a proxy (like localtunnel or ngrok)
# This ensures url_for generates HTTPS links when accessed via HTTPS tunnel
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ensure attendance file exists
def ensure_attendance_file():
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
            json.dump({"records": []}, f, indent=2)

def load_attendance():
    ensure_attendance_file()
    with lock:
        with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_attendance(data):
    with lock:
        with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# Students database helpers
def ensure_students_file():
    if not os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"students": []}, f, indent=2)

def load_students():
    ensure_students_file()
    with lock:
        with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_students(data):
    with lock:
        with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def get_student_by_id(student_id):
    """Get student data by student ID"""
    students_data = load_students()
    for student in students_data.get("students", []):
        if student.get("student_id") == student_id:
            return student
    return None

def add_or_update_student(name, student_id, face_descriptor, voice_features=None):
    """Add new student or update existing student's face and voice data"""
    students_data = load_students()
    students = students_data.get("students", [])
    
    # Check if student already exists
    for student in students:
        if student.get("student_id") == student_id:
            # Update existing student
            student["name"] = name
            student["face_descriptor"] = face_descriptor
            if voice_features:
                student["voice_features"] = voice_features
            student["updated_at"] = datetime.utcnow().isoformat() + "Z"
            save_students(students_data)
            return False  # Not new
    
    # Add new student
    new_student = {
        "name": name,
        "student_id": student_id,
        "face_descriptor": face_descriptor,
        "enrolled_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    if voice_features:
        new_student["voice_features"] = voice_features
        
    students.append(new_student)
    students_data["students"] = students
    save_students(students_data)
    return True  # New student

# ... (rest of file) ...

# Face enrollment page
@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        student_id = request.form.get("student_id", "").strip()
        face_descriptor_json = request.form.get("face_descriptor", "")
        speech_verified = request.form.get("speech_verified", "false") == "true"
        
        if not name or not student_id:
            return jsonify({"success": False, "error": "Please provide both name and student ID."}), 400
        
        if not face_descriptor_json:
            return jsonify({"success": False, "error": "Face data not captured."}), 400
            
        try:
            face_descriptor = json.loads(face_descriptor_json)
            
            # Store speech verification status (simplified - just a flag)
            voice_features_list = {"verified": speech_verified} if speech_verified else None
            
            is_new = add_or_update_student(name, student_id, face_descriptor, voice_features_list)
            
            msg = f"Successfully enrolled {name}!" if is_new else f"Updated data for {name}."
            if speech_verified:
                msg += " (Speech verified)"
                
            flash(msg, "success")
            return jsonify({"success": True, "redirect": url_for("index")})
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    return render_template("enroll.html")

def add_or_update_student_voice(student_id, voice_features):
    """Update student's voice data"""
    students_data = load_students()
    students = students_data.get("students", [])
    
    for student in students:
        if student.get("student_id") == student_id:
            student["voice_features"] = voice_features
            student["updated_at"] = datetime.utcnow().isoformat() + "Z"
            save_students(students_data)
            return True
    return False # Student not found

# sessions: simple in-memory active session token & created timestamp
current_session = {
    "token": None,
    "created_at": None,
}

def create_new_session():
    token = uuid.uuid4().hex
    current_session["token"] = token
    current_session["created_at"] = datetime.utcnow().isoformat() + "Z"
    return token

# Health / landing
@app.route("/")
def index():
    return render_template("index.html")

# Teacher login form
@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == TEACHER_PASSWORD:
            # set a cookie to mark teacher session (simple approach)
            resp = make_response(redirect(url_for("teacher_panel")))
            # cookie lasts for 2 hours
            resp.set_cookie("teacher_auth", "1", max_age=2*60*60, httponly=True)
            return resp
        else:
            flash("Wrong password", "danger")
            return redirect(url_for("teacher_login"))
    return render_template("teacher_login.html")

def teacher_required(fn):
    # simple decorator to check cookie
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.cookies.get("teacher_auth") == "1":
            return fn(*args, **kwargs)
        else:
            return redirect(url_for("teacher_login"))
    return wrapper

# Teacher panel: start session, rotate token, view/export
@app.route("/teacher")
@teacher_required
def teacher_panel():
    token = current_session.get("token")
    created_at = current_session.get("created_at")
    attendance = load_attendance()
    records = attendance.get("records", [])
    # show last 100 records (descending)
    last_records = list(reversed(records))[:100]
    # Build check-in URL (host aware)
    base = HOSTNAME if HOSTNAME else request.host_url.rstrip("/")
    checkin_url = f"{base}{url_for('checkin_session', token=token)}" if token else None
    return render_template(
        "teacher.html",
        token=token,
        created_at=created_at,
        checkin_url=checkin_url,
        recent=last_records,
        total=len(records),
    )

# Start a new session
@app.route("/teacher/start", methods=["POST"])
@teacher_required
def teacher_start():
    token = create_new_session()
    flash("New session started.", "success")
    return redirect(url_for("teacher_panel"))

# Rotate token
@app.route("/teacher/rotate", methods=["POST"])
@teacher_required
def teacher_rotate():
    token = create_new_session()
    flash("Session token rotated.", "success")
    return redirect(url_for("teacher_panel"))

# Export attendance to CSV
@app.route("/teacher/export")
@teacher_required
def teacher_export():
    attendance = load_attendance().get("records", [])
    si = BytesIO()
    writer = csv.writer(si)
    writer.writerow(["name", "student_id", "timestamp_utc", "session_id", "user_agent", "ip"])
    for r in attendance:
        writer.writerow([
            r.get("name"),
            r.get("student_id", ""),
            r.get("timestamp"),
            r.get("session_id"),
            r.get("user_agent", ""),
            r.get("ip", ""),
        ])
    si.seek(0)
    return send_file(
        si,
        as_attachment=True,
        download_name=f"attendance_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv",
        mimetype="text/csv",
    )

# QR code image for current session
@app.route("/session_qr.png")
@teacher_required
def session_qr():
    token = current_session.get("token")
    if not token:
        return "No active session", 404
    base = HOSTNAME if HOSTNAME else request.host_url.rstrip("/")
    checkin_url = f"{base}{url_for('checkin_session', token=token)}"
    img = qrcode.make(checkin_url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

# The student-facing check-in page (via scanning QR)
@app.route("/checkin/<token>", methods=["GET", "POST"])
def checkin_session(token):
    # show the check-in form on GET; handle submission on POST
    # validate token
    active = current_session.get("token")
    if token != active:
        # token invalid or expired
        return render_template("checkin.html", valid=False, token=token), 400

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        student_id = request.form.get("student_id", "").strip()
        face_verified = request.form.get("face_verified", "false") == "true"
        verification_data = request.form.get("verification_data", "")
        
        if not name:
            flash("Please enter your name.", "danger")
            return redirect(url_for("checkin_session", token=token))
        
        if not student_id:
            flash("Please enter your student ID.", "danger")
            return redirect(url_for("checkin_session", token=token))
        
        # Check if face verification is required and passed
        if not face_verified:
            flash("Face verification required. Please ensure your face is detected and verified.", "danger")
            return redirect(url_for("checkin_session", token=token))
            
        voice_verified = request.form.get("voice_verified", "false") == "true"
        
        entry = {
            "name": name,
            "student_id": student_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": token,
            "user_agent": request.headers.get("User-Agent", ""),
            "ip": request.remote_addr,
            "face_verified": face_verified,
            "voice_verified": voice_verified,
            "verification_data": verification_data
        }
        data = load_attendance()
        data.setdefault("records", []).append(entry)
        save_attendance(data)
        return render_template("success.html", entry=entry)
    # GET
    return render_template("checkin.html", valid=True, token=token)

# Simple API: add attendance via JSON (optionally used by mobile apps)
@app.route("/api/checkin", methods=["POST"])
def api_checkin():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid JSON"}), 400
    token = payload.get("session_id")
    name = (payload.get("name") or "").strip()
    student_id = (payload.get("student_id") or "").strip()
    if token != current_session.get("token"):
        return jsonify({"error": "Invalid session token"}), 400
    if not name:
        return jsonify({"error": "Missing name"}), 400
    entry = {
        "name": name,
        "student_id": student_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "session_id": token,
        "user_agent": request.headers.get("User-Agent", ""),
        "ip": request.remote_addr
    }
    data = load_attendance()
    data.setdefault("records", []).append(entry)
    save_attendance(data)
    return jsonify({"ok": True, "entry": entry}), 201


# API: Get face descriptor for a student
@app.route("/api/get_face_descriptor", methods=["GET"])
def api_get_face_descriptor():
    student_id = request.args.get("student_id", "").strip()
    
    if not student_id:
        return jsonify({"success": False, "error": "Missing student_id"}), 400
    
    student = get_student_by_id(student_id)
    
    if not student:
        return jsonify({"success": False, "error": "Student not found"}), 404
    
    return jsonify({
        "success": True,
        "descriptor": student.get("face_descriptor"),
        "name": student.get("name")
    })

# API: Enroll voice
@app.route("/api/enroll_voice", methods=["POST"])
def api_enroll_voice():
    student_id = request.form.get("student_id", "").strip()
    audio_file = request.files.get("audio")
    
    if not student_id or not audio_file:
        return jsonify({"success": False, "error": "Missing student_id or audio file"}), 400
        
    # Extract features
    features = voice_auth.extract_features(audio_file)
    if features is None:
        return jsonify({"success": False, "error": "Could not process audio"}), 400
        
    # Convert to list for storage
    features_list = voice_auth.features_to_list(features)
    
    # Save
    if add_or_update_student_voice(student_id, features_list):
        return jsonify({"success": True, "message": "Voice enrolled successfully"})
    else:
        return jsonify({"success": False, "error": "Student not found (enroll face first)"}), 404

# API: Verify voice (simplified - just check if enrolled)
@app.route("/api/verify_voice", methods=["POST"])
def api_verify_voice():
    student_id = request.form.get("student_id", "").strip()
    speech_verified = request.form.get("speech_verified", "false") == "true"
    
    if not student_id:
        return jsonify({"success": False, "error": "Missing student_id"}), 400
        
    student = get_student_by_id(student_id)
    if not student:
        return jsonify({"success": False, "error": "Student not found"}), 404
        
    stored_voice = student.get("voice_features")
    if not stored_voice:
        return jsonify({"success": False, "error": "Speech not enrolled for this student"}), 400
        
    # Simple verification - just check if speech was verified during enrollment
    is_verified = speech_verified and stored_voice.get("verified", False)
    
    return jsonify({
        "success": True,
        "verified": is_verified,
        "confidence": 100 if is_verified else 0,
        "distance": 0
    })

# Admin: clear attendance (dangerous - kept private behind teacher cookie)
@app.route("/teacher/clear", methods=["POST"])
@teacher_required
def teacher_clear():
    save_attendance({"records": []})
    flash("Attendance cleared.", "warning")
    return redirect(url_for("teacher_panel"))

# small utility: show raw JSON (teacher-only)
@app.route("/teacher/raw")
@teacher_required
def teacher_raw():
    return jsonify(load_attendance())

# run
if __name__ == "__main__":
    ensure_attendance_file()
    # create a default session on startup if none exists
    if not current_session.get("token"):
        create_new_session()
    # Run in debug mode on localhost by default
    app.run(host="0.0.0.0", port=5000, debug=True)
    
