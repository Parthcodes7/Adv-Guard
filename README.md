# AdvGuard

AdvGuard is a high-speed, real-time C++ defense layer designed to detect and block adversarial evasion attacks on financial fraud detection machine learning models. 

This project was built for a Data Structures and Algorithms (DSA) academic class. It restricts external ML libraries (like FAISS) and implements custom manual memory management, Locality-Sensitive Hashing (LSH), and K-D Trees from scratch.

## Project Structure
- `cpp_engine/`: The core C++ data structures (KD-Tree, Max-Heap, LSH) and discrepancy detection logic.
- `ml_baseline/`: The Python script (`train_and_attack.py`) that trains a vulnerable Random Forest model and generates adversarial evasion transactions.
- `mcp_server/`: The Model Context Protocol (MCP) server that exposes the C++ geometric outputs to a local LLM for generating human-readable audit reports.

## How to Run

1. **Train Model & Generate Evasion Attack (Python):**
   ```bash
   cd ml_baseline
   pip install numpy pandas scikit-learn joblib
   python train_and_attack.py
   ```
   *This will output `data/evasion_sample.csv`.*

2. **Compile the C++ Engine:**
   ```bash
   cd ../cpp_engine
   mkdir build
   cd build
   cmake ..
   cmake --build .
   ```
   *This builds the `advguard_engine` executable.*

3. **Run the MCP Server:**
   ```bash
   cd ../../mcp_server
   pip install mcp
   mcp dev mcp_advguard.py
   ```
   *You can now connect a Local LLM (like Claude Desktop or an MCP client) and ask it to analyze `../ml_baseline/data/evasion_sample.csv`.*

## Project Roadmap

This project is being implemented in two phases to ensure a robust presentation and a clear separation of core algorithms and advanced features:

### Phase 1: Prototype & Dashboard
- **Real Data Integration:** Incorporate real-world datasets (e.g., Kaggle Credit Card Fraud) into the ML baseline.
- **Integration:** Seamlessly link the Python baseline with the C++ AdvGuardEngine.
- **Dashboard:** Build an interactive Streamlit dashboard to visually demonstrate the ML evasion attack and the AdvGuard geometric defense.

### Phase 2: Advanced Features
- **MCP Integration:** Complete the LLM integration for generating human-readable forensic reports.
- **Benchmarking:** Add `std::chrono` timers to benchmark the $O(\log N)$ performance of the custom C++ KD-Tree.
- **Optimization:** Further algorithmic tuning and advanced attack simulations.
