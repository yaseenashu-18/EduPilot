import os
import random
import numpy as np
import pandas as pd
from faker import Faker

def generate_synthetic_data(output_path="student_data.csv", num_students=5000):
    print(f"Generating {num_students} synthetic student records...")
    
    # Initialize Faker
    fake = Faker()
    Faker.seed(42)
    np.random.seed(42)
    random.seed(42)
    
    departments = ["Computer Science", "Artificial Intelligence", "Data Science", "DevOps", "Cybersecurity"]
    career_goals = ["AIML Engineer", "Software Developer", "Data Analyst", "DevOps Engineer", "Cybersecurity"]
    
    data = []
    
    for i in range(num_students):
        # Basic demographics
        name = fake.name()
        first_name = name.split()[0].lower()
        email = f"{first_name}.{random.randint(10, 999)}@edupilot.com"
        password = "password123"  # Will be hashed when seeded to DB
        dept = random.choice(departments)
        semester = random.randint(1, 8)
        
        # Performance parameters (correlated)
        # Attendance: beta distribution shifted to range 40 - 100, average around 80%
        attendance = float(np.clip(round(np.random.beta(5, 2) * 60 + 40, 1), 40.0, 100.0))
        
        # CGPA: 2.0 to 10.0, average around 7.5
        cgpa_base = np.random.normal(7.2, 1.2)
        if attendance < 65:
            cgpa_base -= 1.0  # low attendance correlates with lower cgpa
        cgpa = float(np.clip(round(cgpa_base, 2), 2.0, 10.0))
        
        # Coding score: 20 to 100, correlated with cgpa
        coding_base = (cgpa / 10.0) * 80 + np.random.normal(15, 10)
        coding_score = int(np.clip(round(coding_base), 20, 100))
        
        # Assignment score: 30 to 100, correlated with cgpa & attendance
        assign_base = (cgpa / 10.0) * 60 + (attendance / 100.0) * 30 + np.random.normal(10, 8)
        assign_score = int(np.clip(round(assign_base), 30, 100))
        
        # Career goal selection
        goal = random.choice(career_goals)
        
        # Calculate Academic Risk Level (Rule-based for synthetic labeling)
        if attendance < 60 or cgpa < 5.0 or (cgpa < 5.5 and assign_score < 50):
            risk_level = "High Risk"
        elif attendance < 75 or cgpa < 6.5 or coding_score < 45 or assign_score < 55:
            risk_level = "Medium Risk"
        else:
            risk_level = "Low Risk"
            
        # Placement Readiness Score (0-100 scale)
        # Based heavily on coding_score (40%), cgpa (40%), and assignment/attendance (20%)
        # Scale CGPA to 100 scale for calculation
        cgpa_scaled = cgpa * 10.0
        placement_score = float(np.clip(round(
            coding_score * 0.45 + 
            cgpa_scaled * 0.35 + 
            assign_score * 0.10 + 
            attendance * 0.10 + 
            np.random.normal(0, 3)
        , 1), 0.0, 100.0))
        
        # Calculate predicted future GPA (CGPA + potential shift based on coding & assignments)
        # E.g. next semester GPA
        gpa_shift = (coding_score + assign_score + attendance) / 300.0 - 0.5  # shift between -0.5 and +0.5
        predicted_gpa = float(np.clip(round(cgpa + gpa_shift * 0.4 + np.random.normal(0, 0.15), 2), 2.0, 10.0))
        
        data.append({
            "name": name,
            "email": email,
            "password": password,
            "department": dept,
            "semester": semester,
            "cgpa": cgpa,
            "attendance": attendance,
            "coding_score": coding_score,
            "assignment_score": assign_score,
            "career_goal": goal,
            "risk_level": risk_level,
            "placement_score": placement_score,
            "predicted_gpa": predicted_gpa
        })
        
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Dataset successfully created and saved to {output_path}")
    print(df.head())
    
    # Return statistics
    print("\nRisk Level Distribution:")
    print(df["risk_level"].value_counts())
    print(f"Mean CGPA: {df['cgpa'].mean():.2f}")
    print(f"Mean Attendance: {df['attendance'].mean():.2f}%")

if __name__ == "__main__":
    generate_synthetic_data()
