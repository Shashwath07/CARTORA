import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5000'

def run_benchmark():
    session = requests.Session()
    print("Logging in...")
    r = session.post(f"{BASE_URL}/api/login", json={'email': 'maya.sharma@cartora.example', 'password': 'CartoraDemo#1'})
    if r.status_code != 200:
        print("Login failed!")
        return

    messages = [
        "Hi, I need help with an order.",
        "Yes, the earbuds.",
        "Can I still return them?",
        "What is the warranty period?",
        "Do I need to send the original box?",
        "Okay, how do I start the return?",
        "I already tried restarting them.",
        "Can you just refund me?",
        "Is there a restocking fee?",
        "Thanks for the info."
    ]

    total_prompt_tokens = 0
    total_comp_tokens = 0
    total_recall_ms = 0
    total_llm_ms = 0
    total_retain_ms = 0
    total_time_ms = 0

    print("Running 10-message benchmark...")
    
    for i, msg in enumerate(messages, 1):
        t0 = time.time()
        r = session.post(f"{BASE_URL}/api/chat", json={'message': msg})
        if r.status_code != 200:
            print(f"Error on message {i}: {r.status_code}")
            continue
            
        data = r.json()
        
        tokens = data.get('tokens', {})
        latency = data.get('latency_ms', {})
        
        total_prompt_tokens += tokens.get('prompt_tokens', 0)
        total_comp_tokens += tokens.get('completion_tokens', 0)
        
        total_recall_ms += latency.get('recall', 0)
        total_llm_ms += latency.get('llm', 0)
        total_retain_ms += latency.get('retain', 0)
        total_time_ms += latency.get('total', 0)
        
        print(f"[{i}/10] Latency: {latency.get('total')}ms | Tokens: {tokens.get('prompt_tokens')}p + {tokens.get('completion_tokens')}c")

    print("\n--- BASELINE RESULTS (Averages over 10 messages) ---")
    print(f"Avg Prompt Tokens: {total_prompt_tokens / 10:.1f}")
    print(f"Avg Completion Tokens: {total_comp_tokens / 10:.1f}")
    print(f"Avg Recall Latency: {total_recall_ms / 10:.1f} ms")
    print(f"Avg LLM Latency: {total_llm_ms / 10:.1f} ms")
    print(f"Avg Retain Latency: {total_retain_ms / 10:.1f} ms")
    print(f"Avg Total Request Latency: {total_time_ms / 10:.1f} ms")
    
if __name__ == '__main__':
    run_benchmark()
