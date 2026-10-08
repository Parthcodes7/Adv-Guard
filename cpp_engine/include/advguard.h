#ifndef ADVGUARD_H
#define ADVGUARD_H

#include <vector>
#include <string>
#include <unordered_map>

// Core transaction representation
struct Transaction {
    std::string id;
    std::vector<double> features;
    bool is_fraud; // Ground truth or expert label
};

// --- K-D Tree Structures ---
struct KDNode {
    Transaction data;
    int split_dimension;
    KDNode* left;
    KDNode* right;

    KDNode(const Transaction& t, int dim) : data(t), split_dimension(dim), left(nullptr), right(nullptr) {}
};

struct Neighbor {
    double distance;
    const Transaction* transaction;
    
    bool operator<(const Neighbor& other) const {
        return distance < other.distance;
    }
};

class MaxHeap {
private:
    std::vector<Neighbor> heap;
    int max_size;

    void heapifyUp(int index);
    void heapifyDown(int index);

public:
    MaxHeap(int k);
    void push(const Neighbor& neighbor);
    const Neighbor& top() const;
    void pop();
    bool isFull() const;
    int size() const;
    std::vector<Neighbor> getElements() const;
};

class KDTree {
private:
    KDNode* root;
    int dimensions;

    KDNode* insertRec(KDNode* node, const Transaction& data, int depth);
    void nearestNeighborRec(KDNode* node, const Transaction& target, int depth, MaxHeap& max_heap);
    void clearRec(KDNode* node);

public:
    KDTree(int dims);
    ~KDTree();

    void insert(const Transaction& data);
    std::vector<Neighbor> getNearestNeighbors(const Transaction& target, int k);
};

// --- Locality-Sensitive Hashing (LSH) ---
class LSH {
private:
    int num_hash_tables;
    int num_hash_functions;
    int dimensions;
    double bucket_width;
    
    std::vector<std::vector<std::vector<double>>> random_vectors;
    std::vector<std::vector<double>> random_biases;
    std::vector<std::unordered_map<std::string, std::vector<Transaction>>> hash_tables;
    
    std::vector<int> hashVector(const std::vector<double>& features, int table_index) const;
    std::string hashToString(const std::vector<int>& hash_vals) const;

public:
    LSH(int tables, int functions, int dims, double width);
    ~LSH();

    void addTransaction(const Transaction& t);
    bool checkCollision(const Transaction& t) const;
};

// --- Core AdvGuard Discrepancy Engine ---
class AdvGuardEngine {
private:
    KDTree kd_tree;
    LSH lsh;
    double evasion_threshold;

public:
    AdvGuardEngine(int dims, int lsh_tables, int lsh_functions, double lsh_width, double threshold = 0.6);
    
    void loadHistoricalData(const std::vector<Transaction>& data);
    void addAttackTemplate(const Transaction& attack_template);
    bool evaluateTransaction(const Transaction& t, std::string& report);
};

#endif // ADVGUARD_H
