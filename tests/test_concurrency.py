import pytest
import concurrent.futures
import requests
import time
import os
import json
import threading

BASE_URL = 'http://127.0.0.1:5000'

def test_concurrent_checkouts():
    """Test that concurrent demo-checkouts do not cause data loss."""
    # Reset orders to baseline first via direct file access to avoid API side-effects
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    orders_file = os.path.join(data_dir, 'orders.json')
    
    with open(orders_file, 'r', encoding='utf-8') as f:
        original = json.load(f)
    # Keep only the original 3 orders
    baseline = [o for o in original if o['order_id'] in ('CT-824501', 'CT-823991', 'CT-825004')]
    with open(orders_file, 'w', encoding='utf-8') as f:
        json.dump(baseline, f, indent=2)

    # Prepare sessions
    sessions = []
    for _ in range(30):
        s = requests.Session()
        sessions.append(s)
        
    # Login all sessions sequentially to avoid auth race conditions (not the subject of this test)
    for s in sessions:
        r = s.post(f'{BASE_URL}/api/login', json={'email':'maya.sharma@cartora.example','password':'CartoraDemo#1'})
        assert r.status_code == 200
        
    def do_checkout(s):
        return s.post(f'{BASE_URL}/api/orders/demo-checkout', json={'product_id': 'P1005'})

    # Fire 30 concurrent checkouts
    successes = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(do_checkout, s) for s in sessions]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res.status_code == 201:
                successes += 1

    assert successes == 30, f"Expected 30 successful checkouts, got {successes}"

    # Verify that the orders table has 30 new orders (plus whatever was there)
    import sqlite3
    db_path = os.path.join(data_dir, 'commerce.db')
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    
    assert count >= 33, f"Data loss detected! Expected at least 33 orders, found {count}"
    
    # Cleanup (reset back to 3)
    with open(orders_file, 'w', encoding='utf-8') as f:
        json.dump(baseline, f, indent=2)

if __name__ == '__main__':
    pytest.main(['-v', __file__])
