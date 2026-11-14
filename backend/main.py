from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import pandas as pd
import numpy as np
import joblib
import threading
from notifications import incident_manager, notification_config, email_dispatcher, webhook_dispatcher

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
    scenario: str = "adversarial"

def run_adversarial_attack(model, fraud_transaction, epsilon=0.1, max_steps=500):
    perturbed = fraud_transaction.copy()
    for step in range(max_steps):
        prediction = model.predict([perturbed])[0]
        if prediction == 0:
            return perturbed, step, True
        direction = -np.sign(perturbed) 
        perturbed += epsilon * direction
    return perturbed, max_steps, False

@app.get("/api/incidents")
def get_incidents():
    return {"incidents": incident_manager.get_incidents()}

@app.post("/api/incidents/{incident_id}/action")
def handle_action(incident_id: str, body: dict):
    action = body.get("action")
    success = incident_manager.update_action(incident_id, action)
    return {"success": success}

@app.post("/api/notifications/config")
def update_config(cfg: dict):
    for k, v in cfg.items():
        if hasattr(notification_config, k):
            setattr(notification_config, k, v)
    return {"success": True}

@app.post("/api/notifications/test")
def test_notification(body: dict):
    test_incident = {
        "id": "TEST_001", "severity": "CRITICAL", "threat_score": 0.9,
        "epsilon": 0.05, "fraud_ratio": 0.9, "ml_prediction": "Safe (Fooled)",
        "steps_taken": 12, "cpp_report": "BLOCKED as probable Adversarial Evasion Attempt.",
        "timestamp": "2026-11-14T14:00:00", "status": "active"
    }
    channel = body.get("channel", "email")
    if channel == "email":
        ok = email_dispatcher.send_alert(test_incident)
    elif channel == "discord":
        ok = webhook_dispatcher.send_discord_alert(notification_config.discord_webhook_url, test_incident)
    elif channel == "telegram":
        ok = webhook_dispatcher.send_telegram_alert(notification_config.telegram_bot_token, notification_config.telegram_chat_id, test_incident)
    else:
        ok = False
    return {"success": ok}

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.post("/api/evaluate")
def evaluate_transaction(req: EvasionRequest):
    if not os.path.exists(MODEL_PATH) or not os.path.exists(HISTORY_CSV):
        raise HTTPException(status_code=500, detail="Model or data not found. Run python training script first.")
        
    model = joblib.load(MODEL_PATH)
    
    # Load transactions from history
    df = pd.read_csv(HISTORY_CSV, header=None)
    if req.scenario == "safe":
        data = df[df[29] == 0.0].drop(columns=[29]).values
    else:
        data = df[df[29] == 1.0].drop(columns=[29]).values
        
    if len(data) == 0:
        raise HTTPException(status_code=500, detail=f"No data found for scenario {req.scenario}.")
        
    target_txn = data[np.random.randint(len(data))]
    
    if req.scenario == "adversarial":
        perturbed_txn, steps, success = run_adversarial_attack(model, target_txn, req.epsilon)
        if not success:
            return {"success": False, "message": "Failed to evade ML model."}
        ml_prediction = "Safe (Fooled)"
    else:
        perturbed_txn = target_txn.copy()
        steps = 0
        pred = model.predict([perturbed_txn])[0]
        ml_prediction = "Fraud" if pred == 1 else "Safe"
        
    # Save perturbed transaction for C++ engine
    np.savetxt(EVASION_CSV, perturbed_txn.reshape(1, -1), delimiter=",")
    
    # Trigger C++ Engine
    cpp_dir = os.path.dirname(os.path.dirname(CPP_ENGINE_PATH))
    result = subprocess.run([CPP_ENGINE_PATH, EVASION_CSV], cwd=cpp_dir, capture_output=True, text=True)
    
    cpp_output = result.stdout
    blocked = "BLOCKED" in cpp_output

    result_dict = {
        "success": True,
        "steps_taken": steps,
        "original_features": target_txn.tolist(),
        "perturbed_features": perturbed_txn.tolist(),
        "ml_prediction": ml_prediction,
        "advguard_blocked": blocked,
        "cpp_report": cpp_output,
        "scenario": req.scenario
    }

    if blocked:
        incident = incident_manager.add_incident({
            "epsilon": req.epsilon,
            "steps_taken": steps,
            "ml_prediction": ml_prediction,
            "cpp_report": cpp_output,
            "scenario": req.scenario
        })

        def dispatch():
            if notification_config.email_enabled:
                email_dispatcher.send_alert(incident)
            if notification_config.discord_enabled:
                webhook_dispatcher.send_discord_alert(notification_config.discord_webhook_url, incident)
            if notification_config.telegram_enabled:
                webhook_dispatcher.send_telegram_alert(notification_config.telegram_bot_token, notification_config.telegram_chat_id, incident)

        threading.Thread(target=dispatch, daemon=True).start()

    return result_dict
