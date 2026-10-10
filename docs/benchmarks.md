# Cartora Benchmarks

## Baseline (Pre-Optimization, Phase 0)
Measured using `scripts/bench.py` on a 10-message support conversation for user C1001.
| Metric | Average |
| :--- | :--- |
| **Prompt Tokens** | 614.9 tokens/req |
| **Completion Tokens** | 102.3 tokens/req |
| **Recall Latency** | 1299.4 ms |
| **LLM Gen Latency** | 1182.2 ms |
| **Retain Latency** | 3001.1 ms (blocking) |
| **Total Request Latency** | 5484.2 ms |

## Phase 1 Optimization
Implemented async retain, budget-capped recall, rule-based intent checks, and short-term context injection.

| Metric | Average |
| :--- | :--- |
| **Prompt Tokens** | 697.7 tokens/req (slightly higher due to keeping rolling context) |
| **Completion Tokens** | 59.5 tokens/req (shorter responses due to better context) |
| **Recall Latency** | 213.4 ms (Skipped via intent checks 70% of the time) |
| **LLM Gen Latency** | 1194.1 ms |
| **Retain Latency** | 204.1 ms (Non-blocking async dispatch) |
| **Total Request Latency** | 1615.2 ms (70.5% speedup!) |

## Phase 2 Optimization (Scalability)
Migrated to SQLite (WAL), added `gunicorn` with `gthread` workers, pinned requirements, configured `flask-limiter`, and added LLM fallback chains.

**Load Test (50 Concurrent Users, Mocked LLM)**
- **Total Time**: 0.45s
- **Success Rate**: 100% (No SQLite locking issues)
- **Error Rate**: 0%
- **P50 Latency**: ~35ms
- **P95 Latency**: ~45ms

*(Note: Load tests against real Groq endpoints without mocking yield ~40s latencies due to provider-side concurrency limits, which is expected. The rate limit configuration correctly limits 50 requests per hour per IP).*
