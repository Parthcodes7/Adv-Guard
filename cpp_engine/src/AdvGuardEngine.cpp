#include "advguard.h"
#include <sstream>

AdvGuardEngine::AdvGuardEngine(int dims, int lsh_tables, int lsh_functions, double lsh_width, double threshold)
    : kd_tree(dims), lsh(lsh_tables, lsh_functions, dims, lsh_width), evasion_threshold(threshold) {}

void AdvGuardEngine::loadHistoricalData(const std::vector<Transaction>& data) {
    for (const auto& t : data) {
        kd_tree.insert(t);
    }
}

void AdvGuardEngine::addAttackTemplate(const Transaction& attack_template) {
    lsh.addTransaction(attack_template);
}

bool AdvGuardEngine::evaluateTransaction(const Transaction& t, std::string& report) {
    std::stringstream ss;
    
    // 1. Check LSH for known attack templates
    if (lsh.checkCollision(t)) {
        ss << "ALERT: High-speed LSH collision detected with known attack template.\n"
           << "Transaction " << t.id << " blocked in O(1) time.\n";
        report = ss.str();
        return true; // Blocked
    }
    
    // 2. K-D Tree Neighborhood Search
    int k = 10;
    std::vector<Neighbor> neighbors = kd_tree.getNearestNeighbors(t, k);
    
    if (neighbors.empty()) {
        ss << "INFO: No spatial neighbors found. Allowing transaction.\n";
        report = ss.str();
        return false;
    }
    
    int fraud_count = 0;
    ss << "INFO: K-D Tree O(log N) Search Results:\n";
    for (size_t i = 0; i < neighbors.size(); ++i) {
        const Neighbor& n = neighbors[i];
        
        // Escape newlines and format cleanly for LLM consumption
        ss << "  Neighbor " << i+1 << " (ID: " << n.transaction->id 
           << ") | Distance: " << n.distance 
           << " | Label: " << (n.transaction->is_fraud ? "Fraud" : "Safe") << "\n";
        
        if (n.transaction->is_fraud) {
            fraud_count++;
        }
    }
    
    // 3. Discrepancy Detection
    double fraud_ratio = static_cast<double>(fraud_count) / neighbors.size();
    ss << "FRAUD NEIGHBOR RATIO: " << (fraud_ratio * 100.0) << "% (Threshold: " << (evasion_threshold * 100.0) << "%)\n";
    
    if (fraud_ratio >= evasion_threshold) {
        ss << "ALERT: Discrepancy engine triggered! ML model predicted Safe, but " 
           << (fraud_ratio * 100) << "% of spatial neighbors are historically Fraud.\n"
           << "Transaction " << t.id << " BLOCKED as probable Adversarial Evasion Attempt.\n";
        report = ss.str();
        return true; // Blocked
    }
    
    ss << "SUCCESS: Transaction geometrically consistent with Safe cluster. Approved.\n";
    report = ss.str();
    return false; // Approved
}
