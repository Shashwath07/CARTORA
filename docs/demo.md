# Cartora Demo Script for Judges

This guide walks you through the Cartora prototype to demonstrate our three core focus areas: **Token Optimization**, **Scalability**, and **Frustration-Aware Escalation**.

## Preparation
1. Ensure your `.env` contains valid `GROQ_API_KEY`, `HINDSIGHT_API_KEY`, and `FLASK_SECRET_KEY`.
2. Start the server using Gunicorn to demonstrate concurrency capability:
   ```bash
   gunicorn app:app --worker-class gthread --threads 4 --workers 2 --bind 0.0.0.0:5000
   ```
3. Open `http://localhost:5000` in your browser.

---

## 1. The Baseline: Smart Memory (Token Optimization)

**Goal:** Show how Cartora remembers users across sessions without wasting tokens.

1. **Login** as `maya.sharma@cartora.example` (Password: `CartoraDemo#1`).
2. Go to the **Assistant** tab.
3. Type: *"I bought earbuds recently. They aren't charging properly."*
4. **Point out the Telemetry Bar:**
   - Look at the bottom of the chat window. The UI displays **Recall**, **LLM**, and **Retain** latencies.
   - Note that **Retain is 0-1ms** because it fires asynchronously (fire-and-forget), whereas it would normally block the UI for 3 seconds.
   - Note the **Prompt Tokens**. We budget the prompt tightly and fence memories so we don't blow up the context window.
5. Close the browser tab entirely (or click Logout, then log back in) to simulate a new session.
6. Type: *"Did you figure out how to reset them?"*
   - *Observation:* The assistant instantly knows you are talking about the earbuds from the previous session because it fetched the outcome via Hindsight Cloud.
7. Type: *"What is my order status for the backpack?"*
   - *Observation:* The telemetry bar will show **0 Memories Used** and **0ms Recall Latency**. 
   - *Explain:* We use heuristic intent checking. Since the customer just asked a deterministic look-up question without continuity words (like "again", "still"), we skipped the Hindsight API entirely, saving 1.2s of latency and preserving tokens.

---

## 2. The Escalation Path (Frustration-Aware)

**Goal:** Show that Cartora automatically detects frustration and transitions to human support safely.

1. Continue in the same chat.
2. We will artificially trigger the rule-based frustration detector (which requires a score of 3).
3. Type: *"This is useless! I want to speak to a human manager right now."*
   - *Observation:* A yellow **⚠️ Case Escalated** banner appears instantly in the chat window.
4. **Explain the Architecture:** 
   - We did *not* use a costly LLM call for sentiment analysis. We used zero-token regex rules to detect the frustration spike.
   - Upon detection, we triggered a *single* ~300-token summarization call to the LLM to generate a clean "handoff brief".
5. Go to the **Cases** tab on the left.
   - You will see a newly generated "Escalation" case. Click on it to show the judges the clean JSON summary (Issue, Mood, Steps Tried) that the human agent will receive.
   - We never lie to the customer: the bot only claims to have contacted a human *after* this SQLite row is securely committed.

---

## 3. Scalability (Concurrency & Resilience)

**Goal:** Prove that the backend handles heavy load without dropping orders.

1. Keep the server running. Open a terminal.
2. Run the concurrent load test:
   ```bash
   python scripts/loadtest.py
   ```
3. **Explain to the Judges:**
   - In Phase 0, 30 concurrent checkouts resulted in 29 lost orders because of JSON-file race conditions. 
   - Now, we are hitting the backend with **50 concurrent users**.
   - Show the loadtest results in the terminal. **100% Success Rate** on the SQLite WAL (Write-Ahead Logging) database. No locks, no lost data.
   - The API is also protected by strict rate limits (`Flask-Limiter`), locking out brute-force attacks on `/api/login` and rate-limiting normal usage.
4. Finally, mention the **Fallback Chain**:
   - If Groq goes down mid-demo, the app won't crash. `agent/llm.py` automatically iterates through a fallback queue (`gpt-oss-120b`, `qwen3-32b`) with exponential backoffs.

---
**End of Demo.** 
*Cartora: Production-ready, secure, and cost-efficient.*
