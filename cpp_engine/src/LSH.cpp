#include "advguard.h"
#include <random>
#include <cmath>
#include <sstream>

LSH::LSH(int tables, int functions, int dims, double width) 
    : num_hash_tables(tables), num_hash_functions(functions), dimensions(dims), bucket_width(width) 
{
    std::mt19937 gen(42); // Fixed seed for reproducibility in academic setting
    std::normal_distribution<double> norm_dist(0.0, 1.0);
    std::uniform_real_distribution<double> unif_dist(0.0, width);

    random_vectors.resize(tables);
    random_biases.resize(tables);

    for (int t = 0; t < tables; ++t) {
        random_vectors[t].resize(functions);
        random_biases[t].resize(functions);
        for (int f = 0; f < functions; ++f) {
            random_vectors[t][f].resize(dims);
            for (int d = 0; d < dims; ++d) {
                random_vectors[t][f][d] = norm_dist(gen);
            }
            random_biases[t][f] = unif_dist(gen);
        }
    }
}

LSH::~LSH() {}

std::vector<int> LSH::hashVector(const std::vector<double>& features, int table_index) const {
    std::vector<int> hashes(num_hash_functions);
    for (int f = 0; f < num_hash_functions; ++f) {
        double dot_product = 0.0;
        for (int d = 0; d < dimensions; ++d) {
            dot_product += features[d] * random_vectors[table_index][f][d];
        }
        hashes[f] = static_cast<int>(std::floor((dot_product + random_biases[table_index][f]) / bucket_width));
    }
    return hashes;
}

std::string LSH::hashToString(const std::vector<int>& hash_vals) const {
    std::stringstream ss;
    for (int h : hash_vals) {
        ss << h << "_";
    }
    return ss.str();
}

void LSH::addTransaction(const Transaction& t) {
    if (hash_tables.empty()) {
        hash_tables.resize(num_hash_tables);
    }

    for (int table = 0; table < num_hash_tables; ++table) {
        std::vector<int> hashes = hashVector(t.features, table);
        std::string bucket_id = hashToString(hashes);
        hash_tables[table][bucket_id].push_back(t);
    }
}

bool LSH::checkCollision(const Transaction& t) const {
    if (hash_tables.empty()) return false;

    for (int table = 0; table < num_hash_tables; ++table) {
        std::vector<int> hashes = hashVector(t.features, table);
        std::string bucket_id = hashToString(hashes);
        
        if (hash_tables[table].find(bucket_id) != hash_tables[table].end()) {
            return true;
        }
    }
    return false;
}
