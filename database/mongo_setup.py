import os
import numpy as np
import pandas as pd
import pymongo
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

def setup_mongo():
    print("Setting up MongoDB Atlas database...")
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("Error: MONGO_URI not found in environment!")
        return
        
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    
    # Drop existing collections to ensure fresh start
    print("Clearing collections...")
    db.students.drop()
    db.teachers.drop()
    db.admins.drop()
    db.subjects.drop()
    db.tasks.drop()
    db.predictions.drop()
    
    # 1. Seed Teacher
    print("Seeding teacher...")
    hashed_pwd = generate_password_hash("password123")
    db.teachers.insert_one({
        "name": "Dr. Sarah Connor",
        "email": "teacher@paruluniversity.ac.in",
        "password": hashed_pwd,
        "department": "Computer Science"
    })
    
    # 2. Seed Admin
    print("Seeding admin...")
    db.admins.insert_one({
        "name": "System Administrator",
        "email": "admin@edupilot.com",
        "password": hashed_pwd
    })
    
    # 3. Seed default Student
    print("Seeding default student...")
    res = db.students.insert_one({
        "name": "Yaseen Ashu",
        "email": "student@paruluniversity.ac.in",
        "password": hashed_pwd,
        "department": "Computer Science",
        "semester": 6,
        "cgpa": 7.8,
        "attendance": 78.0,
        "coding_score": 65,
        "assignment_score": 72,
        "career_goal": "AIML Engineer"
    })
    student_id = res.inserted_id
    
    # Seed subjects
    subjects = [
        {"student_id": student_id, "subject_name": "Data Structures & Algorithms", "marks": 82},
        {"student_id": student_id, "subject_name": "Database Management Systems", "marks": 74},
        {"student_id": student_id, "subject_name": "Machine Learning Fundamentals", "marks": 68},
        {"student_id": student_id, "subject_name": "Operating Systems", "marks": 88},
        {"student_id": student_id, "subject_name": "Discrete Mathematics", "marks": 62}
    ]
    db.subjects.insert_many(subjects)
    
    # Seed tasks
    tasks = [
        {"student_id": student_id, "task_title": "Solve 5 DSA array problems on LeetCode", "status": "Pending", "due_date": "2026-05-28"},
        {"student_id": student_id, "task_title": "Watch python ML tutorial and write a clean script", "status": "Pending", "due_date": "2026-05-28"},
        {"student_id": student_id, "task_title": "Revise DBMS Transactions Unit 3", "status": "Completed", "due_date": "2026-05-24"}
    ]
    db.tasks.insert_many(tasks)
    
    # Seed predictions
    db.predictions.insert_one({
        "student_id": student_id,
        "predicted_gpa": 7.95,
        "risk_level": "Low Risk",
        "placement_score": 74.5
    })
    
    # 4. Seed additional students from csv if it exists
    csv_path = "student_data.csv"
    if os.path.exists(csv_path):
        print(f"Seeding additional students from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        added_count = 0
        for idx, row in df.head(100).iterrows():
            email = row['email']
            # Avoid duplicates
            if email == 'student@paruluniversity.ac.in' or email == 'student@edupilot.com':
                continue
                
            # Intelligently convert @edupilot.com -> @paruluniversity.ac.in for testing enforcer
            if "@edupilot.com" in email:
                email = email.replace("@edupilot.com", "@paruluniversity.ac.in")
                
            s_res = db.students.insert_one({
                "name": row['name'],
                "email": email,
                "password": hashed_pwd,
                "department": row['department'],
                "semester": int(row['semester']),
                "cgpa": float(row['cgpa']),
                "attendance": float(row['attendance']),
                "coding_score": int(row['coding_score']),
                "assignment_score": int(row['assignment_score']),
                "career_goal": row['career_goal']
            })
            s_id = s_res.inserted_id
            
            # Seed subjects
            depts_subjs = {
                "Computer Science": [("DSA", 80), ("DBMS", 75), ("OS", 85), ("CN", 70), ("Discrete Math", 65)],
                "Artificial Intelligence": [("Python", 85), ("ML Fundamentals", 78), ("Probability", 70), ("Neural Networks", 60), ("DSA", 72)],
                "Data Science": [("Statistics", 80), ("SQL", 85), ("Data Mining", 70), ("Data Visualization", 78), ("Python", 82)],
                "DevOps": [("Linux Administration", 75), ("Networking", 70), ("Scripting", 80), ("Cloud Computing", 68), ("Software Engineering", 72)],
                "Cybersecurity": [("Cryptography", 65), ("Network Security", 72), ("Linux Administration", 80), ("Ethical Hacking", 60), ("Information Security", 75)]
            }
            
            sub_list = depts_subjs.get(row['department'], depts_subjs["Computer Science"])
            sub_docs = []
            for sub_name, sub_base_mark in sub_list:
                m = int(np.clip(sub_base_mark + np.random.normal(0, 8), 30, 100))
                sub_docs.append({"student_id": s_id, "subject_name": sub_name, "marks": m})
            db.subjects.insert_many(sub_docs)
            
            # Seed prediction
            db.predictions.insert_one({
                "student_id": s_id,
                "predicted_gpa": float(row['predicted_gpa']),
                "risk_level": row['risk_level'],
                "placement_score": float(row['placement_score'])
            })
            added_count += 1
            
        print(f"Successfully seeded {added_count} additional students from CSV into MongoDB.")
    
    print("MongoDB Database seeding completed successfully!")

if __name__ == "__main__":
    setup_mongo()
