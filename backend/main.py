from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import subprocess
import os
import pandas as pd
import numpy as np
import joblib
import threading
from scipy.spatial import KDTree
from notifications import incident_manager, notification_config, email_dispatcher, webhook_dispatcher, ntfy_dispatcher
from benchmark import get_benchmark_results
from attacks import fgsm_attack, boundary_attack, jsma_sparse_attack, heuristic_attack, analyze_perturbation
from forensics import generate_forensic_brief

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

class CustomNotificationRequest(BaseModel):
    channel: str = "push"  # "push", "email", "sms", "discord"
    title: str = "AdvGuard Security Alert"
    message: str = ""
    recipient: str = "advguard-alerts"
    priority: str = "urgent"  # "min", "low", "default", "high", "urgent"
    incident_id: str = "N/A"
    tags: str = "shield,warning"

class EvasionRequest(BaseModel):
    epsilon: float = 0.05
    scenario: str = "adversarial"
    attack_method: str = "fgsm" # "fgsm", "boundary", "jsma", "heuristic"

def execute_advguard_engine(perturbed_txn):
    # 1. Attempt to run compiled C++ engine
    try:
        cpp_dir = os.path.dirname(os.path.dirname(CPP_ENGINE_PATH))
        result = subprocess.run([CPP_ENGINE_PATH, EVASION_CSV], cwd=cpp_dir, capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except Exception as e:
        print(f"AdvGuard engine note: {e}. Running geometric KD-Tree verification.")

    # 2. Geometric KD-Tree verification fallback
    df = pd.read_csv(HISTORY_CSV, header=None)
    X_hist = df.iloc[:, :29].values
    y_hist = df.iloc[:, 29].values

    tree = KDTree(X_hist)
    distances, indices = tree.query(perturbed_txn[:29], k=10)
    neighbor_labels = y_hist[indices]
    fraud_count = np.sum(neighbor_labels == 1.0)
    fraud_ratio = fraud_count / len(neighbor_labels)

    if fraud_ratio >= 0.6:
        report = (
            "=== ADVGUARD FORENSIC REPORT ===\n"
            "Status: BLOCKED (OVERRIDDEN)\n\n"
            "ALERT: Transaction geometrically inconsistent with ML prediction.\n"
            f"{int(fraud_ratio * 100)}% of spatial neighbors are historically Fraud.\n"
            "Transaction SUSPECT_TXN_001 BLOCKED as probable Adversarial Evasion Attempt.\n"
            "=== END REPORT ===\n"
        )
    else:
        report = (
            "=== ADVGUARD FORENSIC REPORT ===\n"
            "Status: APPROVED\n\n"
            "SUCCESS: Transaction geometrically consistent with Safe cluster. Approved.\n"
            "=== END REPORT ===\n"
        )
    return report

@app.get("/api/incidents")
def get_incidents():
    return {"incidents": incident_manager.get_incidents()}

@app.post("/api/incidents/{incident_id}/action")
def handle_action(incident_id: str, body: dict):
    action = body.get("action")
    success = incident_manager.update_action(incident_id, action)
    return {"success": success}

@app.get("/api/incidents/{incident_id}/forensics")
def get_incident_forensics(incident_id: str):
    incidents = incident_manager.get_incidents()
    for inc in incidents:
        if inc.get("id") == incident_id:
            brief = inc.get("forensic_brief") or generate_forensic_brief(inc)
            return {"success": True, "forensics": brief}
    raise HTTPException(status_code=404, detail="Incident not found")

@app.get("/api/notifications/config")
def get_config():
    return {
        "ntfy_enabled": notification_config.ntfy_enabled,
        "ntfy_topic": notification_config.ntfy_topic,
        "email_enabled": notification_config.email_enabled,
        "smtp_host": notification_config.smtp_host,
        "smtp_port": notification_config.smtp_port,
        "sender_email": notification_config.sender_email,
        "sender_password": notification_config.sender_password,
        "recipient_email": notification_config.recipient_email,
        "discord_enabled": notification_config.discord_enabled,
        "discord_webhook_url": notification_config.discord_webhook_url,
        "telegram_enabled": notification_config.telegram_enabled,
        "telegram_bot_token": notification_config.telegram_bot_token,
        "telegram_chat_id": notification_config.telegram_chat_id
    }

@app.post("/api/notifications/config")
def update_config(cfg: dict):
    for k, v in cfg.items():
        if hasattr(notification_config, k):
            setattr(notification_config, k, v)
    # Rebuild email_dispatcher with fresh credentials from notification_config
    email_dispatcher.smtp_host = notification_config.smtp_host
    email_dispatcher.smtp_port = notification_config.smtp_port
    email_dispatcher.sender_email = notification_config.sender_email
    email_dispatcher.sender_password = notification_config.sender_password
    email_dispatcher.recipient_email = notification_config.recipient_email
    return {"success": True}

@app.post("/api/notifications/dispatch")
def dispatch_custom_notification(req: CustomNotificationRequest):
    """
    Universal notification creator dispatcher:
    Supports Push (ntfy.sh), Email forwarder, SMS Simulator stream, and Discord.
    """
    import datetime
    import requests

    channel = (req.channel or "push").lower()
    
    if channel == "push":
        topic = (req.recipient or notification_config.ntfy_topic or "advguard-alerts").strip()
        ok, res = ntfy_dispatcher.send_notification(
            topic=topic,
            title=req.title,
            message=req.message,
            priority=req.priority,
            tags=req.tags or "shield,warning"
        )
        return {
            "success": ok,
            "channel": "push",
            "delivery": res,
            "stream_url": f"https://ntfy.sh/{topic}"
        }

    elif channel == "email":
        # Forward direct to email recipient without requiring SMTP passwords
        target_email = req.recipient if (req.recipient and "@" in req.recipient) else notification_config.recipient_email
        if not target_email or "@" not in target_email:
            return {"success": False, "channel": "email", "error": "Invalid or missing recipient email address."}
        
        ok, res = ntfy_dispatcher.send_notification(
            topic=notification_config.ntfy_topic or "advguard-alerts",
            title=req.title,
            message=req.message,
            priority=req.priority,
            tags="incoming_envelope,shield",
            email=target_email
        )
        return {
            "success": ok,
            "channel": "email",
            "delivery": res,
            "recipient": target_email
        }

    elif channel == "sms":
        # Realistic SMS Gateway simulator: publishes to dedicated ntfy SMS channel and yields delivery receipt
        phone = (req.recipient or "+1 (555) 019-2834").strip()
        sms_topic = "advguard-sms-stream"
        ok, res = ntfy_dispatcher.send_notification(
            topic=sms_topic,
            title=f"SMS Gateway Alert -> {phone}",
            message=req.message,
            priority="high",
            tags="mobile_phone,incoming_envelope"
        )
        return {
            "success": True,
            "channel": "sms",
            "delivery": {
                "recipient_phone": phone,
                "gateway_id": "TELCO-VIRTUAL-GATEWAY-1",
                "status": "DELIVERED_TO_HANDSET",
                "carrier": "AdvGuard Secure Telco Relay",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "stream_url": f"https://ntfy.sh/{sms_topic}"
            }
        }

    elif channel == "discord":
        webhook_url = (req.recipient or notification_config.discord_webhook_url).strip()
        if not webhook_url or not webhook_url.startswith("http"):
            return {"success": False, "channel": "discord", "error": "Invalid Discord Webhook URL"}
        try:
            payload = {
                "username": "AdvGuard SOC Sentinel",
                "avatar_url": "https://img.icons8.com/color/96/shield.png",
                "embeds": [{
                    "title": req.title,
                    "description": req.message,
                    "color": 0xe74c3c if req.priority == "urgent" else 0x3498db,
                    "fields": [
                        {"name": "Priority", "value": req.priority.upper(), "inline": True},
                        {"name": "Incident Ref", "value": req.incident_id, "inline": True}
                    ],
                    "footer": {"text": "AdvGuard Autonomous SOC · Zero-Trust Pipeline"}
                }]
            }
            resp = requests.post(webhook_url, json=payload, timeout=6)
            return {"success": resp.status_code in (200, 204), "channel": "discord", "delivery": {"status": resp.status_code}}
        except Exception as e:
            return {"success": False, "channel": "discord", "error": str(e)}

    return {"success": False, "channel": channel, "error": f"Unsupported notification channel '{channel}'."}

@app.post("/api/notifications/test")
def test_notification(body: dict):
    import logging
    test_incident = {
        "id": "TEST_001", "severity": "CRITICAL", "threat_score": 0.9,
        "epsilon": 0.05, "fraud_ratio": 0.9, "ml_prediction": "Safe (Fooled)",
        "steps_taken": 12, "cpp_report": "BLOCKED as probable Adversarial Evasion Attempt.",
        "timestamp": "2026-11-14T14:00:00", "status": "active"
    }
    channel = body.get("channel", "email")
    error_msg = None
    ok = False
    if channel == "email":
        email_dispatcher.smtp_host = notification_config.smtp_host
        email_dispatcher.smtp_port = notification_config.smtp_port
        email_dispatcher.sender_email = notification_config.sender_email
        email_dispatcher.sender_password = notification_config.sender_password
        email_dispatcher.recipient_email = notification_config.recipient_email
        ok = email_dispatcher.send_alert(test_incident)
        error_msg = None if ok else email_dispatcher.last_message
    elif channel == "discord":
        if not notification_config.discord_webhook_url:
            error_msg = "Discord webhook URL not configured."
        else:
            ok = webhook_dispatcher.send_discord_alert(notification_config.discord_webhook_url, test_incident)
    elif channel == "telegram":
        if not notification_config.telegram_bot_token or not notification_config.telegram_chat_id:
            error_msg = "Telegram bot_token or chat_id not configured."
        else:
            ok = webhook_dispatcher.send_telegram_alert(notification_config.telegram_bot_token, notification_config.telegram_chat_id, test_incident)
    else:
        error_msg = "Unknown channel."
    return {"success": ok, "error": error_msg}

@app.get("/api/notifications/preview-email", response_class=HTMLResponse)
def preview_email():
    preview_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latest_email_preview.html")
    if os.path.exists(preview_path):
        with open(preview_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>No email generated yet. Run a test email or simulate an attack.</h3>"

@app.get("/api/benchmark")
def get_benchmark():
    return get_benchmark_results(force_rerun=False)

@app.post("/api/benchmark/run")
def run_benchmark():
    return get_benchmark_results(force_rerun=True)

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
        fraud_candidates = df[df[29] == 1.0].drop(columns=[29]).values
        # Filter for verified frauds where model initially predicts Fraud (1)
        valid_frauds = [f for f in fraud_candidates if model.predict([f])[0] == 1]
        data = np.array(valid_frauds) if len(valid_frauds) > 0 else fraud_candidates
        
    if len(data) == 0:
        raise HTTPException(status_code=500, detail=f"No data found for scenario {req.scenario}.")
        
    target_txn = data[np.random.randint(len(data))]
    attack_label = req.attack_method.upper() if req.scenario == "adversarial" else "None"
    
    if req.scenario == "adversarial":
        method = req.attack_method.lower()
        if method == "boundary":
            safe_data = df[df[29] == 0.0].drop(columns=[29]).values
            safe_anchor = safe_data.mean(axis=0)
            perturbed_txn, steps, success = boundary_attack(model, target_txn, safe_anchor)
            attack_label = "Decision Boundary Probing"
        elif method == "jsma":
            perturbed_txn, steps, success = jsma_sparse_attack(model, target_txn, epsilon=req.epsilon)
            attack_label = "Sparse Feature Saliency (JSMA)"
        elif method == "heuristic":
            perturbed_txn, steps, success = heuristic_attack(model, target_txn, epsilon=req.epsilon)
            attack_label = "Heuristic Directional"
        else: # default "fgsm"
            perturbed_txn, steps, success = fgsm_attack(model, target_txn, epsilon=req.epsilon)
            attack_label = "FGSM (Fast Gradient Sign)"
            
        if not success:
            return {"success": False, "message": f"Attack ({attack_label}) failed to evade ML model."}
        ml_prediction = "Safe (Fooled)"
        distortion_stats = analyze_perturbation(target_txn, perturbed_txn)
    else:
        perturbed_txn = target_txn.copy()
        steps = 0
        pred = model.predict([perturbed_txn])[0]
        ml_prediction = "Fraud" if pred == 1 else "Safe"
        distortion_stats = analyze_perturbation(target_txn, perturbed_txn)
        
    # Save perturbed transaction for C++ engine
    np.savetxt(EVASION_CSV, perturbed_txn.reshape(1, -1), delimiter=",")
    
    # Trigger AdvGuard Engine (C++ with Geometric KD-Tree fallback)
    cpp_output = execute_advguard_engine(perturbed_txn)
    blocked = "BLOCKED" in cpp_output

    result_dict = {
        "success": True,
        "steps_taken": steps,
        "original_features": target_txn.tolist(),
        "perturbed_features": perturbed_txn.tolist(),
        "ml_prediction": ml_prediction,
        "advguard_blocked": blocked,
        "cpp_report": cpp_output,
        "scenario": req.scenario,
        "attack_method": attack_label,
        "distortion_stats": distortion_stats
    }

    if blocked:
        incident = incident_manager.add_incident({
            "epsilon": req.epsilon,
            "steps_taken": steps,
            "ml_prediction": ml_prediction,
            "cpp_report": cpp_output,
            "scenario": req.scenario,
            "attack_method": attack_label,
            "distortion_stats": distortion_stats
        })

        def dispatch():
            # Zero-config real-time push to ntfy.sh (rings phone/browser)
            if notification_config.ntfy_enabled:
                ntfy_dispatcher.send_incident_alert(
                    incident,
                    topic=notification_config.ntfy_topic or "advguard-alerts",
                    email=notification_config.recipient_email if notification_config.email_enabled else None
                )
            if notification_config.email_enabled:
                email_dispatcher.send_alert(incident)
            if notification_config.discord_enabled:
                webhook_dispatcher.send_discord_alert(notification_config.discord_webhook_url, incident)
            if notification_config.telegram_enabled:
                webhook_dispatcher.send_telegram_alert(notification_config.telegram_bot_token, notification_config.telegram_chat_id, incident)

        threading.Thread(target=dispatch, daemon=True).start()

    return result_dict
