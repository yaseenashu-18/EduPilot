import datetime

def get_recommendations(cgpa, attendance, coding_score, assignment_score, career_goal):
    """
    Generate dynamic recommendations based on student's performance metrics and career goal.
    Returns a dictionary with categories:
    - career_recommendations: list of suggestions for career path
    - academic_recommendations: list of general academic study habits
    - urgent_actions: critical high-risk flags
    """
    recs = {
        "career_recommendations": [],
        "academic_recommendations": [],
        "urgent_actions": []
    }
    
    # 1. Career Goal Recommendations
    if career_goal == "AIML Engineer":
        if coding_score < 50:
            recs["career_recommendations"].extend([
                "Start with Python Basics (variables, loops, functions).",
                "Learn Linear Algebra and Calculus fundamentals.",
                "Review ML Basics: supervised vs unsupervised learning."
            ])
        elif coding_score < 75:
            recs["career_recommendations"].extend([
                "Implement simple ML algorithms from scratch (Linear Regression, KNN).",
                "Complete a Pandas and NumPy data manipulation course.",
                "Solve beginner-level data science challenges on Kaggle."
            ])
        else:
            recs["career_recommendations"].extend([
                "Explore Deep Learning frameworks (PyTorch or TensorFlow).",
                "Work on end-to-end ML pipelines and model deployment (Flask/FastAPI).",
                "Contribute to open-source ML libraries or write technical blogs."
            ])
            
    elif career_goal == "Software Developer":
        if coding_score < 50:
            recs["career_recommendations"].extend([
                "Learn core programming concepts in Java, C++ or JavaScript.",
                "Study object-oriented programming (OOP) principles.",
                "Solve 2 easy coding problems daily on platforms like LeetCode."
            ])
        elif coding_score < 75:
            recs["career_recommendations"].extend([
                "Focus on core Data Structures (Arrays, Linked Lists, Stacks, Queues).",
                "Build a basic full-stack web application.",
                "Learn standard version control using Git and GitHub."
            ])
        else:
            recs["career_recommendations"].extend([
                "Study advanced concepts (Trees, Graphs, Dynamic Programming).",
                "Learn System Design principles (Monolith vs Microservices).",
                "Participate in online hackathons and code sprint contests."
            ])
            
    elif career_goal == "Data Analyst":
        if coding_score < 50:
            recs["career_recommendations"].extend([
                "Master Advanced Microsoft Excel (Pivot tables, VLOOKUP).",
                "Learn SQL Basics (SELECT, WHERE, GROUP BY, ORDER BY).",
                "Understand basic statistical measures (Mean, Median, Std Dev)."
            ])
        elif coding_score < 75:
            recs["career_recommendations"].extend([
                "Learn data visualization tools like Tableau or Power BI.",
                "Practice complex SQL Queries (Joins, Subqueries, CTEs).",
                "Learn data cleaning methodologies using Python (Pandas)."
            ])
        else:
            recs["career_recommendations"].extend([
                "Build a complete data analytics portfolio with live dashboards.",
                "Learn story-telling with data and business communication.",
                "Understand A/B testing and hypothesis evaluation."
            ])
            
    elif career_goal == "DevOps Engineer":
        if coding_score < 50:
            recs["career_recommendations"].extend([
                "Get comfortable with Linux Command Line basics.",
                "Learn basic Scripting with Bash or Python.",
                "Understand the basics of Computer Networks (HTTP, DNS, IP)."
            ])
        elif coding_score < 75:
            recs["career_recommendations"].extend([
                "Learn Git branch management and code workflows.",
                "Understand Containerization fundamentals (Docker).",
                "Build a simple CI/CD Pipeline (GitHub Actions or Jenkins)."
            ])
        else:
            recs["career_recommendations"].extend([
                "Explore Infrastructure as Code (IaC) using Terraform.",
                "Learn Cloud administration (AWS, Azure, or GCP).",
                "Understand Container Orchestration (Kubernetes)."
            ])
            
    elif career_goal == "Cybersecurity":
        if coding_score < 50:
            recs["career_recommendations"].extend([
                "Learn networking concepts (OSI model, TCP/IP handshake).",
                "Understand the basics of operating systems security (Linux/Windows).",
                "Study basic cryptography concepts (hashing, symmetric/asymmetric key)."
            ])
        elif coding_score < 75:
            recs["career_recommendations"].extend([
                "Learn to use basic security tools (Wireshark, Nmap, Burp Suite).",
                "Understand common web vulnerabilities (OWASP Top 10).",
                "Participate in Capture The Flag (CTF) competitions."
            ])
        else:
            recs["career_recommendations"].extend([
                "Study penetration testing methodologies.",
                "Learn secure coding practices to prevent vulnerabilities.",
                "Prepare for professional certifications like Security+ or CEH."
            ])

    # 2. General Academic Performance Recommendations
    if cgpa < 6.0:
        recs["academic_recommendations"].extend([
            "Focus heavily on clearing backlogs and core subject concepts.",
            "Complete all revision sheets and past exam papers.",
            "Attend college remedial classes or seek peer tutoring."
        ])
    elif cgpa < 7.5:
        recs["academic_recommendations"].extend([
            "Review weak subjects for at least 1 hour daily.",
            "Participate actively in class discussions to clarify doubts.",
            "Summarize lecture notes weekly."
        ])
    else:
        recs["academic_recommendations"].extend([
            "Maintain your high GPA by planning study schedules ahead of exams.",
            "Aim for outstanding grades in project-based courses.",
            "Engage in academic research or technical papers under faculty guidance."
        ])
        
    # 3. Attendance Recommendations & Urgent Actions
    if attendance < 70:
        recs["urgent_actions"].append("CRITICAL: Your attendance is below 70%. Attendance shortage might bar you from end-semester exams.")
        recs["academic_recommendations"].extend([
            "Improve class consistency immediately.",
            "Meet your academic mentor to discuss attendance recovery plans.",
            "Formulate a strict daily morning study routine."
        ])
    elif attendance < 75:
        recs["urgent_actions"].append("WARNING: Attendance is currently borderline (between 70% and 75%). Increase class presence.")
        recs["academic_recommendations"].append("Attend all incoming laboratory and theory sessions to secure full internal marks.")
        
    if assignment_score < 50:
        recs["urgent_actions"].append("CRITICAL: Assignment average is poor (<50%). Submitting pending worksheets is essential.")
        
    return recs


def generate_weekly_tasks(student_id, cgpa, attendance, coding_score, risk_level, career_goal, weak_subjects):
    """
    Generate dynamic weekly tasks for a student.
    Returns a list of dictionaries with structure:
    - task_title: string
    - due_date: string (YYYY-MM-DD)
    """
    tasks = []
    today = datetime.date.today()
    due = (today + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    # 1. Subject specific tasks based on weak subjects
    if weak_subjects:
        for subj in weak_subjects[:2]:
            tasks.append({
                "student_id": student_id,
                "task_title": f"Revise {subj} Unit 2 and solve last year's questions",
                "status": "Pending",
                "due_date": due
            })
    else:
        tasks.append({
            "student_id": student_id,
            "task_title": "Review core academic course sheets and prepare weekly notes",
            "status": "Pending",
            "due_date": due
        })
        
    # 2. Career path tasks
    if career_goal == "AIML Engineer":
        if coding_score < 60:
            tasks.append({
                "student_id": student_id,
                "task_title": "Watch Python ML introductory tutorial and write notes",
                "status": "Pending",
                "due_date": due
            })
        else:
            tasks.append({
                "student_id": student_id,
                "task_title": "Solve 2 classification problems on simple datasets in Jupyter",
                "status": "Pending",
                "due_date": due
            })
    elif career_goal == "Software Developer":
        if coding_score < 60:
            tasks.append({
                "student_id": student_id,
                "task_title": "Solve 5 basic DSA questions (Arrays and Strings) on LeetCode",
                "status": "Pending",
                "due_date": due
            })
        else:
            tasks.append({
                "student_id": student_id,
                "task_title": "Implement a simple OOPs project (e.g. Library Management System)",
                "status": "Pending",
                "due_date": due
            })
    elif career_goal == "Data Analyst":
        tasks.append({
            "student_id": student_id,
            "task_title": "Complete SQL joins practice queries and aggregate exercises",
            "status": "Pending",
            "due_date": due
        })
    elif career_goal == "DevOps Engineer":
        tasks.append({
            "student_id": student_id,
            "task_title": "Write a bash script to automate folder backup and setup simple Dockerfile",
            "status": "Pending",
            "due_date": due
        })
    elif career_goal == "Cybersecurity":
        tasks.append({
            "student_id": student_id,
            "task_title": "Solve 3 PortSwigger Web Security Academy lab exercises (SQLi / XSS)",
            "status": "Pending",
            "due_date": due
        })
        
    # 3. Academic risk mitigation tasks
    if risk_level == "High Risk":
        tasks.append({
            "student_id": student_id,
            "task_title": "Schedule a 1-on-1 counseling session with your Class Coordinator",
            "status": "Pending",
            "due_date": due
        })
        tasks.append({
            "student_id": student_id,
            "task_title": "Ensure 100% attendance in all classes this upcoming week",
            "status": "Pending",
            "due_date": due
        })
    elif risk_level == "Medium Risk":
        tasks.append({
            "student_id": student_id,
            "task_title": "Submit all outstanding class and laboratory assignments",
            "status": "Pending",
            "due_date": due
        })
    else:
        # Low risk - extra boost
        tasks.append({
            "student_id": student_id,
            "task_title": "Take a mock placement programming assessment test (60 min)",
            "status": "Pending",
            "due_date": due
        })
        
    # Limit to max 4 tasks for readability
    return tasks[:4]
