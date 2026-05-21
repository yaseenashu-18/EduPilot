import os
import sqlite3
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# Import recommendation engine and ML helper tools
from ml.recommendation_engine import get_recommendations, generate_weekly_tasks
from ml.generate_data import generate_synthetic_data
from ml.train_model import train_models

app = Flask(__name__)
app.secret_key = "edupilot_ai_secret_key_secure_and_premium"

DB_PATH = os.path.join("database", "database.db")
CSV_PATH = "student_data.csv"

# Global ML model placeholders
risk_model = None
gpa_model = None

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


def get_db_connection():
    """Establish connection to SQLite database with dictionary rows"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user = None
        if role == "student":
            cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
            user = cursor.fetchone()
        elif role == "teacher":
            cursor.execute("SELECT * FROM teachers WHERE email = ?", (email,))
            user = cursor.fetchone()
        elif role == "admin":
            cursor.execute("SELECT * FROM admins WHERE email = ?", (email,))
            user = cursor.fetchone()
            
        conn.close()
        
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify if student already registered
        cursor.execute("SELECT id FROM students WHERE email = ?", (email,))
        if cursor.fetchone():
            flash("Email already registered! Please sign in.", "error")
            conn.close()
            return redirect(url_for("login"))
            
        hashed_pwd = generate_password_hash(password)
        
        # Base defaults for registrations: attendance 80.0, cgpa 7.0, coding 50, assignment 60
        try:
            cursor.execute("""
            INSERT INTO students (name, email, password, department, semester, cgpa, attendance, coding_score, assignment_score, career_goal)
            VALUES (?, ?, ?, ?, ?, 7.0, 80.0, 50, 60, ?)
            """, (name, email, hashed_pwd, department, semester, career_goal))
            
            student_id = cursor.lastrowid
            
            # Seed 5 basic subjects for student performance evaluation
            subjects = [
                ("Data Structures & Algorithms", 70),
                ("Database Management Systems", 68),
                ("Operating Systems", 75),
                ("Computer Networks", 62),
                ("Mathematics", 65)
            ]
            for s_name, m in subjects:
                cursor.execute("INSERT INTO subjects (student_id, subject_name, marks) VALUES (?, ?, ?)", (student_id, s_name, m))
                
            # Create default weekly tasks
            default_tasks = generate_weekly_tasks(student_id, 7.0, 80.0, 50, "Low Risk", career_goal, [])
            for task in default_tasks:
                cursor.execute("""
                INSERT INTO tasks (student_id, task_title, status, due_date)
                VALUES (?, ?, ?, ?)
                """, (student_id, task["task_title"], task["status"], task["due_date"]))
                
            # Create a base prediction record
            cursor.execute("""
            INSERT INTO predictions (student_id, predicted_gpa, risk_level, placement_score)
            VALUES (?, 7.15, 'Low Risk', 58.0)
            """, (student_id,))
            
            conn.commit()
            flash("Account registered successfully! Please log in.", "success")
            conn.close()
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error during registration: {e}", "error")
            conn.close()
            
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Clear session data and redirect"""
    session.clear()
    flash("Successfully logged out.", "success")
    return redirect(url_for("index"))


# ----------------------------------------------------
# STUDENT FEATURES & DASHBOARD
# ----------------------------------------------------

@app.route("/student/dashboard")
def student_dashboard():
    """Main student dashboard view with live ML prediction triggers"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    student_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch Student Info
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    
    # 2. Fetch Subjects and calculate weak areas (< 60)
    cursor.execute("SELECT * FROM subjects WHERE student_id = ?", (student_id,))
    subjects = cursor.fetchall()
    
    weak_subjects = []
    marks_labels = []
    marks_values = []
    for sub in subjects:
        marks_labels.append(sub["subject_name"])
        marks_values.append(sub["marks"])
        if sub["marks"] < 60:
            weak_subjects.append(sub["subject_name"])
            
    # 3. Predict Academic Risk and GPA using ML models
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
            print(f"Error runs ML inference: {e}")
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
            print(f"Error runs GPA ML inference: {e}")
    else:
        # Fallback heuristic
        gpa_shift = (coding_score + assignment_score + attendance) / 300.0 - 0.5
        predicted_gpa = float(np.clip(cgpa + gpa_shift * 0.35, 2.0, 10.0))
        
    # Update predictions table cache
    cursor.execute("SELECT id FROM predictions WHERE student_id = ?", (student_id,))
    pred_record = cursor.fetchone()
    if pred_record:
        cursor.execute("""
        UPDATE predictions 
        SET predicted_gpa = ?, risk_level = ?, placement_score = ?
        WHERE student_id = ?
        """, (predicted_gpa, risk_level, placement_score, student_id))
    else:
        cursor.execute("""
        INSERT INTO predictions (student_id, predicted_gpa, risk_level, placement_score)
        VALUES (?, ?, ?, ?)
        """, (student_id, predicted_gpa, risk_level, placement_score))
    conn.commit()
    
    # 4. Fetch Weekly Tasks
    cursor.execute("SELECT * FROM tasks WHERE student_id = ? ORDER BY id DESC", (student_id,))
    tasks = cursor.fetchall()
    
    # Fetch top recommendation
    recs = get_recommendations(cgpa, attendance, coding_score, assignment_score, career_goal)
    career_recs = recs["career_recommendations"]
    
    conn.close()
    
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    
    conn.close()
    
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    
    cursor.execute("SELECT * FROM subjects WHERE student_id = ?", (student_id,))
    subjects = cursor.fetchall()
    
    cursor.execute("SELECT * FROM predictions WHERE student_id = ?", (student_id,))
    pred = cursor.fetchone()
    
    conn.close()
    
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


@app.route("/student/tasks/toggle/<int:task_id>")
def toggle_task(task_id):
    """Toggle weekly checklist task status between Completed and Pending"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ? AND student_id = ?", (task_id, session["user_id"]))
    task = cursor.fetchone()
    
    if task:
        new_status = "Pending" if task["status"] == "Completed" else "Completed"
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
        
    conn.close()
    return redirect(url_for("student_dashboard"))


@app.route("/student/tasks/regenerate")
def regenerate_tasks():
    """Regenerate tasks based on active weak subjects, career track, and risk parameters"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    student_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get student performance variables
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    
    cursor.execute("SELECT risk_level FROM predictions WHERE student_id = ?", (student_id,))
    pred_row = cursor.fetchone()
    risk = pred_row["risk_level"] if pred_row else "Low Risk"
    
    cursor.execute("SELECT subject_name FROM subjects WHERE student_id = ? AND marks < 60", (student_id,))
    weak_rows = cursor.fetchall()
    weak_subjs = [r["subject_name"] for r in weak_rows]
    
    # Delete current tasks
    cursor.execute("DELETE FROM tasks WHERE student_id = ?", (student_id,))
    
    # Generate new weekly tasks
    new_tasks = generate_weekly_tasks(
        student_id, 
        student["cgpa"], 
        student["attendance"], 
        student["coding_score"], 
        risk, 
        student["career_goal"], 
        weak_subjs
    )
    
    for t in new_tasks:
        cursor.execute("""
        INSERT INTO tasks (student_id, task_title, status, due_date)
        VALUES (?, ?, ?, ?)
        """, (student_id, t["task_title"], t["status"], t["due_date"]))
        
    conn.commit()
    conn.close()
    flash("Weekly tasks regenerated based on AI parameters!", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/student/career/update", methods=["POST"])
def update_career_goal():
    """Update student career goal selection dynamically"""
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
        
    career_goal = request.form.get("career_goal")
    student_id = session["user_id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE students SET career_goal = ? WHERE id = ?", (career_goal, student_id))
    conn.commit()
    conn.close()
    
    flash(f"Career focus successfully switched to {career_goal}!", "success")
    return redirect(url_for("student_dashboard"))


# ----------------------------------------------------
# TEACHER FEATURES & DASHBOARD
# ----------------------------------------------------

@app.route("/teacher/dashboard")
def teacher_dashboard():
    """Teacher Supervision Dashboard"""
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))
        
    dept = session.get("department")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch Students in department
    cursor.execute("""
        SELECT s.*, p.risk_level, p.predicted_gpa, p.placement_score 
        FROM students s
        LEFT JOIN predictions p ON s.id = p.student_id
        WHERE s.department = ?
        ORDER BY s.name ASC
    """, (dept,))
    students = cursor.fetchall()
    
    # 2. Compute Statistics Averages
    total_students = len(students)
    high_risk_count = 0
    med_risk_count = 0
    low_risk_count = 0
    cgpa_sum = 0
    attendance_sum = 0
    
    for s in students:
        cgpa_sum += s["cgpa"]
        attendance_sum += s["attendance"]
        
        risk = s["risk_level"] or "Low Risk"
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
    
    conn.close()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.attendance, p.risk_level 
        FROM students s
        LEFT JOIN predictions p ON s.id = p.student_id
        WHERE s.department = ?
    """, (dept,))
    rows = cursor.fetchall()
    
    # Calculate attendance distribution ranges:
    # 1: < 60%, 2: 60-75%, 3: 75-90%, 4: 90-100%
    att_ranges = [0, 0, 0, 0]
    high_r, med_r, low_r = 0, 0, 0
    for r in rows:
        att = r["attendance"]
        if att < 60:
            att_ranges[0] += 1
        elif att < 75:
            att_ranges[1] += 1
        elif att < 90:
            att_ranges[2] += 1
        else:
            att_ranges[3] += 1
            
        risk = r["risk_level"] or "Low Risk"
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
    
    conn.close()
    
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
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM students")
    students_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM teachers")
    teachers_count = cursor.fetchone()[0]
    
    # Read active teachers list
    cursor.execute("SELECT * FROM teachers ORDER BY id DESC")
    teachers = cursor.fetchall()
    
    conn.close()
    
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
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch global averages
    cursor.execute("SELECT attendance, cgpa FROM students")
    rows = cursor.fetchall()
    
    att_ranges = [0, 0, 0, 0]
    cgpa_sum, att_sum = 0, 0
    total = len(rows)
    for r in rows:
        att = r["attendance"]
        cgpa_sum += r["cgpa"]
        att_sum += att
        if att < 60:
            att_ranges[0] += 1
        elif att < 75:
            att_ranges[1] += 1
        elif att < 90:
            att_ranges[2] += 1
        else:
            att_ranges[3] += 1
            
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN risk_level = 'Low Risk' THEN 1 ELSE 0 END) as low,
            SUM(CASE WHEN risk_level = 'Medium Risk' THEN 1 ELSE 0 END) as med,
            SUM(CASE WHEN risk_level = 'High Risk' THEN 1 ELSE 0 END) as high
        FROM predictions
    """)
    pred_counts = cursor.fetchone()
    
    stats = {
        "low_risk": pred_counts["low"] or 0,
        "med_risk": pred_counts["med"] or 0,
        "high_risk": pred_counts["high"] or 0,
        "avg_cgpa": cgpa_sum / total if total > 0 else 0,
        "avg_attendance": att_sum / total if total > 0 else 0
    }
    
    conn.close()
    
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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM teachers WHERE email = ?", (email,))
    if cursor.fetchone():
        flash("Professor email already registered!", "error")
        conn.close()
        return redirect(url_for("admin_dashboard"))
        
    hashed_pwd = generate_password_hash(password)
    try:
        cursor.execute("""
        INSERT INTO teachers (name, email, password, department)
        VALUES (?, ?, ?, ?)
        """, (name, email, hashed_pwd, department))
        conn.commit()
        flash(f"Professor {name} successfully added to the system database!", "success")
    except Exception as e:
        flash(f"Error registering professor: {e}", "error")
    
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/teacher/delete/<int:teacher_id>")
def admin_delete_teacher(teacher_id):
    """Remove a faculty account"""
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
    conn.commit()
    conn.close()
    
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

@app.route("/download_report/<int:student_id>")
def download_report(student_id):
    """Generate printable layout summary of student profile"""
    if "user_id" not in session or session.get("role") not in ["teacher", "admin"]:
        return "Unauthorized Access Profile", 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    
    if not student:
        conn.close()
        return "Student record not found", 404
        
    cursor.execute("SELECT * FROM subjects WHERE student_id = ?", (student_id,))
    subjects = cursor.fetchall()
    
    cursor.execute("SELECT * FROM predictions WHERE student_id = ?", (student_id,))
    pred = cursor.fetchone()
    
    conn.close()
    
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
    """Assures SQLite database is initialized and seeded on boot"""
    if not os.path.exists(DB_PATH):
        print("Database not found. Triggering db_setup.py...")
        from database.db_setup import setup_database
        # If student csv exists, setup will load records
        setup_database(DB_PATH, CSV_PATH)

startup_checks()

if __name__ == "__main__":
    app.run(debug=True)
