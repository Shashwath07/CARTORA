import pytest
import os
import sqlite3
from backend.services.commerce_service import get_customer_orders, build_commerce_context, search_relevant_orders, create_demo_order

def test_dynamic_order_retrieval():
    # 1. Multiple orders for the same product
    order1, _ = create_demo_order('C1001', 'P1002') 
    order2, _ = create_demo_order('C1001', 'P1002')
    
    # 2. Retrieval by partial or case-insensitive product name
    orders_after = search_relevant_orders('C1001', 'where is my smartwatch')
    assert order1['order_id'] in [o['order_id'] for o in orders_after]
    assert order2['order_id'] in [o['order_id'] for o in orders_after]
    
    # 3. Retrieval by exact order ID
    orders_exact = search_relevant_orders('C1001', f"status of {order1['order_id']}")
    assert len(orders_exact) >= 1
    assert order1['order_id'] in [o['order_id'] for o in orders_exact]
    
    # 4. User A unable to retrieve User B orders
    order_b, _ = create_demo_order('C1002', 'P1003')
    orders_b_searched_by_a = search_relevant_orders('C1001', f"check {order_b['order_id']}")
    assert order_b['order_id'] not in [o['order_id'] for o in orders_b_searched_by_a]
    
    # 5. Missing orders
    orders_missing = search_relevant_orders('C1001', 'where is my nonexistentproduct')
    # Should fallback to recent 5 orders if no match
    assert len(orders_missing) <= 5
    
    ctx = build_commerce_context('C1001', message='where is my smartwatch')
    assert order1['order_id'] in ctx
    assert order2['order_id'] in ctx
