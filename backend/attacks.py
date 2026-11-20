"""
AdvGuard Advanced Adversarial Attack Suite for Tabular ML Models
Implements:
1. FGSM (Fast Gradient Sign Method) via finite-difference gradient estimation
2. Decision Boundary Probing Attack (HopSkipJump / Binary Search Line Search)
3. Sparse Saliency Attack (JSMA-inspired: targets top sensitive features only)
4. Heuristic Directional Attack (Baseline)
"""

import numpy as np

FEATURE_NAMES = [
    "Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9",
    "V10", "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19",
    "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28"
]

def analyze_perturbation(original, perturbed):
    """Calculates L1, L2, Linf norms and identifies top perturbed features."""
    diff = perturbed - original
    l1 = float(np.sum(np.abs(diff)))
    l2 = float(np.linalg.norm(diff))
    linf = float(np.max(np.abs(diff)))
    
    # Identify features with non-trivial change
    changed_indices = np.where(np.abs(diff) > 1e-4)[0]
    changed_count = int(len(changed_indices))
    
    # Sort by absolute delta
    sorted_indices = np.argsort(np.abs(diff))[::-1]
    top_features = []
    for idx in sorted_indices[:5]:
        if np.abs(diff[idx]) > 1e-4:
            feat_name = FEATURE_NAMES[idx] if idx < len(FEATURE_NAMES) else f"Feat_{idx}"
            top_features.append({
                "index": int(idx),
                "name": feat_name,
                "delta": round(float(diff[idx]), 4),
                "original": round(float(original[idx]), 4),
                "perturbed": round(float(perturbed[idx]), 4)
            })
            
    return {
        "l1": round(l1, 4),
        "l2": round(l2, 4),
        "linf": round(linf, 4),
        "changed_count": changed_count,
        "total_features": len(original),
        "sparsity_ratio": round(changed_count / len(original), 2),
        "top_features": top_features
    }

def fgsm_attack(model, fraud_transaction, safe_anchor=None, epsilon=0.05, max_steps=50):
    """
    Fast Gradient Sign Method (FGSM) for tabular models.
    Computes numerical gradient of P(fraud | x) and steps in the direction of steepest descent.
    """
    x = fraud_transaction.copy()
    n_features = len(x)
    probe_delta = max(0.04, epsilon)
    
    for step in range(max_steps):
        # Estimate gradient of fraud probability w.r.t each feature
        grad = np.zeros(n_features)
        curr_prob = model.predict_proba([x])[0][1]
        
        for i in range(n_features):
            x_plus = x.copy()
            x_plus[i] += probe_delta
            p_plus = model.predict_proba([x_plus])[0][1]
            grad[i] = (p_plus - curr_prob) / probe_delta
            
        if np.all(np.abs(grad) < 1e-5):
            # Gradient plateau fallback: step along vector toward safe centroid
            if safe_anchor is not None:
                direction = np.sign(safe_anchor - x)
            else:
                direction = -np.sign(x)
        else:
            # Gradient descent: step in direction that decreases fraud probability
            direction = -np.sign(grad)
            
        x += epsilon * direction
        
        if model.predict([x])[0] == 0:
            return x, step + 1, True
            
    final_pred = model.predict([x])[0]
    return x, max_steps, (final_pred == 0)

def boundary_attack(model, fraud_transaction, safe_anchor, max_iterations=30):
    """
    Decision Boundary Probing Attack.
    Performs binary search between the fraud sample and a safe reference centroid
    to find the critical decision threshold with minimal L2 perturbation.
    """
    low = 0.0
    high = 1.0
    best_alpha = 1.0
    
    # Binary search for boundary crossing
    for step in range(max_iterations):
        mid = (low + high) / 2.0
        candidate = (1.0 - mid) * fraud_transaction + mid * safe_anchor
        pred = model.predict([candidate])[0]
        
        if pred == 0:
            best_alpha = mid
            # Try to get closer to the original fraud sample
            high = mid
        else:
            low = mid
            
    # Point lying just across the boundary into the safe classification space
    boundary_sample = (1.0 - best_alpha) * fraud_transaction + best_alpha * safe_anchor
    if np.allclose(boundary_sample, fraud_transaction, atol=1e-5):
        boundary_sample += 0.01 * (safe_anchor - fraud_transaction)
    final_pred = model.predict([boundary_sample])[0]
    
    return boundary_sample, max_iterations, (final_pred == 0)

def jsma_sparse_attack(model, fraud_transaction, safe_anchor=None, epsilon=0.08, max_features=4):
    """
    Sparse Feature Saliency Attack (JSMA-inspired).
    Computes sensitivity of all features and perturbs ONLY the top sensitive features,
    leaving the remaining 85%+ features completely unmodified (high sparsity).
    """
    x = fraud_transaction.copy()
    n_features = len(x)
    probe_delta = max(0.04, epsilon)
    
    # Evaluate feature sensitivity: |dP / dx_i|
    sensitivities = []
    base_prob = model.predict_proba([x])[0][1]
    
    for i in range(n_features):
        x_plus = x.copy()
        x_plus[i] += probe_delta
        p_plus = model.predict_proba([x_plus])[0][1]
        diff = abs(p_plus - base_prob)
        sensitivities.append((i, diff))
        
    sensitivities.sort(key=lambda s: s[1], reverse=True)
    top_feature_indices = [s[0] for s in sensitivities[:max_features]]
    
    # Iteratively nudge only the top features
    for step in range(30):
        for idx in top_feature_indices:
            if safe_anchor is not None:
                direction = np.sign(safe_anchor[idx] - x[idx]) if safe_anchor[idx] != x[idx] else -1.0
            else:
                direction = -np.sign(x[idx]) if x[idx] != 0 else -1.0
            x[idx] += epsilon * direction
            
        if model.predict([x])[0] == 0:
            return x, step + 1, True
            
    final_pred = model.predict([x])[0]
    return x, 30, (final_pred == 0)

def heuristic_attack(model, fraud_transaction, epsilon=0.1, max_steps=500):
    """Baseline heuristic directional perturbation."""
    perturbed = fraud_transaction.copy()
    for step in range(max_steps):
        prediction = model.predict([perturbed])[0]
        if prediction == 0:
            return perturbed, step + 1, True
        direction = -np.sign(perturbed)
        perturbed += epsilon * direction
    return perturbed, max_steps, False
