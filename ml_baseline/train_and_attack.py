import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
import os

from sklearn.datasets import fetch_openml
from sklearn.preprocessing import StandardScaler

def load_real_data():
    """
    Loads the real Kaggle Credit Card Fraud dataset from OpenML.
    """
    print("Fetching real Kaggle Credit Card Fraud dataset from OpenML...")
    data = fetch_openml(data_id=1597, as_frame=True, parser='auto')
    df = data.frame
    
    # Ensure Class is numeric
    df['Class'] = pd.to_numeric(df['Class'])
    
    # Use the full dataset for maximum accuracy and perfect training
    df_sampled = df
    
    y = df_sampled['Class'].values
    X = df_sampled.drop(columns=['Class'])
    
    # Scale features (StandardScaler is standard practice, especially for Amount)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Save the scaler to reverse transform if needed
    joblib.dump(scaler, "data/scaler.pkl")
    
    return train_test_split(X_scaled, y, test_size=0.2, random_state=42)

def train_model(X_train, y_train):
    """
    Trains a vulnerable baseline ML model.
    """
    print("Training vulnerable baseline model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    return model

def adversarial_evasion_attack(model, fraud_transaction, epsilon=0.5, max_steps=500):
    """
    A white-box style evasion attack simulation.
    Nudges a fraudulent transaction towards the decision boundary until it is classified as safe.
    
    Args:
        model: The trained ML model
        fraud_transaction: The feature vector of a known fraud
        epsilon: The step size for perturbation
    Returns:
        perturbed_transaction, success_boolean
    """
    perturbed = fraud_transaction.copy()
    
    # Assuming fraud is class 1, we want the model to predict class 0 (safe)
    for step in range(max_steps):
        prediction = model.predict([perturbed])[0]
        if prediction == 0:
            print(f"Attack successful at step {step}!")
            return perturbed, True
            
        # Simplistic evasion: move features slightly towards 0 (the mean of our legit class)
        # In a sophisticated attack, this would use gradient-based methods like FGSM for tabular data.
        direction = -np.sign(perturbed) 
        perturbed += epsilon * direction
        
    print("Attack failed to evade the model.")
    return perturbed, False

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    
    # 1. Load Data
    X_train, X_test, y_train, y_test = load_real_data()
    
    # Save training data for C++ KD-Tree history (limit to 1000 to keep C++ memory usage low for prototype)
    # The C++ engine needs history to build its KD-Tree.
    history_subset_X = X_train[:1000]
    history_subset_y = y_train[:1000].reshape(-1, 1)
    history_combined = np.hstack([history_subset_X, history_subset_y])
    np.savetxt("data/historical_history.csv", history_combined, delimiter=",")
    print("Saved historical history to data/historical_history.csv")
    
    # 2. Train Base Model
    model = train_model(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("Baseline Model Performance:")
    print(classification_report(y_test, y_pred))
    
    # Save the model
    joblib.dump(model, "data/vulnerable_model.pkl")
    print("Saved model to data/vulnerable_model.pkl")
    
    # 3. Simulate an Attack
    # Pick a known fraud transaction from the test set
    fraud_indices = np.where(y_test == 1)[0]
    original_fraud = X_test[fraud_indices[0]]
    
    print("\n--- Starting Adversarial Evasion ---")
    print(f"Original ML Prediction: {model.predict([original_fraud])[0]} (Expected: 1.0 Fraud)")
    
    perturbed_fraud, success = adversarial_evasion_attack(model, original_fraud, epsilon=0.1)
    
    if success:
        print(f"The model has been fooled. It now predicts this transaction as: {model.predict([perturbed_fraud])[0]} Safe.")
        print("This is exactly the blind spot where AdvGuard's C++ KD-Tree defense will step in!")
        # Save perturbed transaction for the C++ engine to ingest and block
        np.savetxt("data/evasion_sample.csv", perturbed_fraud.reshape(1, -1), delimiter=",")
        print("Saved evasion sample to data/evasion_sample.csv")
        
        print("\n--- Triggering AdvGuard C++ Engine ---")
        cpp_executable = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cpp_engine", "build", "advguard_engine.exe"))
        evasion_csv = os.path.abspath("data/evasion_sample.csv")
        
        if os.path.exists(cpp_executable):
            import subprocess
            # Change directory to cpp_engine so it finds the relative history paths
            cpp_dir = os.path.dirname(os.path.dirname(cpp_executable))
            result = subprocess.run([cpp_executable, evasion_csv], cwd=cpp_dir, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("C++ Errors:", result.stderr)
        else:
            print(f"WARNING: Could not find C++ executable at {cpp_executable}. Please compile the C++ code first.")
