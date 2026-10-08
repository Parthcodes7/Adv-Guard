from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import pandas as pd
import numpy as np
import joblib

app = FastAPI()

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(BASE_DIR, "ml_baseline")
DATA_DIR = os.path.join(ML_DIR, "data")
MODEL_PATH = os.path.join(DATA_DIR, "vulnerable_model.pkl")
CPP_ENGINE_PATH = os.path.join(BASE_DIR, "cpp_engine", "build", "advguard_engine.exe")
EVASION_CSV = os.path.join(DATA_DIR, "evasion_sample.csv")
HISTORY_CSV = os.path.join(DATA_DIR, "historical_history.csv")

class EvasionRequest(BaseModel):
    epsilon: float = 0.1

def run_adversarial_attack(model, fraud_transaction, epsilon=0.1, max_steps=500):
    perturbed = fraud_transaction.copy()
    for step in range(max_steps):
        prediction = model.predict([perturbed])[0]
        if prediction == 0:
            return perturbed, step, True
        direction = -np.sign(perturbed) 
        perturbed += epsilon * direction
    return perturbed, max_steps, False

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.post("/api/evaluate")
def evaluate_transaction(req: EvasionRequest):
    if not os.path.exists(MODEL_PATH) or not os.path.exists(HISTORY_CSV):
        raise HTTPException(status_code=500, detail="Model or data not found. Run python training script first.")
        
    model = joblib.load(MODEL_PATH)
    
    # Load a fraud transaction from history
    df = pd.read_csv(HISTORY_CSV, header=None)
    fraud_data = df[df[29] == 1.0].drop(columns=[29]).values
    if len(fraud_data) == 0:
        raise HTTPException(status_code=500, detail="No fraud data found in history.")
        
    target_txn = fraud_data[np.random.randint(len(fraud_data))]
    
    # Execute Attack
    perturbed_txn, steps, success = run_adversarial_attack(model, target_txn, req.epsilon)
    
    if not success:
        return {"success": False, "message": "Failed to evade ML model."}
        
    # Save perturbed transaction for C++ engine
    np.savetxt(EVASION_CSV, perturbed_txn.reshape(1, -1), delimiter=",")
    
    # Trigger C++ Engine
    cpp_dir = os.path.dirname(os.path.dirname(CPP_ENGINE_PATH))
    result = subprocess.run([CPP_ENGINE_PATH, EVASION_CSV], cwd=cpp_dir, capture_output=True, text=True)
    
    cpp_output = result.stdout
    blocked = "BLOCKED" in cpp_output
    
    return {
        "success": True,
        "steps_taken": steps,
        "original_features": target_txn.tolist(),
        "perturbed_features": perturbed_txn.tolist(),
        "ml_prediction": "Safe (Fooled)",
        "advguard_blocked": blocked,
        "cpp_report": cpp_output
    }
