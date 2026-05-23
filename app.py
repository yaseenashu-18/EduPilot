import os
import secrets
from urllib.parse import urlencode
import joblib
import pandas as pd
import numpy as np
import pymongo
from bson.objectid import ObjectId
from bson.errors import InvalidId
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# Import recommendation engine and ML helper tools
from ml.recommendation_engine import get_recommendations, generate_weekly_tasks
from ml.generate_data import generate_synthetic_data
from ml.train_model import train_models

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "edupilot_ai_secret_key_secure_and_premium")

# MongoDB connection setup using pymongo client
mongo_uri = os.getenv("MONGO_URI")
client = pymongo.MongoClient(mongo_uri)
try:
    db = client.get_default_database()
except Exception:
    db = client["malvision"]

CSV_PATH = "student_data.csv"

# Global ML model placeholders
risk_model = None
gpa_model = None


def mongo_to_dict(doc):
    """Convert a PyMongo document to a standard dict with string id for templates"""
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
    return doc


def mongo_to_list(cursor):
    """Convert a PyMongo cursor to a list of dicts with string id"""
    return [mongo_to_dict(doc) for doc in cursor]


def to_object_id(val):
    """Safely convert value to BSON ObjectId, returning None if invalid (e.g. SQLite integer IDs)"""
    if not val:
        return None
    try:
        return ObjectId(val)
    except (InvalidId, TypeError, ValueError):
        return None


def load_ml_models():
    """Load serialized scikit-learn models from disk with fallback rules on missing pkls"""
    global risk_model, gpa_model
    risk_path = os.path.join("models", "risk_model.pkl")
    gpa_path = os.path.join("models", "gpa_model.pkl")
    
    if os.path.exists(risk_path):
        try:
            risk_model = joblib.load(risk_path)
            print("Successfully loaded Risk Prediction Model.")
        except Exception as e:
            print(f"Error loading risk model: {e}")
            risk_model = None
    else:
        print("Risk prediction pkl not found. Fallback rules will be used.")
        risk_model = None
        
    if os.path.exists(gpa_path):
        try:
            gpa_model = joblib.load(gpa_path)
            print("Successfully loaded GPA Prediction Model.")
        except Exception as e:
            print(f"Error loading GPA model: {e}")
            gpa_model = None
    else:
        print("GPA prediction pkl not found. Fallback rules will be used.")
        gpa_model = None


# Load models on server boot
load_ml_models()


def send_reset_email(to_email, reset_link):
    """Send a password reset email using SMTP settings from the environment"""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not smtp_server or not smtp_email or not smtp_password:
        print("[SMTP CONFIG] SMTP settings are not fully configured in the environment. Falling back to sandbox.")
        return False, "SMTP settings are not fully configured in the environment."

    try:
        smtp_port = int(smtp_port) if smtp_port else 587
    except ValueError:
        smtp_port = 587
        
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "EduPilot AI - Password Recovery"
        msg["From"] = f"EduPilot AI <{smtp_email}>"
        msg["To"] = to_email
        
        # HTML body
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>EduPilot AI - Password Reset</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8fafc;
                    margin: 0;
                    padding: 0;
                    color: #1e293b;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -4px rgba(0,0,0,0.05);
                    border: 1px solid #e2e8f0;
                }}
                .header {{
                    background: linear-gradient(135deg, #4f46e5, #0ea5e9);
                    padding: 40px 20px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .header p {{
                    margin: 8px 0 0 0;
                    opacity: 0.9;
                    font-size: 15px;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .content p {{
                    font-size: 16px;
                    line-height: 1.6;
                    color: #475569;
                    margin-top: 0;
                    margin-bottom: 24px;
                }}
                .btn-container {{
                    text-align: center;
                    margin: 35px 0;
                }}
                .btn {{
                    display: inline-block;
                    background-color: #4f46e5;
                    color: #ffffff !important;
                    text-decoration: none;
                    padding: 14px 30px;
                    font-size: 16px;
                    font-weight: 600;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2), 0 2px 4px -1px rgba(79, 70, 229, 0.1);
                    transition: background-color 0.2s;
                }}
                .btn:hover {{
                    background-color: #4338ca;
                }}
                .footer {{
                    background-color: #f8fafc;
                    padding: 24px 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #94a3b8;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer a {{
                    color: #4f46e5;
                    text-decoration: none;
                }}
                .security-note {{
                    margin-top: 30px;
                    font-size: 13px;
                    color: #94a3b8;
                    border-top: 1px dashed #e2e8f0;
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>EduPilot AI</h1>
                    <p>Intellectual Learning & Performance Analytics</p>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>We received a request to recover the password for your EduPilot account. Click the button below to set a new password:</p>
                    
                    <div class="btn-container">
                        <a href="{reset_link}" class="btn" style="color: #ffffff !important;">Reset Password</a>
                    </div>
                    
                    <p>If the button above does not work, copy and paste the following link into your web browser:</p>
                    <p style="word-break: break-all; font-size: 14px; background-color: #f1f5f9; padding: 12px; border-radius: 6px; font-family: monospace;">
                        {reset_link}
                    </p>
                    
                    <div class="security-note">
                        <p><strong>Note:</strong> This link is valid for the next 60 minutes. If you did not request this recovery, you can safely ignore this email. Your password will remain unchanged.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2026 EduPilot AI. All rights reserved.</p>
                    <p>For support, contact <a href="mailto:{smtp_email}">{smtp_email}</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_content, "html"))
        
        # Connect to server
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, to_email, msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        print(f"[SMTP ERROR] Failed to send email via SMTP: {e}")
        return False, str(e)


# ----------------------------------------------------
# AUTHENTICATION ROUTES
# ----------------------------------------------------

@app.route("/")
def index():
    """Landing public homepage"""
    # If user already logged in, redirect to correct dashboard
    if "user_id" in session:
        role = session.get("role")
        if role == "student":
            return redirect(url_for("student_dashboard"))
        elif role == "teacher":
            return redirect(url_for("teacher_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
            
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Unified login for Student, Teacher, and Admin"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")  # student, teacher, admin
        
        # Allow administrative bypass for admin@edupilot.com
        if role == "admin" and email == "admin@edupilot.com":
            pass
        # Enforce @paruluniversity.ac.in domain validation for other logins
        elif role in ["student", "teacher", "admin"] and not (email.endswith("@paruluniversity.ac.in") or email in ["yaseenashu0108@gmail.com", "yaseenashu18@gmail.com"]):
            flash("Access restricted to @paruluniversity.ac.in domain users only.", "error")
            return render_template("login.html")
            
        user = None
        if role == "student":
            user = db.students.find_one({"email": email})
        elif role == "teacher":
            user = db.teachers.find_one({"email": email})
        elif role == "admin":
            user = db.admins.find_one({"email": email})
            
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["role"] = role
            session["name"] = user["name"]
            session["email"] = user["email"]
            if role != "admin":
                session["department"] = user["department"]
            
            flash(f"Successfully logged in as {user['name']}!", "success")
            
            if role == "student":
                return redirect(url_for("student_dashboard"))
            elif role == "teacher":
                return redirect(url_for("teacher_dashboard"))
            elif role == "admin":
                return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid email or password credentials. Please try again.", "error")
            
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Student Registration Route"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        department = request.form.get("department")
        semester = int(request.form.get("semester"))
        career_goal = request.form.get("career_goal")
        
        # Enforce @paruluniversity.ac.in domain validation for registration
        if not (email.endswith("@paruluniversity.ac.in") or email in ["yaseenashu0108@gmail.com", "yaseenashu18@gmail.com"]):
            flash("Registration is restricted to @paruluniversity.ac.in domain users only.", "error")
            return render_template("register.html")
            
        # Verify if student already registered
        if db.students.find_one({"email": email}):
            flash("Email already registered! Please sign in.", "error")
            return redirect(url_for("login"))
            
        hashed_pwd = generate_password_hash(password)
        
        try:
            # Base defaults for registrations: attendance 80.0, cgpa 7.0, coding 50, assignment 60
            res = db.students.insert_one({
                "name": name,
                "email": email,
                "password": hashed_pwd,
                "department": department,
                "semester": semester,
                "cgpa": 7.0,
                "attendance": 80.0,
                "coding_score": 50,
                "assignment_score": 60,
                "career_goal": career_goal
            })
            
            student_id = res.inserted_id
            
            # Seed 5 basic subjects for student performance evaluation
            subjects = [
                {"student_id": student_id, "subject_name": "Data Structures & Algorithms", "marks": 70},
                {"student_id": student_id, "subject_name": "Database Management Systems", "marks": 68},
                {"student_id": student_id, "subject_name": "Operating Systems", "marks": 75},
                {"student_id": student_id, "subject_name": "Computer Networks", "marks": 62},
                {"student_id": student_id, "subject_name": "Mathematics", "marks": 65}
            ]
            db.subjects.insert_many(subjects)
                
            # Create default weekly tasks
            default_tasks = generate_weekly_tasks(str(student_id), 7.0, 80.0, 50, "Low Risk", career_goal, [])
            task_docs = []
            for task in default_tasks:
                task_docs.append({
                    "student_id": student_id,
                    "task_title": task["task_title"],
                    "status": task["status"],
                    "due_date": task["due_date"]
                })
            if task_docs:
                db.tasks.insert_many(task_docs)
                
            # Create a base prediction record
            db.predictions.insert_one({
                "student_id": student_id,
                "predicted_gpa": 7.15,
                "risk_level": "Low Risk",
                "placement_score": 58.0
            })
            
            flash("Account registered successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error during registration: {e}", "error")
            
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Clear session data and redirect"""
    session.clear()
    flash("Successfully logged out.", "success")
    return redirect(url_for("index"))


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Request a password reset link"""
    if "user_id" in session:
        role = session.get("role")
        if role == "student":
            return redirect(url_for("student_dashboard"))
        elif role == "teacher":
            return redirect(url_for("teacher_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
            
    reset_link = None
    if request.method == "POST":
        email = request.form.get("email")
        
        # 1. Search across collections
        student = db.students.find_one({"email": email})
        teacher = db.teachers.find_one({"email": email})
        admin = db.admins.find_one({"email": email})
        
        user_coll = None
        user_doc = None
        
        if student:
            user_coll = db.students
            user_doc = student
        elif teacher:
            user_coll = db.teachers
            user_doc = teacher
        elif admin:
            user_coll = db.admins
            user_doc = admin
            
        if user_doc and user_coll is not None:
            # Generate secure reset token
            token = secrets.token_urlsafe(32)
            import datetime
            # Expiry set to 1 hour from now
            expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            
            user_coll.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {
                    "reset_token": token,
                    "reset_token_expiry": expiry
                }}
            )
            
            # Construct reset URL using request host
            host_url = request.host_url.rstrip("/")
            if "127.0.0.1" in host_url:
                host_url = host_url.replace("127.0.0.1", "localhost")
                
            reset_link = f"{host_url}/reset_password/{token}"
            print(f"\n[PASSWORD RESET SIMULATION] Click to reset password for {email}: {reset_link}\n")
            
            # Attempt real SMTP mail sending
            mail_success, mail_error = send_reset_email(email, reset_link)
            if mail_success:
                flash(f"A password reset link has been successfully sent to {email}.", "success")
                # Hide developer sandbox card since email was successfully delivered
                reset_link = None
            else:
                # If mail sending failed, flash a warning/info and fallback to the simulation sandbox
                if os.getenv("SMTP_EMAIL") and os.getenv("SMTP_EMAIL") != "your-project-email@gmail.com":
                    flash(f"Failed to send email via SMTP ({mail_error}). Falling back to Developer Sandbox simulation.", "warning")
                else:
                    flash("SMTP email credentials are not configured in your .env file. Falling back to Developer Sandbox simulation.", "info")
        else:
            flash("No active account found with that email address. Please double check.", "error")
            
    return render_template("forgot_password.html", reset_link=reset_link)


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Reset account password using valid token"""
    if "user_id" in session:
        session.clear()
        
    import datetime
    
    # 1. Search for user with matching token in MongoDB collections
    student = db.students.find_one({"reset_token": token})
    teacher = db.teachers.find_one({"reset_token": token})
    admin = db.admins.find_one({"reset_token": token})
    
    user_coll = None
    user_doc = None
    
    if student:
        user_coll = db.students
        user_doc = student
    elif teacher:
        user_coll = db.teachers
        user_doc = teacher
    elif admin:
        user_coll = db.admins
        user_doc = admin
        
    if not user_doc or user_coll is None:
        flash("The password reset link is invalid or has already been used.", "error")
        return redirect(url_for("forgot_password"))
        
    # 2. Check token expiration
    expiry = user_doc.get("reset_token_expiry")
    if not expiry:
        flash("The password reset link is invalid.", "error")
        return redirect(url_for("forgot_password"))
        
    now = datetime.datetime.utcnow()
    if expiry < now:
        # Clean up expired token
        user_coll.update_one(
            {"_id": user_doc["_id"]},
            {"$unset": {"reset_token": "", "reset_token_expiry": ""}}
        )
        flash("Your password reset link has expired. Please request a new one.", "error")
        return redirect(url_for("forgot_password"))
        
    if request.method == "POST":
        password = request.form.get("password")
        
        # Hash new password
        hashed_password = generate_password_hash(password)
        
        # Update user password and clear reset token fields
        user_coll.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"password": hashed_password},
             "$unset": {"reset_token": "", "reset_token_expiry": ""}}
        )
        
        flash("Your password has been reset successfully! You can now sign in.", "success")
        return redirect(url_for("login"))
        
    return render_template("reset_password.html", token=token)


# ----------------------------------------------------
# GOOGLE OAUTH 2.0 FLOW ROUTES
# ----------------------------------------------------

@app.route("/login/google")
def login_google():
    """Initiate Google OAuth 2.0 flow"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        redirect_uri = url_for("login_google_callback", _external=True)
    
    # Generate random state to protect against CSRF
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account"
    }
    
    authorization_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return redirect(authorization_url)


@app.route("/login/google/callback")
def login_google_callback():
    """Handle Google OAuth 2.0 callback and enforce domain/auto-registration"""
    # 1. Verify CSRF state
    request_state = request.args.get("state")
    session_state = session.pop("oauth_state", None)
    
    if not request_state or request_state != session_state:
        flash("Authentication failed: session state mismatch.", "error")
        return redirect(url_for("login"))
        
    code = request.args.get("code")
    if not code:
        flash("Authentication failed: authorization code not returned.", "error")
        return redirect(url_for("login"))
        
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        redirect_uri = url_for("login_google_callback", _external=True)
    
    # 2. Exchange code for Access Token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        token_response = requests.post(token_url, data=data, timeout=10)
        token_data = token_response.json()
        
        if "error" in token_data:
            flash(f"OAuth token exchange error: {token_data.get('error_description', 'unknown error')}", "error")
            return redirect(url_for("login"))
            
        access_token = token_data.get("access_token")
        
        # 3. Fetch user profile from UserInfo Endpoint
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = requests.get(userinfo_url, headers=headers, timeout=10)
        user_info = userinfo_response.json()
        
        email = user_info.get("email")
        name = user_info.get("name", "Parul Student")
        
        if not email:
            flash("Unable to retrieve email from Google login.", "error")
            return redirect(url_for("login"))
            
        # 4. Enforce @paruluniversity.ac.in domain validation (except admin system bypass)
        if email != "admin@edupilot.com" and email not in ["yaseenashu0108@gmail.com", "yaseenashu18@gmail.com"] and not email.endswith("@paruluniversity.ac.in"):
            flash("Access restricted to @paruluniversity.ac.in domain users only.", "error")
            return redirect(url_for("login"))
            
        # 5. Check if user already exists in students, teachers or admins
        student = mongo_to_dict(db.students.find_one({"email": email}))
        teacher = mongo_to_dict(db.teachers.find_one({"email": email}))
        admin = mongo_to_dict(db.admins.find_one({"email": email}))
        
        if student:
            session["user_id"] = student["id"]
            session["role"] = "student"
            session["name"] = student["name"]
            session["email"] = student["email"]
            session["department"] = student["department"]
            flash(f"Successfully logged in as {student['name']} via Google!", "success")
            return redirect(url_for("student_dashboard"))
            
        elif teacher:
            session["user_id"] = teacher["id"]
            session["role"] = "teacher"
            session["name"] = teacher["name"]
            session["email"] = teacher["email"]
            session["department"] = teacher["department"]
            flash(f"Successfully logged in as {teacher['name']} via Google!", "success")
            return redirect(url_for("teacher_dashboard"))
            
        elif admin:
            session["user_id"] = admin["id"]
            session["role"] = "admin"
            session["name"] = admin["name"]
            session["email"] = admin["email"]
            flash(f"Successfully logged in as Admin via Google!", "success")
            return redirect(url_for("admin_dashboard"))
            
        else:
            # First-time user: Auto-register with premium student defaults!
            hashed_pwd = generate_password_hash(secrets.token_urlsafe(16))
            
            res = db.students.insert_one({
                "name": name,
                "email": email,
                "password": hashed_pwd,
                "department": "Computer Science",  # default
                "semester": 1,                      # default
                "cgpa": 7.0,
                "attendance": 80.0,
                "coding_score": 50,
                "assignment_score": 60,
                "career_goal": "Software Developer"  # default
            })
            
            student_id = res.inserted_id
            
            # Seed 5 basic subjects for student performance evaluation
            subjects = [
                {"student_id": student_id, "subject_name": "Data Structures & Algorithms", "marks": 70},
                {"student_id": student_id, "subject_name": "Database Management Systems", "marks": 68},
                {"student_id": student_id, "subject_name": "Operating Systems", "marks": 75},
                {"student_id": student_id, "subject_name": "Computer Networks", "marks": 62},
                {"student_id": student_id, "subject_name": "Mathematics", "marks": 65}
            ]
            db.subjects.insert_many(subjects)
                
            # Create default weekly tasks
            default_tasks = generate_weekly_tasks(str(student_id), 7.0, 80.0, 50, "Low Risk", "Software Developer", [])
            task_docs = []
            for task in default_tasks:
                task_docs.append({
                    "student_id": student_id,
                    "task_title": task["task_title"],
                    "status": task["status"],
                    "due_date": task["due_date"]
                })
            if task_docs:
                db.tasks.insert_many(task_docs)
                
            # Create a base prediction record
            db.predictions.insert_one({
                "student_id": student_id,
                "predicted_gpa": 7.15,
                "risk_level": "Low Risk",
                "placement_score": 58.0
            })
            
            # Fetch the newly registered student
            student = mongo_to_dict(db.students.find_one({"_id": student_id}))
            
            # Establish Session
            session["user_id"] = student["id"]
            session["role"] = "student"
            session["name"] = student["name"]
            session["email"] = student["email"]
            session["department"] = student["department"]
            
            flash(f"Welcome to EduPilot! Your student profile has been auto-registered.", "success")
            return redirect(url_for("student_dashboard"))
            
    except Exception as e:
        flash(f"Google Sign-In failed: {str(e)}", "error")
        return redirect(url_for("login"))


# ----------------------------------------------------
# STUDENT FEATURES & DASHBOARD
# ----------------------------------------------------

@app.route("/student/dashboard")
def student_dashboard():
    """Main student dashboard view with live ML prediction triggers"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    student_id = session["user_id"]
    oid = to_object_id(student_id)
    if not oid:
        session.clear()
        flash("Your session is invalid or has expired. Please log in again.", "error")
        return redirect(url_for("login"))
        
    student = mongo_to_dict(db.students.find_one({"_id": oid}))
    
    if not student:
        session.clear()
        flash("Student profile not found.", "error")
        return redirect(url_for("login"))
        
    # Fetch Subjects and calculate weak areas (< 60)
    subjects = mongo_to_list(db.subjects.find({"student_id": oid}))
    
    weak_subjects = []
    marks_labels = []
    marks_values = []
    for sub in subjects:
        marks_labels.append(sub["subject_name"])
        marks_values.append(sub["marks"])
        if sub["marks"] < 60:
            weak_subjects.append(sub["subject_name"])
            
    # Predict Academic Risk and GPA using ML models
    attendance = student["attendance"]
    cgpa = student["cgpa"]
    coding_score = student["coding_score"]
    assignment_score = student["assignment_score"]
    career_goal = student["career_goal"]
    
    # Analytical calculations for placement readiness
    placement_score = float(np.clip(
        coding_score * 0.45 + cgpa * 3.5 + assignment_score * 0.10 + attendance * 0.10, 
        0.0, 100.0
    ))
    
    # ML Risk Prediction
    risk_level = "Low Risk"
    if risk_model:
        try:
            pred = risk_model.predict([[attendance, cgpa, coding_score, assignment_score]])
            risk_level = pred[0]
        except Exception as e:
            print(f"Error running ML inference: {e}")
    else:
        # Fallback heuristic
        if attendance < 60 or cgpa < 5.0 or (cgpa < 5.5 and assignment_score < 50):
            risk_level = "High Risk"
        elif attendance < 75 or cgpa < 6.5 or coding_score < 45 or assignment_score < 55:
            risk_level = "Medium Risk"
            
    # ML GPA Prediction
    predicted_gpa = cgpa + 0.15
    if gpa_model:
        try:
            pred = gpa_model.predict([[attendance, assignment_score, coding_score]])
            predicted_gpa = float(np.clip(pred[0], 2.0, 10.0))
        except Exception as e:
            print(f"Error running GPA ML inference: {e}")
    else:
        # Fallback heuristic
        gpa_shift = (coding_score + assignment_score + attendance) / 300.0 - 0.5
        predicted_gpa = float(np.clip(cgpa + gpa_shift * 0.35, 2.0, 10.0))
        
    # Update predictions table cache
    pred_record = db.predictions.find_one({"student_id": oid})
    if pred_record:
        db.predictions.update_one(
            {"student_id": oid},
            {"$set": {
                "predicted_gpa": predicted_gpa,
                "risk_level": risk_level,
                "placement_score": placement_score
            }}
        )
    else:
        db.predictions.insert_one({
            "student_id": oid,
            "predicted_gpa": predicted_gpa,
            "risk_level": risk_level,
            "placement_score": placement_score
        })
        
    # Fetch Weekly Tasks sorted by _id descending
    tasks = mongo_to_list(db.tasks.find({"student_id": oid}).sort("_id", -1))
    
    # Fetch top recommendation
    recs = get_recommendations(cgpa, attendance, coding_score, assignment_score, career_goal)
    career_recs = recs["career_recommendations"]
    
    return render_template(
        "student_dashboard.html",
        student=student,
        active_page="dashboard",
        weak_subjects=weak_subjects,
        placement_score=placement_score,
        risk_level=risk_level,
        predicted_gpa=predicted_gpa,
        tasks=tasks,
        career_recs=career_recs,
        marks_labels=marks_labels,
        marks_values=marks_values
    )


@app.route("/student/recommendations")
def student_recommendations():
    """Dedicated Student AI Learning Path Page"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    student_id = session["user_id"]
    oid = to_object_id(student_id)
    if not oid:
        session.clear()
        return redirect(url_for("login"))
        
    student = mongo_to_dict(db.students.find_one({"_id": oid}))
    if not student:
        session.clear()
        return redirect(url_for("login"))
        
    recs = get_recommendations(
        student["cgpa"], 
        student["attendance"], 
        student["coding_score"], 
        student["assignment_score"], 
        student["career_goal"]
    )
    
    return render_template(
        "recommendations.html",
        student=student,
        active_page="recommendations",
        recommendations=recs
    )


@app.route("/student/analytics")
def student_analytics():
    """Detailed Student Analytics Page"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    student_id = session["user_id"]
    oid = to_object_id(student_id)
    if not oid:
        session.clear()
        return redirect(url_for("login"))
        
    student = mongo_to_dict(db.students.find_one({"_id": oid}))
    if not student:
        session.clear()
        return redirect(url_for("login"))
        
    subjects = mongo_to_list(db.subjects.find({"student_id": oid}))
    pred = mongo_to_dict(db.predictions.find_one({"student_id": oid}))
    
    marks_labels = [s["subject_name"] for s in subjects]
    marks_values = [s["marks"] for s in subjects]
    
    placement_score = pred["placement_score"] if pred else 60.0
    predicted_gpa = pred["predicted_gpa"] if pred else student["cgpa"]
    
    return render_template(
        "analytics.html",
        student=student,
        active_page="analytics",
        marks_labels=marks_labels,
        marks_values=marks_values,
        subjects_marks=[(s["subject_name"], s["marks"]) for s in subjects],
        placement_score=placement_score,
        predicted_gpa=predicted_gpa
    )


@app.route("/student/tasks/toggle/<task_id>")
def toggle_task(task_id):
    """Toggle weekly checklist task status between Completed and Pending"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    student_id = session["user_id"]
    s_oid = to_object_id(student_id)
    t_oid = to_object_id(task_id)
    
    if not s_oid or not t_oid:
        return redirect(url_for("student_dashboard"))
        
    task = db.tasks.find_one({"_id": t_oid, "student_id": s_oid})
    
    if task:
        new_status = "Pending" if task["status"] == "Completed" else "Completed"
        db.tasks.update_one({"_id": t_oid}, {"$set": {"status": new_status}})
        
    return redirect(url_for("student_dashboard"))


@app.route("/student/tasks/regenerate")
def regenerate_tasks():
    """Regenerate tasks based on active weak subjects, career track, and risk parameters"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    student_id = session["user_id"]
    oid = to_object_id(student_id)
    if not oid:
        session.clear()
        return redirect(url_for("login"))
        
    student = db.students.find_one({"_id": oid})
    if not student:
        session.clear()
        return redirect(url_for("login"))
        
    pred_row = db.predictions.find_one({"student_id": oid})
    risk = pred_row["risk_level"] if pred_row else "Low Risk"
    
    weak_rows = db.subjects.find({"student_id": oid, "marks": {"$lt": 60}})
    weak_subjs = [r["subject_name"] for r in weak_rows]
    
    # Delete current tasks
    db.tasks.delete_many({"student_id": oid})
    
    # Generate new weekly tasks
    new_tasks = generate_weekly_tasks(
        str(oid), 
        student["cgpa"], 
        student["attendance"], 
        student["coding_score"], 
        risk, 
        student["career_goal"], 
        weak_subjs
    )
    
    task_docs = []
    for t in new_tasks:
        task_docs.append({
            "student_id": oid,
            "task_title": t["task_title"],
            "status": t["status"],
            "due_date": t["due_date"]
        })
    if task_docs:
        db.tasks.insert_many(task_docs)
        
    flash("Weekly tasks regenerated based on AI parameters!", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/student/career/update", methods=["POST"])
def update_career_goal():
    """Update student career goal selection dynamically"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    career_goal = request.form.get("career_goal")
    student_id = session["user_id"]
    oid = to_object_id(student_id)
    if not oid:
        session.clear()
        return redirect(url_for("login"))
        
    db.students.update_one({"_id": oid}, {"$set": {"career_goal": career_goal}})
    
    flash(f"Career focus successfully switched to {career_goal}!", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    """Edit Profile Settings Page for Students and Teachers"""
    if "user_id" not in session or session.get("role") not in ["student", "teacher"]:
        flash("Please log in to edit your profile.", "error")
        return redirect(url_for("login"))
        
    user_id = session["user_id"]
    oid = to_object_id(user_id)
    if not oid:
        session.clear()
        flash("Your session is invalid or has expired. Please log in again.", "error")
        return redirect(url_for("login"))
        
    role = session["role"]
    
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        department = request.form.get("department")
        
        if role == "student":
            semester = int(request.form.get("semester"))
            career_goal = request.form.get("career_goal")
            
            update_data = {
                "name": name,
                "department": department,
                "semester": semester,
                "career_goal": career_goal
            }
            if password:  # if new password is provided, hash and save it
                update_data["password"] = generate_password_hash(password)
                
            db.students.update_one({"_id": oid}, {"$set": update_data})
                
            # Update active Flask session variables
            session["name"] = name
            session["department"] = department
            
            flash("Your student profile has been successfully updated!", "success")
            return redirect(url_for("student_dashboard"))
            
        elif role == "teacher":
            update_data = {
                "name": name,
                "department": department
            }
            if password:  # if new password is provided, hash and save it
                update_data["password"] = generate_password_hash(password)
                
            db.teachers.update_one({"_id": oid}, {"$set": update_data})
                
            # Update active Flask session variables
            session["name"] = name
            session["department"] = department
            
            flash("Your faculty profile has been successfully updated!", "success")
            return redirect(url_for("teacher_dashboard"))
            
    # GET request
    if role == "student":
        user = mongo_to_dict(db.students.find_one({"_id": oid}))
    else:
        user = mongo_to_dict(db.teachers.find_one({"_id": oid}))
        
    if not user:
        session.clear()
        flash("Your profile was not found.", "error")
        return redirect(url_for("login"))
        
    return render_template("edit_profile.html", user=user)


# ----------------------------------------------------
# TEACHER FEATURES & DASHBOARD
# ----------------------------------------------------

@app.route("/teacher/dashboard")
def teacher_dashboard():
    """Teacher Supervision Dashboard"""
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))
        
    dept = session.get("department")
    
    # Fetch Students in department
    students = mongo_to_list(db.students.find({"department": dept}).sort("name", 1))
    
    # Enrich student documents with cached predictive statistics
    for s in students:
        s_oid = to_object_id(s["id"])
        pred = db.predictions.find_one({"student_id": s_oid}) if s_oid else None
        if pred:
            s["risk_level"] = pred.get("risk_level")
            s["predicted_gpa"] = pred.get("predicted_gpa")
            s["placement_score"] = pred.get("placement_score")
        else:
            s["risk_level"] = "Low Risk"
            s["predicted_gpa"] = s["cgpa"]
            s["placement_score"] = 60.0
            
    # Compute Statistics Averages
    total_students = len(students)
    high_risk_count = 0
    med_risk_count = 0
    low_risk_count = 0
    cgpa_sum = 0
    attendance_sum = 0
    
    for s in students:
        cgpa_sum += s["cgpa"]
        attendance_sum += s["attendance"]
        
        risk = s.get("risk_level") or "Low Risk"
        if risk == "High Risk":
            high_risk_count += 1
        elif risk == "Medium Risk":
            med_risk_count += 1
        else:
            low_risk_count += 1
            
    avg_cgpa = cgpa_sum / total_students if total_students > 0 else 0
    avg_attendance = attendance_sum / total_students if total_students > 0 else 0
    
    stats = {
        "total_students": total_students,
        "high_risk": high_risk_count,
        "med_risk": med_risk_count,
        "low_risk": low_risk_count,
        "avg_cgpa": avg_cgpa,
        "avg_attendance": avg_attendance
    }
    
    return render_template(
        "teacher_dashboard.html",
        active_page="dashboard",
        department=dept,
        students=students,
        stats=stats
    )


@app.route("/teacher/analytics")
def teacher_analytics():
    """Teacher Detailed Analytics View"""
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))
        
    dept = session.get("department")
    students = mongo_to_list(db.students.find({"department": dept}))
    
    # Calculate attendance distribution ranges:
    # 0: < 60%, 1: 60-75%, 2: 75-90%, 3: 90-100%
    att_ranges = [0, 0, 0, 0]
    high_r, med_r, low_r = 0, 0, 0
    for s in students:
        att = s["attendance"]
        if att < 60:
            att_ranges[0] += 1
        elif att < 75:
            att_ranges[1] += 1
        elif att < 90:
            att_ranges[2] += 1
        else:
            att_ranges[3] += 1
            
        s_oid = to_object_id(s["id"])
        pred = db.predictions.find_one({"student_id": s_oid}) if s_oid else None
        risk = pred.get("risk_level") if pred else "Low Risk"
        if risk == "High Risk":
            high_r += 1
        elif risk == "Medium Risk":
            med_r += 1
        else:
            low_r += 1
            
    stats = {
        "low_risk": low_r,
        "med_risk": med_r,
        "high_risk": high_r
    }
    
    return render_template(
        "analytics.html",
        active_page="analytics",
        attendance_distribution=att_ranges,
        stats=stats
    )


# ----------------------------------------------------
# ADMIN CONSOLE & ACTIONS
# ----------------------------------------------------

@app.route("/admin/dashboard")
def admin_dashboard():
    """Global system administrator console panel"""
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
        
    students_count = db.students.count_documents({})
    teachers_count = db.teachers.count_documents({})
    
    # Read active teachers list
    teachers = mongo_to_list(db.teachers.find().sort("_id", -1))
    
    # Read dataset size
    csv_rows = 0
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            csv_rows = len(df)
        except Exception:
            csv_rows = 0
            
    stats = {
        "students_count": students_count,
        "teachers_count": teachers_count,
        "csv_rows": csv_rows
    }
    
    return render_template(
        "admin_dashboard.html",
        active_page="dashboard",
        stats=stats,
        teachers=teachers
    )


@app.route("/admin/analytics")
def admin_analytics():
    """Global admin system-wide analytics"""
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
        
    students = mongo_to_list(db.students.find())
    
    att_ranges = [0, 0, 0, 0]
    cgpa_sum, att_sum = 0, 0
    total = len(students)
    for s in students:
        att = s["attendance"]
        cgpa_sum += s["cgpa"]
        att_sum += att
        if att < 60:
            att_ranges[0] += 1
        elif att < 75:
            att_ranges[1] += 1
        elif att < 90:
            att_ranges[2] += 1
        else:
            att_ranges[3] += 1
            
    low = db.predictions.count_documents({"risk_level": "Low Risk"})
    med = db.predictions.count_documents({"risk_level": "Medium Risk"})
    high = db.predictions.count_documents({"risk_level": "High Risk"})
    
    stats = {
        "low_risk": low,
        "med_risk": med,
        "high_risk": high,
        "avg_cgpa": cgpa_sum / total if total > 0 else 0,
        "avg_attendance": att_sum / total if total > 0 else 0
    }
    
    return render_template(
        "analytics.html",
        active_page="analytics",
        attendance_distribution=att_ranges,
        stats=stats
    )


@app.route("/admin/teacher/add", methods=["POST"])
def admin_add_teacher():
    """Add a new professor/teacher supervised account"""
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
        
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    department = request.form.get("department")
    
    # Enforce @paruluniversity.ac.in domain validation for teachers
    if not email.endswith("@paruluniversity.ac.in"):
        flash("Professor registration is restricted to @paruluniversity.ac.in domain users only.", "error")
        return redirect(url_for("admin_dashboard"))
        
    if db.teachers.find_one({"email": email}):
        flash("Professor email already registered!", "error")
        return redirect(url_for("admin_dashboard"))
        
    hashed_pwd = generate_password_hash(password)
    try:
        db.teachers.insert_one({
            "name": name,
            "email": email,
            "password": hashed_pwd,
            "department": department
        })
        flash(f"Professor {name} successfully added to the system database!", "success")
    except Exception as e:
        flash(f"Error registering professor: {e}", "error")
    
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/teacher/delete/<teacher_id>")
def admin_delete_teacher(teacher_id):
    """Remove a faculty account"""
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
        
    oid = to_object_id(teacher_id)
    if oid:
        db.teachers.delete_one({"_id": oid})
    
    flash("Faculty account removed from platform database.", "success")
    return redirect(url_for("admin_dashboard"))


# ----------------------------------------------------
# ADMIN ML & DATA GENERATION TRIGGERS
# ----------------------------------------------------

@app.route("/admin/action/generate_data")
def admin_generate_data():
    """Trigger generation of synthetic data (5k students)"""
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
        
    try:
        generate_synthetic_data(CSV_PATH, 5000)
        flash("Successfully generated synthetic student dataset (5,000 records)!", "success")
    except Exception as e:
        flash(f"Error during synthetic generation: {e}", "error")
        
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/action/train_models")
def admin_train_models():
    """Trigger scikit-learn ML training routines and reload pkls"""
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
        
    try:
        if not os.path.exists(CSV_PATH):
            # Generate automatically if missing
            generate_synthetic_data(CSV_PATH, 1000)
            
        train_models(CSV_PATH, "models")
        # Reload models in Flask thread
        load_ml_models()
        flash("Models trained successfully! Refreshed serialized parameters.", "success")
    except Exception as e:
        flash(f"Error training models: {e}", "error")
        
    return redirect(url_for("admin_dashboard"))


# ----------------------------------------------------
# PDF / PRINTABLE STUDENT REPORT DOWNLOAD
# ----------------------------------------------------

@app.route("/download_report/<student_id>")
def download_report(student_id):
    """Generate printable layout summary of student profile"""
    if "user_id" not in session or session.get("role") not in ["teacher", "admin"]:
        return "Unauthorized Access Profile", 403
        
    oid = to_object_id(student_id)
    if not oid:
        return "Invalid student identifier format", 400
        
    student = mongo_to_dict(db.students.find_one({"_id": oid}))
    
    if not student:
        return "Student record not found", 404
        
    subjects = mongo_to_list(db.subjects.find({"student_id": oid}))
    pred = mongo_to_dict(db.predictions.find_one({"student_id": oid}))
    
    # Render direct report layout
    return render_template(
        "report_template.html",
        student=student,
        subjects=subjects,
        pred=pred
    )


# ----------------------------------------------------
# DATABASE INITIALIZER ROUTINE
# ----------------------------------------------------
def startup_checks():
    """Assures MongoDB Atlas connection is verified and seeded if empty"""
    try:
        db.client.admin.command('ping')
        print("Successfully verified connection to MongoDB Atlas!")
        
        # If the database is completely unseeded, trigger seeding script
        if db.students.count_documents({}) == 0:
            print("MongoDB is currently empty. Triggering setup seeder...")
            from database.mongo_setup import setup_mongo
            setup_mongo()
    except Exception as e:
        print(f"MongoDB connection check failed: {e}")


startup_checks()

if __name__ == "__main__":
    # Bind to 0.0.0.0 to support both IPv4 and IPv6 localhost resolution in port forwarding tunnels.
    # Default to port 5000 to match authorized Google OAuth redirect URIs.
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
