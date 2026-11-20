"""
AdvGuard Notification System
Handles incident management, email alerts, Discord/Telegram webhooks.
"""

import heapq
import logging
import os
import re
import smtplib
import ssl
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests
from forensics import generate_forensic_brief

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# A. IncidentManager — priority queue backed by a max-heap
# ---------------------------------------------------------------------------

class IncidentManager:
    def __init__(self):
        # heap entries: (-threat_score, incident_id, incident_dict)
        self._heap: list = []
        self._incidents: dict = {}  # id -> incident dict

    def add_incident(self, data: dict) -> dict:
        # Parse fraud_ratio from cpp_report (float before %)
        cpp_report = data.get("cpp_report", "")
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", cpp_report)
        fraud_ratio = float(match.group(1)) / 100.0 if match else 0.0

        epsilon = float(data.get("epsilon", 0.0))
        threat_score = round(0.4 * epsilon + 0.6 * fraud_ratio, 6)

        if threat_score > 0.7:
            severity = "CRITICAL"
        elif threat_score > 0.5:
            severity = "HIGH"
        elif threat_score > 0.3:
            severity = "WARNING"
        else:
            severity = "SAFE"

        incident_id = str(uuid.uuid4())[:8].upper()
        incident = {
            "id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "threat_score": threat_score,
            "epsilon": epsilon,
            "steps_taken": data.get("steps_taken", 0),
            "fraud_ratio": fraud_ratio,
            "ml_prediction": data.get("ml_prediction", "Unknown"),
            "status": "active",
            "cpp_report": cpp_report,
            "scenario": data.get("scenario", "adversarial"),
            "attack_method": data.get("attack_method", "FGSM"),
            "distortion_stats": data.get("distortion_stats", {})
        }

        # Autonomous AI Forensic Intelligence Dossier
        incident["forensic_brief"] = generate_forensic_brief(incident)

        heapq.heappush(self._heap, (-threat_score, incident_id, incident))
        self._incidents[incident_id] = incident
        logger.info("Incident %s created: severity=%s threat_score=%.4f", incident_id, severity, threat_score)
        return incident

    def get_incidents(self) -> list:
        return sorted(self._incidents.values(), key=lambda i: i["threat_score"], reverse=True)

    def update_action(self, incident_id: str, action: str) -> bool:
        valid_statuses = {"resolved", "mfa_challenged", "quarantined", "active"}
        if incident_id not in self._incidents:
            logger.warning("update_action: incident %s not found", incident_id)
            return False
        status = action if action in valid_statuses else action
        self._incidents[incident_id]["status"] = status
        logger.info("Incident %s status -> %s", incident_id, status)
        return True


# ---------------------------------------------------------------------------
# B. EmailDispatcher
# ---------------------------------------------------------------------------

_SEVERITY_COLOR = {
    "CRITICAL": "#e74c3c",
    "HIGH":     "#e67e22",
    "WARNING":  "#f1c40f",
    "SAFE":     "#2ecc71",
}

class EmailDispatcher:
    def __init__(self, smtp_host: str, smtp_port: int, sender_email: str,
                 sender_password: str, recipient_email: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email
        self.last_message = ""

    def send_alert(self, incident: dict) -> bool:
        try:
            severity = incident.get("severity", "UNKNOWN")
            color = _SEVERITY_COLOR.get(severity, "#95a5a6")

            subject = (
                f"[AdvGuard] {severity} ALERT - "
                f"Adversarial Evasion Detected #{incident.get('id', 'N/A')}"
            )

            cpp_summary = str(incident.get("cpp_report", ""))[:300]
            brief = incident.get("forensic_brief") or generate_forensic_brief(incident)
            exec_summary_html = brief.get("executive_summary", "")

            html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d1117;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#161b22;border-radius:12px;border:1px solid #30363d;overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:{color};padding:20px 32px;">
            <h1 style="margin:0;color:#fff;font-size:22px;letter-spacing:1px;">
              &#x26A0; AdvGuard — {severity} Alert
            </h1>
            <p style="margin:4px 0 0;color:rgba(255,255,255,0.8);font-size:13px;">
              Incident #{incident.get('id','N/A')} &bull; {incident.get('timestamp','N/A')} UTC
            </p>
          </td>
        </tr>
        <!-- Autonomous Forensic Intelligence Brief -->
        <tr>
          <td style="padding:20px 32px 0;">
            <div style="background:#0d1117;border:1px solid #30363d;border-left:4px solid {color};border-radius:6px;padding:14px 16px;color:#c9d1d9;font-size:13px;line-height:1.5;">
              <strong style="color:#58a6ff;font-size:13px;display:block;margin-bottom:6px;">🧠 Autonomous AI Forensic Brief:</strong>
              {exec_summary_html}
            </div>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:28px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border-collapse:collapse;color:#c9d1d9;font-size:14px;">
              <tr style="border-bottom:1px solid #21262d;">
                <td style="padding:10px 8px;color:#8b949e;width:40%;">Severity</td>
                <td style="padding:10px 8px;">
                  <span style="background:{color};color:#fff;padding:3px 10px;
                               border-radius:4px;font-weight:600;font-size:12px;">
                    {severity}
                  </span>
                </td>
              </tr>
              <tr style="border-bottom:1px solid #21262d;">
                <td style="padding:10px 8px;color:#8b949e;">Threat Score</td>
                <td style="padding:10px 8px;font-weight:600;">{incident.get('threat_score', 0):.4f}</td>
              </tr>
              <tr style="border-bottom:1px solid #21262d;">
                <td style="padding:10px 8px;color:#8b949e;">Epsilon (perturbation)</td>
                <td style="padding:10px 8px;">{incident.get('epsilon', 'N/A')}</td>
              </tr>
              <tr style="border-bottom:1px solid #21262d;">
                <td style="padding:10px 8px;color:#8b949e;">Fraud Ratio</td>
                <td style="padding:10px 8px;">{incident.get('fraud_ratio', 0):.2%}</td>
              </tr>
              <tr style="border-bottom:1px solid #21262d;">
                <td style="padding:10px 8px;color:#8b949e;">ML Prediction</td>
                <td style="padding:10px 8px;">{incident.get('ml_prediction', 'N/A')}</td>
              </tr>
              <tr style="border-bottom:1px solid #21262d;">
                <td style="padding:10px 8px;color:#8b949e;">Steps Taken</td>
                <td style="padding:10px 8px;">{incident.get('steps_taken', 'N/A')}</td>
              </tr>
              <tr style="border-bottom:1px solid #21262d;">
                <td style="padding:10px 8px;color:#8b949e;">Status</td>
                <td style="padding:10px 8px;">{incident.get('status', 'active')}</td>
              </tr>
              <tr>
                <td style="padding:10px 8px;color:#8b949e;vertical-align:top;">C++ Report</td>
                <td style="padding:10px 8px;">
                  <pre style="margin:0;background:#0d1117;border:1px solid #30363d;
                              border-radius:6px;padding:10px;color:#79c0ff;
                              font-size:12px;white-space:pre-wrap;word-break:break-word;">
{cpp_summary}</pre>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:16px 32px;border-top:1px solid #21262d;">
            <p style="margin:0;color:#484f58;font-size:11px;text-align:center;">
              AdvGuard Adversarial Evasion Detection System &bull; Automated Alert
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

            # Always save preview HTML file for immediate browser inspection
            preview_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latest_email_preview.html")
            try:
                with open(preview_path, "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                logger.warning("Could not write preview HTML: %s", e)

            # Verify sender credentials
            if not self.sender_email or not self.sender_password:
                self.last_message = "Sender Email & 16-character App Password are required to deliver real emails to your inbox. Please enter them in Settings."
                logger.warning(self.last_message)
                return False

            recipient = self.recipient_email or self.sender_email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient
            msg.attach(MIMEText(html, "html"))

            port = int(self.smtp_port) if self.smtp_port else 465
            if port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, port, context=context, timeout=12) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, recipient, msg.as_string())
            else:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_host, port, timeout=12) as server:
                    server.starttls(context=context)
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, recipient, msg.as_string())

            self.last_message = f"Real email alert successfully delivered to {recipient}!"
            logger.info(self.last_message)
            return True

        except smtplib.SMTPAuthenticationError as auth_err:
            self.last_message = "Gmail Auth Failed: Google blocks regular passwords. Generate a 16-character App Password at myaccount.google.com/apppasswords and enter it in Settings."
            logger.error("SMTP Auth Error: %s", auth_err)
            return False
        except Exception as exc:
            self.last_message = f"SMTP transmission error: {str(exc)}"
            logger.error("EmailDispatcher.send_alert failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# C. WebhookDispatcher
# ---------------------------------------------------------------------------

_DISCORD_COLORS = {
    "CRITICAL": 15158332,   # red
    "HIGH":     16744272,   # orange
    "WARNING":  16776960,   # yellow
}

class WebhookDispatcher:
    def send_discord_alert(self, webhook_url: str, incident: dict) -> bool:
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False
        try:
            severity = incident.get("severity", "SAFE")
            color = _DISCORD_COLORS.get(severity, 3066993)  # default green for SAFE
            brief = incident.get("forensic_brief") or generate_forensic_brief(incident)
            exec_brief_text = brief.get("executive_summary", "")[:350]
            
            payload = {
                "username": "AdvGuard SOC",
                "embeds": [{
                    "title": f"🚨 {severity} — Adversarial Evasion Intercepted",
                    "description": f"**Incident:** `{incident.get('id', 'N/A')}` | **Attack:** `{incident.get('attack_method', 'FGSM')}`",
                    "color": color,
                    "fields": [
                        {"name": "🧠 Executive Forensic Advisory", "value": exec_brief_text, "inline": False},
                        {"name": "Severity",      "value": severity,                                     "inline": True},
                        {"name": "Threat Score",  "value": f"`{incident.get('threat_score', 0):.4f}`",   "inline": True},
                        {"name": "Fraud Ratio",   "value": f"{incident.get('fraud_ratio', 0):.2%}",      "inline": True},
                        {"name": "ML Prediction", "value": str(incident.get("ml_prediction", "N/A")),   "inline": True},
                        {"name": "Timestamp",     "value": str(incident.get("timestamp", "N/A")),        "inline": False},
                    ],
                    "footer": {"text": "AdvGuard FinSec Intelligence Engine"},
                }]
            }
            resp = requests.post(webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Discord alert sent for incident %s", incident.get("id"))
            return True
        except Exception as exc:
            logger.error("WebhookDispatcher.send_discord_alert failed: %s", exc)
            return False

    def send_telegram_alert(self, bot_token: str, chat_id: str, incident: dict) -> bool:
        if not bot_token or not chat_id:
            logger.warning("Telegram bot_token or chat_id not configured")
            return False
        try:
            severity = incident.get("severity", "SAFE")
            text = (
                f"🚨 *AdvGuard {severity} Alert*\n\n"
                f"*Incident ID:* `{incident.get('id', 'N/A')}`\n"
                f"*Threat Score:* `{incident.get('threat_score', 0):.4f}`\n"
                f"*Epsilon:* `{incident.get('epsilon', 'N/A')}`\n"
                f"*Fraud Ratio:* `{incident.get('fraud_ratio', 0):.2%}`\n"
                f"*ML Prediction:* `{incident.get('ml_prediction', 'N/A')}`\n"
                f"*Steps Taken:* `{incident.get('steps_taken', 'N/A')}`\n"
                f"*Timestamp:* `{incident.get('timestamp', 'N/A')}`\n"
                f"*Status:* `{incident.get('status', 'active')}`"
            )
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Telegram alert sent for incident %s", incident.get("id"))
            return True
        except Exception as exc:
            logger.error("WebhookDispatcher.send_telegram_alert failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# D. NtfyDispatcher — Zero-Config Instant Mobile Push & Email Delivery
# ---------------------------------------------------------------------------

class NtfyDispatcher:
    def send_notification(self, topic: str = "advguard-alerts", title: str = "AdvGuard Security Alert",
                          message: str = "", priority: str = "urgent", tags: str = "shield,warning",
                          click_url: str = None, email: str = None) -> tuple:
        """
        Sends an instant push notification via ntfy.sh (zero-config, works on all devices).
        If email is provided, ntfy also forwards an email to that address!
        """
        clean_topic = re.sub(r'[^a-zA-Z0-9_-]', '', topic.strip()) or "advguard-alerts"
        url = f"https://ntfy.sh/{clean_topic}"
        headers = {
            "Title": title,
            "Priority": priority,
            "Tags": tags,
        }
        if click_url:
            headers["Click"] = click_url
        if email and "@" in email:
            headers["Email"] = email.strip()

        try:
            resp = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return True, {
                    "id": data.get("id"),
                    "topic": clean_topic,
                    "view_url": f"https://ntfy.sh/{clean_topic}",
                    "message": "Notification dispatched successfully!",
                    "email_forwarded": bool(email and "@" in email)
                }
            return False, {"error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return False, {"error": str(e)}

    def send_incident_alert(self, incident: dict, topic: str = "advguard-alerts", email: str = None) -> bool:
        severity = incident.get("severity", "CRITICAL")
        threat_score = incident.get("threat_score", 0.0)
        attack_method = incident.get("attack_method", "FGSM")
        
        title = f"🚨 AdvGuard {severity} — {attack_method} Intercepted"
        body = (
            f"Adversarial Evasion Blocked by AdvGuard KD-Tree!\n"
            f"• Incident ID: #{incident.get('id', 'N/A')}\n"
            f"• Threat Score: {threat_score:.4f}\n"
            f"• Attack: {attack_method} (ε={incident.get('epsilon', 0.05)})\n"
            f"• Neighborhood Fraud Ratio: {incident.get('fraud_ratio', 0):.1%}\n"
            f"• ML Model Verdict: {incident.get('ml_prediction', 'Safe (Fooled)')}\n"
            f"• AdvGuard Action: OVERRIDDEN & BLOCKED"
        )
        tags = "warning,shield" if severity == "CRITICAL" else "information_source,shield"
        prio = "urgent" if severity == "CRITICAL" else "high"
        
        ok, res = self.send_notification(topic=topic, title=title, message=body, priority=prio, tags=tags, email=email)
        return ok


# ---------------------------------------------------------------------------
# E. NotificationConfig — loads from environment with safe defaults
# ---------------------------------------------------------------------------

@dataclass
class NotificationConfig:
    ntfy_enabled: bool = field(default_factory=lambda: True)
    ntfy_topic: str = field(default_factory=lambda: "advguard-alerts")
    email_enabled: bool = field(default_factory=lambda: os.getenv("EMAIL_ENABLED", "false").lower() == "true")
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "465")))
    sender_email: str = field(default_factory=lambda: os.getenv("SENDER_EMAIL", ""))
    sender_password: str = field(default_factory=lambda: os.getenv("SENDER_PASSWORD", ""))
    recipient_email: str = field(default_factory=lambda: os.getenv("RECIPIENT_EMAIL", ""))
    discord_enabled: bool = field(default_factory=lambda: os.getenv("DISCORD_ENABLED", "false").lower() == "true")
    discord_webhook_url: str = field(default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL", ""))
    telegram_enabled: bool = field(default_factory=lambda: os.getenv("TELEGRAM_ENABLED", "false").lower() == "true")
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))


# ---------------------------------------------------------------------------
# F. Global instances
# ---------------------------------------------------------------------------

incident_manager = IncidentManager()
notification_config = NotificationConfig()

email_dispatcher = EmailDispatcher(
    smtp_host=notification_config.smtp_host,
    smtp_port=notification_config.smtp_port,
    sender_email=notification_config.sender_email,
    sender_password=notification_config.sender_password,
    recipient_email=notification_config.recipient_email,
)

webhook_dispatcher = WebhookDispatcher()
ntfy_dispatcher = NtfyDispatcher()
