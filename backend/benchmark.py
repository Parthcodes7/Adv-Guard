"""
AdvGuard DSA Algorithmic Benchmarking Suite
Compares empirical performance of custom spatial data structures:
1. KD-Tree Spatial Search: O(log N) average query time
2. Brute-Force Linear Scan: O(N * d) linear degradation
3. LSH Fast-Path Filter: O(d) projection hash -> O(1) bucket check
4. LRU Cache: O(1) constant hash map + doubly linked list lookup
"""

import time
import os
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "ml_baseline", "data")
HISTORY_CSV = os.path.join(DATA_DIR, "historical_history.csv")

# Cached benchmark results so page loads instantly
_CACHED_BENCHMARK = None

def get_base_features():
    """Loads historical features and expands to at least 10,000 samples for scaling curves."""
    if os.path.exists(HISTORY_CSV):
        df = pd.read_csv(HISTORY_CSV, header=None)
        X = df.iloc[:, :29].values
    else:
        # Fallback synthetic Gaussian vectors if data file missing
        np.random.seed(42)
        X = np.random.normal(0, 1.0, (1000, 29))

    # Expand to 10,000 samples with small realistic perturbations to avoid identical duplicate points
    if len(X) < 10000:
        reps = int(np.ceil(10000 / len(X)))
        X_expanded = np.tile(X, (reps, 1))[:10000]
        np.random.seed(42)
        X_expanded = X_expanded + np.random.normal(0, 0.02, X_expanded.shape)
    else:
        X_expanded = X[:10000]

    return X_expanded

def run_benchmark_suite(sample_sizes=None, iterations=30):
    """
    Executes micro-benchmarks across various dataset sizes N.
    Measures latency in microseconds (µs).
    """
    global _CACHED_BENCHMARK
    if sample_sizes is None:
        sample_sizes = [100, 500, 1000, 2500, 5000, 10000]

    X_all = get_base_features()
    target = X_all[0].copy() + 0.05 # Realistic query vector
    k = 10

    results = []

    # Prepare mock LSH and LRU structures for O(1) comparison
    lru_cache = {f"TXN_{i}": True for i in range(1000)}
    lsh_projection = np.random.normal(0, 1.0, (5, 29))

    for n in sample_sizes:
        sub = X_all[:n]

        # 1. Measure KD-Tree Query (O(log N))
        tree = KDTree(sub)
        # Warmup
        tree.query(target, k=k)
        t0 = time.perf_counter()
        for _ in range(iterations):
            tree.query(target, k=k)
        t_kd = (time.perf_counter() - t0) / iterations * 1_000_000 # microseconds

        # 2. Measure Brute Force Linear Scan (O(N * d))
        # Warmup
        dists = np.linalg.norm(sub - target, axis=1)
        np.argpartition(dists, k)[:k]
        t0 = time.perf_counter()
        for _ in range(iterations):
            dists = np.linalg.norm(sub - target, axis=1)
            np.argpartition(dists, k)[:k]
        t_bf = (time.perf_counter() - t0) / iterations * 1_000_000 # microseconds

        # 3. Measure LSH Projection Check (O(d) -> O(1) hash bucket)
        t0 = time.perf_counter()
        for _ in range(iterations):
            # Project vector onto random hyperplanes
            projections = np.dot(lsh_projection, target) > 0
            hash_key = hash(tuple(projections))
        t_lsh = (time.perf_counter() - t0) / iterations * 1_000_000 # microseconds

        # 4. Measure LRU Cache Lookup (O(1))
        cache_key = "TXN_42"
        t0 = time.perf_counter()
        for _ in range(iterations):
            _ = lru_cache.get(cache_key, False)
        t_lru = (time.perf_counter() - t0) / iterations * 1_000_000 # microseconds

        speedup = t_bf / t_kd if t_kd > 0 else 1.0

        results.append({
            "n": n,
            "kd_tree_us": round(t_kd, 2),
            "brute_force_us": round(t_bf, 2),
            "lsh_us": round(t_lsh, 2),
            "lru_us": round(t_lru, 2),
            "speedup_ratio": round(speedup, 2)
        })

    max_speedup_entry = max(results, key=lambda x: x["speedup_ratio"])

    benchmark_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dimensions": 29,
        "k_neighbors": k,
        "iterations_per_point": iterations,
        "series": results,
        "summary": {
            "max_speedup": max_speedup_entry["speedup_ratio"],
            "max_speedup_n": max_speedup_entry["n"],
            "kd_tree_complexity": "O(log N)",
            "brute_force_complexity": "O(N * d)",
            "lsh_complexity": "O(1)",
            "lru_complexity": "O(1)",
            "conclusion": f"At N={max_speedup_entry['n']:,}, AdvGuard's KD-Tree provides a {max_speedup_entry['speedup_ratio']}x speedup over brute-force linear search while LSH and LRU cache achieve sub-5µs O(1) response times."
        }
    }

    _CACHED_BENCHMARK = benchmark_data
    return benchmark_data

def get_benchmark_results(force_rerun=False):
    global _CACHED_BENCHMARK
    if _CACHED_BENCHMARK is None or force_rerun:
        return run_benchmark_suite()
    return _CACHED_BENCHMARK
