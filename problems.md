# Known Problems and Mitigations

## Problem 1: False Positives from AdvGuard (The "Unlucky Customer" Scenario)

**Description:**
A legitimate transaction coincidentally falls into a dense fraud cluster in the historical data space. The primary ML model correctly identifies it as "Safe", but the AdvGuard KD-Tree finds that a supermajority (e.g., 60%+) of the nearest neighbors are known frauds. Because it meets the threshold, AdvGuard overrides the ML model and blocks the transaction, resulting in a False Positive for a legitimate customer.

**Mitigation Strategies:**

1. **Increase the Supermajority Threshold:**
   Raise the threshold from 60% to 75% or 80%. This makes the system more conservative and ensures AdvGuard only overrides the ML model when there is overwhelming evidence that the transaction is in a fraud cluster.

2. **Increase 'K' (Look at More Neighbors):**
   Increase the number of nearest neighbors searched by the KD-Tree (e.g., from `k=10` to `k=30` or `k=50`). This smooths out local density spikes where a legitimate transaction might accidentally have a small pocket of frauds near it.

3. **Change the Distance Metric (Feature Weighting):**
   Instead of using standard Euclidean distance which treats all features equally, apply weights to prioritize critical features (e.g., Device ID, Account Age) or use a different metric like Mahalanobis distance. This can mathematically push legitimate transactions away from fraud clusters based on key trust features.

4. **Introduce "Friction" Instead of a Hard Block:**
   If the ML model says "Safe" but AdvGuard says "Fraud", treat it as a state of uncertainty. Instead of a hard `BLOCKED` status, issue a `CHALLENGE` status to trigger Multi-Factor Authentication (MFA) like SMS OTP. Legitimate customers can easily pass this, while attackers cannot.

5. **Add User-Specific History (UEBA):**
   Before allowing AdvGuard to block a transaction, verify if the transaction perfectly matches the specific customer's personal past behavior. If it's a known safe behavior for that individual, whitelist the transaction despite the global KD-Tree cluster.
