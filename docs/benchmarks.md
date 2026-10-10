# Cartora Benchmarks

## Baseline (Pre-Optimization)

Measured using `scripts/bench.py` on a 10-message support conversation for user C1001.

| Metric | Average |
| :--- | :--- |
| **Prompt Tokens** | 614.9 tokens/req |
| **Completion Tokens** | 102.3 tokens/req |
| **Recall Latency** | 1299.4 ms |
| **LLM Gen Latency** | 1182.2 ms |
| **Retain Latency** | 3001.1 ms (blocking!) |
| **Total Request Latency** | 5484.2 ms |

*(Note: Data layer concurrency lock implemented and verified passing 30-worker simultaneous demo-checkouts without data loss).*
