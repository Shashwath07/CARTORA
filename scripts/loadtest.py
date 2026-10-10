import threading
import time
import requests
import statistics

BASE_URL = 'http://127.0.0.1:5000'

def worker(results):
    session = requests.Session()
    # Mocking user context for login bypass or using demo user
    r = session.post(f"{BASE_URL}/api/login", json={'email': 'maya.sharma@cartora.example', 'password': 'CartoraDemo#1'})
    if r.status_code != 200:
        results.append(('error', 'login_failed'))
        return
        
    t0 = time.time()
    # using a simple pure lookup query to test DB layer without hitting Groq/Hindsight if mocked
    r = session.post(f"{BASE_URL}/api/chat", json={'message': 'What is the status of my order?'})
    t1 = time.time()
    
    if r.status_code == 200:
        results.append(('success', (t1 - t0) * 1000))
    else:
        results.append(('error', r.status_code))

def run_loadtest(concurrent_users=50):
    threads = []
    results = []
    
    print(f"Starting load test with {concurrent_users} concurrent users...")
    start_time = time.time()
    
    for _ in range(concurrent_users):
        t = threading.Thread(target=worker, args=(results,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    total_time = time.time() - start_time
    
    latencies = [r[1] for r in results if r[0] == 'success']
    errors = len([r for r in results if r[0] == 'error'])
    
    if latencies:
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies)
    else:
        p50 = p95 = 0
        
    print(f"\n--- LOAD TEST RESULTS ---")
    print(f"Concurrent Users: {concurrent_users}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Success Rate: {(len(latencies) / concurrent_users) * 100:.1f}%")
    print(f"Error Rate: {(errors / concurrent_users) * 100:.1f}%")
    print(f"P50 Latency: {p50:.1f}ms")
    print(f"P95 Latency: {p95:.1f}ms")

if __name__ == '__main__':
    run_loadtest()
