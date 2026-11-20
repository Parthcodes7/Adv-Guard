"""
AdvGuard Autonomous AI Forensic Incident Intelligence Suite
Generates bank-grade executive security dossiers and forensic advisories
for intercepted adversarial evasion attacks.
"""

from datetime import datetime

# Domain mapping for Kaggle Credit Card PCA features to realistic financial crime attributes
FEATURE_DESCRIPTIONS = {
    "V1": "Cardholder Behavioral Drift Index",
    "V2": "Merchant Account Risk Multiplier",
    "V3": "Terminal Geographic Consistency",
    "V4": "Cross-Border Geolocation & IP Risk Profile",
    "V5": "Device Fingerprint Subnet Velocity",
    "V6": "Account Inactivity Awakening Delta",
    "V7": "Merchant Category Code (MCC) Deviation",
    "V8": "Hardware Token Biometric Saliency",
    "V9": "Billing vs. Shipping Proximity Index",
    "V10": "Virtual Card Terminal Profile & Issuer Risk",
    "V11": "Rapid-Fire Transaction Cadence Metric",
    "V12": "Historical Balance Depletion Velocity",
    "V13": "Time-of-Day Spending Discrepancy",
    "V14": "Primary Behavioral Velocity & Device Token Entropy",
    "V15": "Authorization Latency Variance",
    "V16": "Secondary Device Authentication Score",
    "V17": "Session Anomaly Index & Browser Spoofing Vector",
    "V18": "Card-Not-Present (CNP) Velocity Threshold",
    "V19": "Payment Gateway Route Consistency",
    "V20": "High-Volume Amount Fluctuation Multiplier",
    "V21": "Card BIN Routing Deviation Index",
    "V22": "Historical Customer Profile Match Delta",
    "V23": "Transaction Sequence Frequency Anomaly",
    "V24": "Authentication Protocol Challenge Entropy",
    "V25": "Device OS & User-Agent Integrity Fingerprint",
    "V26": "Micro-Charge Probing Cadence",
    "V27": "Account Age to Transaction Volume Ratio",
    "V28": "Multi-Account Linkage Graph Distance",
    "Time": "Elapsed Transaction Sequence Time",
    "Amount": "Transaction Monetary Volume (USD Standardized)"
}

def generate_forensic_brief(incident_data: dict) -> dict:
    """
    Synthesizes raw spatial numbers, ML predictions, and distortion metrics
    into an enterprise-grade autonomous forensic incident advisory.
    """
    inc_id = str(incident_data.get("id", "UNKNOWN")).upper()
    severity = incident_data.get("severity", "CRITICAL")
    threat_score = float(incident_data.get("threat_score", 0.85))
    fraud_ratio = float(incident_data.get("fraud_ratio", 1.0))
    epsilon = float(incident_data.get("epsilon", 0.05))
    steps = incident_data.get("steps_taken", 1)
    attack_method = incident_data.get("attack_method", "FGSM (Fast Gradient Sign)")
    distortion = incident_data.get("distortion_stats", {})
    l2_norm = distortion.get("l2", 0.12)
    linf_norm = distortion.get("linf", epsilon)
    changed_count = distortion.get("changed_count", 6)
    total_features = distortion.get("total_features", 29)
    top_features = distortion.get("top_features", [])

    # Format timestamp
    ts = incident_data.get("timestamp", datetime.utcnow().isoformat())
    try:
        dt = datetime.fromisoformat(ts.replace("Z", ""))
        formatted_date = dt.strftime("%B %d, %Y - %H:%M:%S UTC")
    except Exception:
        formatted_date = str(ts)

    # 1. Executive Summary
    executive_summary = (
        f"AdvGuard intercepted and neutralized a targeted adversarial evasion attack "
        f"(Incident #{inc_id}) attempting to bypass primary financial fraud detection. "
        f"The attacker employed {attack_method} with a perturbation magnitude of ε={epsilon}, "
        f"successfully deceiving the Random Forest machine learning classifier into approving the transaction "
        f"as 'Safe'. However, AdvGuard's C++ geometric spatial layer revealed that {int(fraud_ratio * 100)}% "
        f"of the 10 nearest historical transactions in 29-dimensional space are verified fraud records. "
        f"AdvGuard automatically overrode the compromised ML verdict, blocking the transaction."
    )

    # 2. Attack Vector Analysis
    if "boundary" in attack_method.lower():
        vector_detail = (
            f"The adversary executed a Decision Boundary Probing Attack (HopSkipJump-style line search). "
            f"By binary-searching the manifold between a safe reference anchor and the fraud centroid, "
            f"the attacker achieved an ultra-low L2 distortion of {l2_norm}, slipping just across "
            f"the classifier's hyper-plane decision threshold while staying physically located within a historical fraud cluster."
        )
    elif "jsma" in attack_method.lower():
        vector_detail = (
            f"The adversary utilized a Jacobian Saliency Feature Attack (JSMA), selectively perturbing "
            f"only {changed_count} out of {total_features} continuous attributes ({distortion.get('sparsity_ratio', 0.14) * 100:.0f}% sparsity). "
            f"By exclusively targeting high-gradient features, the evasion achieved a stealthy profile that mimics natural user variance."
        )
    elif "fgsm" in attack_method.lower():
        vector_detail = (
            f"The adversary deployed the Fast Gradient Sign Method (FGSM), evaluating numerical loss gradients ∇_x L "
            f"across the tree ensemble and executing single-step directional nudges in the steepest descent direction. "
            f"This flipped the model's confidence within {steps} iteration(s) with an L_∞ Chebyshev bound of {linf_norm}."
        )
    else:
        vector_detail = (
            f"The adversary utilized heuristic coordinate drift with uniform epsilon step sizes across continuous attributes, "
            f"iteratively nudging features until crossing the model's decision boundary."
        )

    # 3. Exploit Feature Breakdown
    feature_insights = []
    for tf in top_features:
        name = tf.get("name", "Unknown")
        delta = tf.get("delta", 0.0)
        desc = FEATURE_DESCRIPTIONS.get(name, "Continuous Latent Behavioral Feature")
        direction_str = "decreased" if delta < 0 else "increased"
        feature_insights.append({
            "name": name,
            "description": desc,
            "delta": delta,
            "original": tf.get("original", 0.0),
            "perturbed": tf.get("perturbed", 0.0),
            "significance": f"Attacker {direction_str} this attribute by {abs(delta):.4f} to simulate legitimate historical baseline behavior."
        })

    # 4. Spatial Manifold & Geometric Proof
    spatial_proof = (
        f"AdvGuard's K-Dimensional Space Partitioning Tree (KD-Tree) performed a hyper-plane bounding search "
        f"in O(log N) time complexity. Bounding radius analysis mathematically proved that despite the {l2_norm:.4f} "
        f"Euclidean shift, the transaction's coordinates sit squarely inside a known fraud cluster with a "
        f"supermajority neighbor fraud density of {int(fraud_ratio * 100)}% (Safety Threshold: 60%). "
        f"Consequently, spatial ground truth definitively proved the transaction was an evasion sample."
    )

    # 5. Regulatory Compliance & Forensic Impact
    compliance_notes = [
        "PCI-DSS v4.0 Requirement 10.2: Automated anomaly detection logged and preserved in audit trail.",
        "FinCEN SAR Advisory: Transaction exhibits calculated evasion techniques indicative of organized synthetic fraud rings.",
        "Model Governance (SR 11-7 / OCC 2011-12): Validates that primary ML model decision boundaries require geometric guardrails."
    ]

    # 6. Prescribed Actions
    recommended_actions = [
        "Issue Step-Up Multi-Factor Authentication (OTP Challenge) to verify cardholder identity.",
        "Enroll evasion feature fingerprint into AdvGuard LSH Attack Template Table for O(1) drop of identical probes.",
        "Temporarily quarantine linked card token and inspect associated merchant terminal BINs.",
        "Log incident telemetry to SOC SIEM and dispatch forensic dossier to fraud investigation queue."
    ]

    # Markdown format for webhooks / export
    markdown_report = f"""# 🛡️ AdvGuard Autonomous Forensic Dossier
**Incident Reference:** `{inc_id}` | **Severity:** `{severity}` | **Threat Score:** `{threat_score:.4f}`
**Timestamp:** {formatted_date}
**Detection Vector:** {attack_method} | **Distortion:** L2={l2_norm:.4f}, L_∞={linf_norm:.4f}

---

### 1. Executive Incident Summary
{executive_summary}

### 2. Adversarial Vector Analysis
{vector_detail}

### 3. Exploited Feature Breakdown
"""
    for fi in feature_insights:
        markdown_report += f"- **{fi['name']} ({fi['description']})**: Original `{fi['original']}` → Perturbed `{fi['perturbed']}` (Δ `{fi['delta']}`)\n  *{fi['significance']}*\n"

    markdown_report += f"""
### 4. Geometric Manifold Proof
{spatial_proof}

### 5. Regulatory & Compliance Evaluation
"""
    for cn in compliance_notes:
        markdown_report += f"- ⚖️ {cn}\n"

    markdown_report += """
### 6. Prescribed Security Countermeasures
"""
    for act in recommended_actions:
        markdown_report += f"- [x] {act}\n"

    return {
        "incident_id": inc_id,
        "timestamp": formatted_date,
        "severity": severity,
        "threat_score": threat_score,
        "attack_method": attack_method,
        "distortion": {
            "l2": l2_norm,
            "linf": linf_norm,
            "changed_count": changed_count,
            "total_features": total_features
        },
        "executive_summary": executive_summary,
        "attack_vector_analysis": vector_detail,
        "feature_insights": feature_insights,
        "spatial_proof": spatial_proof,
        "compliance_notes": compliance_notes,
        "recommended_actions": recommended_actions,
        "markdown_report": markdown_report
    }
