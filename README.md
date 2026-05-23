# EduPilot AI – Smart Academic & Career Guidance Platform

EduPilot AI is a modern, full-stack Machine Learning web application designed to help students, teachers, and administrators optimize the academic journey. By applying Random Forest Classifiers and Linear Regression models to student metrics, the platform flags academic risk, estimates semester GPA, calculates placement readiness, and generates custom weekly improvement paths.

---

## Key Features

### 👤 Student Console
- **Unified Academic Roster:** Monitor attendance metrics, current CGPA, assignment progress, and coding streak indicators.
- **AI Recommendation Engine:** Custom learning roadmaps tailored to specific career goals and metrics (e.g. AIML, Software Developer, DevOps, Cybersecurity, Data Analyst).
- **Weekly Checklist:** Actionable, weak-subject-oriented goals generated dynamically by our rule-engine. Toggling tasks automatically synchronizes progress stats.
- **Grade Trajectory & Competency Profiles:** High-fidelity interactive Chart.js visualizations outlining GPA trends and radar competence views.

### 👩‍🏫 Faculty Panel
- **Searchable Supervision Roster:** Live student monitoring filtering by name or performance brackets.
- **Risk Indicators:** Dynamic High, Medium, and Low risk indicator badges predicted via scikit-learn random forests.
- **PDF Report Exporter:** Print-optimized, beautifully laid out reports ready for PDF downloading (Ctrl+P).
- **Classroom Stat Panels:** Aggregated averages tracking total students, average CGPA, and class attendance thresholds.

### 🔑 Administrative Dashboard
- **Global Control Center:** High-level registry counts.
- **ML Re-Triggers:** Single-click console actions to generate 5,000 synthetic records and retrain/serialize standard parameters instantly.
- **Faculty Registry Control:** Add, edit, or delete professor login accounts dynamically.

---

## Tech Stack & Architecture

- **Backend Framework:** Python Flask
- **Frontend Layer:** HTML5, Vanilla CSS3 (custom responsive grid variables, glassmorphism), Bootstrap 5, FontAwesome
- **Charts:** Chart.js
- **Database Schema:** SQLite
- **Machine Learning Pipelines:** Pandas, NumPy, Scikit-learn (Random Forest & Linear Regression), joblib, Faker

---

## Project Structure

```
EduPilotAI/
│
├── app.py                      # Main Flask application & routes controller
├── requirements.txt            # Python environment dependencies
├── Procfile                    # Render deployment profile
├── runtime.txt                 # Target Python engine (python-3.10.12)
├── README.md                   # Installation & platform guide
│
├── ml/
│   ├── generate_data.py        # 5k student synthetic generator (Faker & NumPy)
│   ├── train_model.py          # Random Forest & Linear Regression trainer
│   └── recommendation_engine.py# Heuristic rule-recs and task calculators
│
├── database/
│   ├── database.db             # Loaded SQLite instance
│   └── db_setup.py             # SQLite schema definitions & default seeders
│
├── models/
│   ├── risk_model.pkl          # Trained RandomForest classifier
│   └── gpa_model.pkl           # Trained LinearRegression model
│
├── static/
│   ├── css/
│   │   └── styles.css          # Glassmorphic style declarations & theme variables
│   └── js/
│       ├── main.js             # Theme-toggles, quotes, UI binders
│       └── dashboard_charts.js # Chart.js integrations & radar plots
│
└── templates/
    ├── base.html               # Shared layout structure, responsive sidebars
    ├── index.html              # Startup landing page
    ├── login.html              # Unified login page
    ├── register.html           # Student registration form
    ├── student_dashboard.html  # Personalized student workspace
    ├── teacher_dashboard.html  # Teacher roster dashboard
    ├── admin_dashboard.html    # Administrative ML control center
    ├── analytics.html          # stand-alone interactive graphs
    └── report_template.html    # Print-optimized printable student report
```

---

## Live Evaluation Credentials

To make platform testing instant, the database is pre-seeded with the following credentials (password is **`password123`** for all):

| Profile Role | Login Email | Account Details |
| :--- | :--- | :--- |
| **Student** | `student@paruluniversity.ac.in` | Name: **Yaseen Ashu**, CGPA: **7.8**, Attendance: **78%**, Department: **Computer Science** |
| **Teacher** | `teacher@paruluniversity.ac.in` | Name: **Dr. Sarah Connor**, Department: **Computer Science** |
| **Admin** | `admin@edupilot.com` | Name: **System Administrator** |

---

## Installation & Setup Instructions

### 1. Clone & Position Workspace
Ensure you are operating within the repository directory:
```bash
cd EduPilot
```

### 2. Install Dependencies
Install all required libraries using pip:
```bash
pip install -r requirements.txt
```

### 3. Generate Data and Train Models
Before launching the server, run the ML pipelines to create the student dataset and train/serialize models:
```bash
# 1. Generate 5,000 synthetic student entries (saves as student_data.csv)
python ml/generate_data.py

# 2. Train and save models (saves risk_model.pkl and gpa_model.pkl in models/)
python ml/train_model.py
```

### 4. Create and Seed Database
Run the setup script to initialize the SQLite database (`database/database.db`) and seed the default testing accounts:
```bash
python database/db_setup.py
```

### 5. Launch the Platform
Start the local development server:
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000` to interact with the platform.

---

## Machine Learning Specifications

### 🛡️ Academic Risk Prediction Model
- **Algorithm:** Random Forest Classifier (`RandomForestClassifier`)
- **Features:** Attendance, CGPA, Coding Score, Assignment Score
- **Classes:** Low Risk, Medium Risk, High Risk

### 📈 GPA Forecast Model
- **Algorithm:** Linear Regression (`LinearRegression`)
- **Features:** Attendance, Assignment Score, Coding Score
- **Output:** Predicted future GPA for the upcoming academic session
