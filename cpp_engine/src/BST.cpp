#include "advguard.h"

BST::BST() : root(nullptr) {}

BST::~BST() {
    clearRec(root);
}

void BST::clearRec(BSTNode* node) {
    if (node == nullptr) return;
    clearRec(node->left);
    clearRec(node->right);
    delete node;
}

BSTNode* BST::insertRec(BSTNode* node, const std::string& id, const Transaction& data) {
    if (node == nullptr) {
        return new BSTNode(id, data);
    }
    
    if (id < node->id) {
        node->left = insertRec(node->left, id, data);
    } else if (id > node->id) {
        node->right = insertRec(node->right, id, data);
    }
    // If id == node->id, we just ignore (no duplicates)
    return node;
}

void BST::insert(const Transaction& data) {
    root = insertRec(root, data.id, data);
}

BSTNode* BST::searchRec(BSTNode* node, const std::string& id) const {
    if (node == nullptr || node->id == id) {
        return node;
    }
    
    if (id < node->id) {
        return searchRec(node->left, id);
    } else {
        return searchRec(node->right, id);
    }
}

bool BST::search(const std::string& id, Transaction& out_data) const {
    BSTNode* result = searchRec(root, id);
    if (result != nullptr) {
        out_data = result->data;
        return true;
    }
    return false;
}
