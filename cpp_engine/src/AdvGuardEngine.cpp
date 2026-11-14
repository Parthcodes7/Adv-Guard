#include "advguard.h"
#include <sstream>

AdvGuardEngine::AdvGuardEngine(int dims, int lsh_tables, int lsh_functions, double lsh_width, double threshold)
    : kd_tree(dims), lsh(lsh_tables, lsh_functions, dims, lsh_width), cache(1000), evasion_threshold(threshold) {}

std::string AdvGuardEngine::hashTransactionFeatures(const Transaction& t) const {
    std::stringstream ss;
    // Simple fast hashing based on first few features (or all)
    for (double f : t.features) {
        ss << f << "_";
    }
    return ss.str();
}

// =========================================================
// LRU Cache Implementation (Doubly Linked List + Hash Map)
// =========================================================
LRUCache::LRUCache(int cap) : capacity(cap) {
    head = new CacheNode("", false, "");
    tail = new CacheNode("", false, "");
    head->next = tail;
    tail->prev = head;
}

LRUCache::~LRUCache() {
    CacheNode* curr = head;
    while (curr) {
        CacheNode* nxt = curr->next;
        delete curr;
        curr = nxt;
    }
}

void LRUCache::removeNode(CacheNode* node) {
    CacheNode* prevNode = node->prev;
    CacheNode* nextNode = node->next;
    prevNode->next = nextNode;
    nextNode->prev = prevNode;
}

void LRUCache::addToHead(CacheNode* node) {
    node->prev = head;
    node->next = head->next;
    head->next->prev = node;
    head->next = node;
}

bool LRUCache::get(const std::string& key, bool& is_blocked, std::string& report) {
    if (cache_map.find(key) != cache_map.end()) {
        CacheNode* node = cache_map[key];
        removeNode(node);
        addToHead(node); // Move to most recently used
        is_blocked = node->is_blocked;
        report = node->report;
        return true;
    }
    return false;
}

void LRUCache::put(const std::string& key, bool is_blocked, const std::string& report) {
    if (cache_map.find(key) != cache_map.end()) {
        CacheNode* node = cache_map[key];
        node->is_blocked = is_blocked;
        node->report = report;
        removeNode(node);
        addToHead(node);
    } else {
        CacheNode* newNode = new CacheNode(key, is_blocked, report);
        cache_map[key] = newNode;
        addToHead(newNode);

        if (cache_map.size() > capacity) {
            // Evict Least Recently Used (tail->prev)
            CacheNode* lru = tail->prev;
            removeNode(lru);
            cache_map.erase(lru->key);
            delete lru;
        }
    }
}
// =========================================================

void AdvGuardEngine::loadHistoricalData(const std::vector<Transaction>& data) {
    for (const auto& t : data) {
        kd_tree.insert(t);
    }
}

void AdvGuardEngine::addAttackTemplate(const Transaction& attack_template) {
    lsh.addTransaction(attack_template);
}

bool AdvGuardEngine::evaluateTransaction(const Transaction& t, std::string& report) {
    std::string cache_key = hashTransactionFeatures(t);
    bool cached_blocked = false;
    
    // 0. Check LRU Cache (O(1) Time)
    if (cache.get(cache_key, cached_blocked, report)) {
        report = "INFO: LRU Cache Hit! Returning previous evaluation in O(1) time.\n" + report;
        return cached_blocked;
    }

    std::stringstream ss;
    
    // 1. Check LSH for known attack templates
    if (lsh.checkCollision(t)) {
        ss << "ALERT: High-speed LSH collision detected with known attack template.\n"
           << "Transaction " << t.id << " blocked in O(1) time.\n";
        report = ss.str();
        cache.put(cache_key, true, report); // Cache result
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
        cache.put(cache_key, true, report); // Cache result
        return true; // Blocked
    }
    
    ss << "SUCCESS: Transaction geometrically consistent with Safe cluster. Approved.\n";
    report = ss.str();
    cache.put(cache_key, false, report); // Cache result
    return false; // Approved
}
