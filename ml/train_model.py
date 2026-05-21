import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.metrics import classification_report, mean_squared_error, r2_score

def train_models(data_path="student_data.csv", models_dir="models"):
    print("Loading data...")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at {data_path}. Please run generate_data.py first.")
        
    df = pd.read_csv(data_path)
    
    # Create models directory if not exists
    os.makedirs(models_dir, exist_ok=True)
    
    print("\n----------------------------------------------------")
    print("1. TRAINING ACADEMIC RISK PREDICTION MODEL")
    print("----------------------------------------------------")
    # Features: attendance, cgpa, coding_score, assignment_score
    risk_features = ["attendance", "cgpa", "coding_score", "assignment_score"]
    X_risk = df[risk_features]
    y_risk = df["risk_level"]
    
    # Train-test split
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_risk, y_risk, test_size=0.2, random_state=42, stratify=y_risk)
    
    # RandomForest Classifier
    risk_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    risk_model.fit(X_train_r, y_train_r)
    
    # Evaluation
    y_pred_r = risk_model.predict(X_test_r)
    print("Academic Risk Classification Report:")
    print(classification_report(y_test_r, y_pred_r))
    
    # Save Risk Model
    risk_model_path = os.path.join(models_dir, "risk_model.pkl")
    joblib.dump(risk_model, risk_model_path)
    print(f"Risk model successfully saved to {risk_model_path}")
    
    print("\n----------------------------------------------------")
    print("2. TRAINING GPA PREDICTION MODEL")
    print("----------------------------------------------------")
    # Features: attendance, assignment_score, coding_score
    gpa_features = ["attendance", "assignment_score", "coding_score"]
    X_gpa = df[gpa_features]
    y_gpa = df["predicted_gpa"]
    
    # Train-test split
    X_train_g, X_test_g, y_train_g, y_test_g = train_test_split(X_gpa, y_gpa, test_size=0.2, random_state=42)
    
    # Linear Regression Model
    gpa_model = LinearRegression()
    gpa_model.fit(X_train_g, y_train_g)
    
    # Evaluation
    y_pred_g = gpa_model.predict(X_test_g)
    mse = mean_squared_error(y_test_g, y_pred_g)
    r2 = r2_score(y_test_g, y_pred_g)
    print(f"Mean Squared Error: {mse:.4f}")
    print(f"R-squared Score: {r2:.4f}")
    
    # Save GPA Model
    gpa_model_path = os.path.join(models_dir, "gpa_model.pkl")
    joblib.dump(gpa_model, gpa_model_path)
    print(f"GPA model successfully saved to {gpa_model_path}")
    
    print("\nModel training workflow completed successfully!")

if __name__ == "__main__":
    train_models()
