import os
import sqlite3
import numpy as np
import pandas as pd
from werkzeug.security import generate_password_hash

def setup_database(db_path=os.path.join("database", "database.db"), csv_path="student_data.csv"):
    print("Setting up SQLite database...")
    
    # Ensure database folder exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create tables
    print("Creating tables...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        department TEXT NOT NULL,
        semester INTEGER NOT NULL,
        cgpa REAL NOT NULL,
        attendance REAL NOT NULL,
        coding_score INTEGER NOT NULL,
        assignment_score INTEGER NOT NULL,
        career_goal TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        department TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_name TEXT NOT NULL,
        marks INTEGER NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        task_title TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        due_date TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        predicted_gpa REAL NOT NULL,
        risk_level TEXT NOT NULL,
        placement_score REAL NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    print("Tables created successfully.")
    
    # Seed default teacher
    print("Seeding default teacher...")
    hashed_pwd = generate_password_hash("password123")
    cursor.execute("SELECT id FROM teachers WHERE email = 'teacher@edupilot.com'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO teachers (name, email, password, department)
        VALUES ('Dr. Sarah Connor', 'teacher@edupilot.com', ?, 'Computer Science')
        """, (hashed_pwd,))
        
    # Seed default admin
    print("Seeding default admin...")
    cursor.execute("SELECT id FROM admins WHERE email = 'admin@edupilot.com'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO admins (name, email, password)
        VALUES ('System Administrator', 'admin@edupilot.com', ?)
        """, (hashed_pwd,))
        
    # Seed default student
    print("Seeding default student...")
    cursor.execute("SELECT id FROM students WHERE email = 'student@edupilot.com'")
    default_student_exists = cursor.fetchone()
    
    if not default_student_exists:
        cursor.execute("""
        INSERT INTO students (name, email, password, department, semester, cgpa, attendance, coding_score, assignment_score, career_goal)
        VALUES ('Yaseen Ashu', 'student@edupilot.com', ?, 'Computer Science', 6, 7.8, 78.0, 65, 72, 'AIML Engineer')
        """, (hashed_pwd,))
        
        student_id = cursor.lastrowid
        
        # Seed subjects for default student
        subjects = [
            ("Data Structures & Algorithms", 82),
            ("Database Management Systems", 74),
            ("Machine Learning Fundamentals", 68),
            ("Operating Systems", 88),
            ("Discrete Mathematics", 62)
        ]
        for sub_name, marks in subjects:
            cursor.execute("""
            INSERT INTO subjects (student_id, subject_name, marks)
            VALUES (?, ?, ?)
            """, (student_id, sub_name, marks))
            
        # Seed weekly tasks for default student
        tasks = [
            ("Solve 5 DSA array problems on LeetCode", "Pending", "2026-05-28"),
            ("Watch python ML tutorial and write a clean script", "Pending", "2026-05-28"),
            ("Revise DBMS Transactions Unit 3", "Completed", "2026-05-24")
        ]
        for task_title, status, due_date in tasks:
            cursor.execute("""
            INSERT INTO tasks (student_id, task_title, status, due_date)
            VALUES (?, ?, ?, ?)
            """, (student_id, task_title, status, due_date))
            
        # Seed predictions for default student
        cursor.execute("""
        INSERT INTO predictions (student_id, predicted_gpa, risk_level, placement_score)
        VALUES (?, 7.95, 'Low Risk', 74.5)
        """, (student_id,))
        
    conn.commit()
    
    # Load more synthetic students from csv if it exists
    if os.path.exists(csv_path):
        print(f"Seeding additional students from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        # Only seed if student count is small
        cursor.execute("SELECT COUNT(*) FROM students")
        current_count = cursor.fetchone()[0]
        
        if current_count < 100:
            # Insert first 100 students from CSV
            added_count = 0
            for idx, row in df.head(100).iterrows():
                # Avoid duplicates
                if row['email'] == 'student@edupilot.com':
                    continue
                
                cursor.execute("SELECT id FROM students WHERE email = ?", (row['email'],))
                if cursor.fetchone():
                    continue
                    
                cursor.execute("""
                INSERT INTO students (name, email, password, department, semester, cgpa, attendance, coding_score, assignment_score, career_goal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['name'],
                    row['email'],
                    hashed_pwd,
                    row['department'],
                    int(row['semester']),
                    float(row['cgpa']),
                    float(row['attendance']),
                    int(row['coding_score']),
                    int(row['assignment_score']),
                    row['career_goal']
                ))
                
                s_id = cursor.lastrowid
                
                # Create random subjects based on department
                depts_subjs = {
                    "Computer Science": [("DSA", 80), ("DBMS", 75), ("OS", 85), ("CN", 70), ("Discrete Math", 65)],
                    "Artificial Intelligence": [("Python", 85), ("ML Fundamentals", 78), ("Probability", 70), ("Neural Networks", 60), ("DSA", 72)],
                    "Data Science": [("Statistics", 80), ("SQL", 85), ("Data Mining", 70), ("Data Visualization", 78), ("Python", 82)],
                    "DevOps": [("Linux Administration", 75), ("Networking", 70), ("Scripting", 80), ("Cloud Computing", 68), ("Software Engineering", 72)],
                    "Cybersecurity": [("Cryptography", 65), ("Network Security", 72), ("Linux Administration", 80), ("Ethical Hacking", 60), ("Information Security", 75)]
                }
                
                sub_list = depts_subjs.get(row['department'], depts_subjs["Computer Science"])
                for sub_name, sub_base_mark in sub_list:
                    # add some random noise to marks
                    m = int(np.clip(sub_base_mark + np.random.normal(0, 8), 30, 100))
                    cursor.execute("""
                    INSERT INTO subjects (student_id, subject_name, marks)
                    VALUES (?, ?, ?)
                    """, (s_id, sub_name, m))
                
                # Add a prediction
                # Categorize risk and gpa based on synthetic csv values
                cursor.execute("""
                INSERT INTO predictions (student_id, predicted_gpa, risk_level, placement_score)
                VALUES (?, ?, ?, ?)
                """, (
                    s_id,
                    float(row['predicted_gpa']),
                    row['risk_level'],
                    float(row['placement_score'])
                ))
                
                added_count += 1
                
            conn.commit()
            print(f"Successfully seeded {added_count} additional students from dataset.")
            
    conn.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    setup_database()
