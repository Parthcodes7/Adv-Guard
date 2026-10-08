# AdvGuard: Project Implementation Report

This document outlines the in-depth progress and technical implementation details of the **AdvGuard** project up to this point. This report can serve as a foundation for your final academic submission or presentation for your Data Structures and Algorithms (DSA) course.

---

## 1. The Core Problem & Threat Model
Modern financial fraud detection systems rely heavily on Machine Learning (e.g., Random Forests, Neural Networks). These models are highly vulnerable to **Adversarial Evasion Attacks**. 
In our threat model, an attacker takes a known fraudulent transaction and slightly perturbs its continuous features (e.g., tweaking the amount by a few cents, shifting the velocity counter). These tiny, mathematically calculated nudges push the transaction just across the ML model's decision boundary, causing the model to incorrectly classify it as "Safe".

## 2. AdvGuard Architecture
To defend against this, we designed **AdvGuard**: a high-speed, purely geometric defense layer written entirely in C++. It acts as a safety net that catches what the ML model misses. 

Instead of relying on another ML model (which could also be evaded), AdvGuard uses strict spatial proximity. If a transaction sits in a region of space surrounded entirely by historical fraud, AdvGuard will mathematically override the ML model and block the transaction.

## 3. Python ML Baseline & Attack Simulation (`ml_baseline/`)
We successfully scaffolded the vulnerable baseline.
*   **Data Generation:** We generate a dummy dataset of 1000 transactions with 10 continuous features, split into Legitimate and Fraudulent distributions.
*   **Vulnerable Model:** We trained a standard `RandomForestClassifier` which achieved 99% accuracy on the test set.
*   **White-Box Attack (`train_and_attack.py`):** We implemented an adversarial loop that takes a known Fraud transaction and nudges its features step-by-step toward the mean of the Safe class. 
*   **Success:** At step 9, the Random Forest model was successfully fooled into predicting `0.0 (Safe)`. The feature vector of this successful evasion attack is saved to `evasion_sample.csv` for the C++ engine to catch.

## 4. Custom C++ Data Structures (`cpp_engine/`)
To meet strict academic constraints, we avoided all external ML/DSA libraries (like FAISS or scikit-learn). All data structures feature manual memory management and raw pointers.

### A. Max-Heap (`MaxHeap.cpp`)
*   **Purpose:** To maintain the state of the $k$-nearest neighbors during the spatial search.
*   **Implementation:** An array-based (`std::vector`) binary Max-Heap. The root of the heap always holds the neighbor furthest from the target. If a closer neighbor is found, the root is popped and the new neighbor is pushed in $O(\log k)$ time via custom `heapifyUp` and `heapifyDown` algorithms.

### B. K-Dimensional Tree (`KDTree.cpp`)
*   **Purpose:** To perform an $O(\log N)$ spatial search for historical transactions.
*   **Implementation:** A fully custom recursive binary space partitioning tree. 
    *   **Nodes:** Uses raw `KDNode*` pointers.
    *   **Insertion:** Recursively cycles through the $N$ dimensions, splitting the space hyperplane by hyperplane.
    *   **Search:** Traverses to the leaf node, then unwinds the recursion, calculating Euclidean distances. It mathematically checks if the hypersphere of radius $r$ (the distance to the $k^{th}$ nearest neighbor in the Max-Heap) intersects the splitting plane. If so, it searches the opposite branch.
    *   **Memory:** Implements a custom destructor `clearRec` to manually `delete` all allocated node pointers, preventing memory leaks.

### C. Locality-Sensitive Hashing (`LSH.cpp`)
*   **Purpose:** An $O(1)$ fast-path filter to catch known, repetitive attack scripts (templates).
*   **Implementation:** Utilizes Random Projections. It generates standard normal (Gaussian) vectors and uniform biases to create hyperplanes. Transactions are hashed into integer buckets. If an incoming transaction lands in the same bucket as a known attack template, it is immediately flagged.

## 5. The Discrepancy Engine (`AdvGuardEngine.cpp`)
This is the core logic bridging the data structures:
1.  It checks the $O(1)$ **LSH** tables.
2.  If clear, it queries the $O(\log N)$ **KD-Tree** for the 10 closest historical neighbors.
3.  It calculates the `Fraud Ratio` of those neighbors.
4.  If the ML model claims the transaction is "Safe", but the KD-Tree proves that >60% of the closest historical transactions are "Fraud", AdvGuard **overrides** the ML model and blocks the transaction as a geometric evasion attempt.

*We successfully compiled this engine using `g++ -std=c++14`, and it correctly processed the adversarial sample!*

## 6. Interpretability via MCP (`mcp_server/`)
To provide human-readable context to Bank Managers, we integrated the **Model Context Protocol (MCP)**.
*   **Implementation:** We wrote `mcp_advguard.py` using the `FastMCP` framework.
*   **Functionality:** It exposes the C++ executable as a tool to a Local LLM (like Claude Desktop). The LLM can pass a CSV to the tool, execute the C++ geometric math, read the raw spatial distances outputted by standard out, and translate those raw vectors into a plain-English forensic security alert.

---

## Project Roadmap: Two-Phase Implementation

To ensure a smooth delivery and a strong presentation, the remainder of the project is divided into two phases:

### Phase 1: Working Prototype & Dashboard (50-60% target)
The primary goal of this phase is to build a highly visual, end-to-end working prototype that demonstrates the core DSA concepts working against the ML model.
1. **Real Data Integration:** Swap the dummy Gaussian data for a real-world dataset (e.g., Kaggle Credit Card Fraud CSV) to make the prototype realistic and robust.
2. **C++ & Python Integration:** Ensure the Python ML baseline can seamlessly interface with the compiled C++ `AdvGuardEngine` (e.g., via subprocess or bindings) to run the geometric analysis pipeline automatically.
3. **Interactive Dashboard:** Build a sleek web dashboard (using **Streamlit**) to provide a visual interface for the prototype. The dashboard will:
    *   Show the original transactions and feature distributions.
    *   Show the adversarial attack successfully fooling the Random Forest.
    *   Visually demonstrate AdvGuard stepping in to block the transaction based on spatial proximity.

### Phase 2: Advanced Features & LLM Integration (Remaining 40%)
Once the Phase 1 prototype is complete, the focus shifts to advanced features, code optimization, and interpretability.
1. **MCP & LLM Server:** Finalize the `mcp_server` (`mcp_advguard.py`) so a Local LLM (like Claude Desktop) can read the C++ geometric outputs and generate human-readable security forensic reports, explaining exactly *why* a transaction was blocked.
2. **Benchmarking & Analytics:** Add `std::chrono` timers in the C++ engine to benchmark the algorithms and generate charts proving the $O(\log N)$ time complexity of the custom KD-Tree for the final presentation.
3. **Advanced Tweaks:** Add additional DSA optimizations, tune the LSH hashing for specific attack vectors, or implement more complex adversarial attacks in the baseline.
