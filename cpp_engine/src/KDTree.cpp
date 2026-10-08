#include "advguard.h"
#include <cmath>
#include <limits>
#include <algorithm>

KDTree::KDTree(int dims) : root(nullptr), dimensions(dims) {}

KDTree::~KDTree() {
    clearRec(root);
}

void KDTree::clearRec(KDNode* node) {
    if (node) {
        clearRec(node->left);
        clearRec(node->right);
        delete node;
    }
}

KDNode* KDTree::insertRec(KDNode* node, const Transaction& data, int depth) {
    if (node == nullptr) {
        int dim = depth % dimensions;
        return new KDNode(data, dim);
    }

    int dim = node->split_dimension;
    if (data.features[dim] < node->data.features[dim]) {
        node->left = insertRec(node->left, data, depth + 1);
    } else {
        node->right = insertRec(node->right, data, depth + 1);
    }
    return node;
}

void KDTree::insert(const Transaction& data) {
    root = insertRec(root, data, 0);
}

static double calculateDistance(const std::vector<double>& a, const std::vector<double>& b) {
    double sum = 0.0;
    for (size_t i = 0; i < a.size() && i < b.size(); ++i) {
        double diff = a[i] - b[i];
        sum += diff * diff;
    }
    return std::sqrt(sum);
}

void KDTree::nearestNeighborRec(KDNode* node, const Transaction& target, int depth, MaxHeap& max_heap) {
    if (node == nullptr) return;

    double dist = calculateDistance(node->data.features, target.features);

    if (node->data.id != target.id) {
        max_heap.push({dist, &(node->data)});
    }

    int dim = node->split_dimension;
    double axis_dist = target.features[dim] - node->data.features[dim];

    KDNode* first = (axis_dist < 0) ? node->left : node->right;
    KDNode* second = (axis_dist < 0) ? node->right : node->left;

    nearestNeighborRec(first, target, depth + 1, max_heap);

    if (!max_heap.isFull() || std::abs(axis_dist) < max_heap.top().distance) {
        nearestNeighborRec(second, target, depth + 1, max_heap);
    }
}

std::vector<Neighbor> KDTree::getNearestNeighbors(const Transaction& target, int k) {
    MaxHeap max_heap(k);
    nearestNeighborRec(root, target, 0, max_heap);
    
    std::vector<Neighbor> neighbors = max_heap.getElements();
    std::sort(neighbors.begin(), neighbors.end(), [](const Neighbor& a, const Neighbor& b) {
        return a.distance < b.distance;
    });
    return neighbors;
}
