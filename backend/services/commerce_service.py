import json
import os
import logging
import random
import string
import threading
from datetime import datetime, date
import sqlite3

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'commerce.db')

_db_lock = threading.RLock()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with _db_lock:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return [] if filename not in ('customers.json', 'demo_users.json') else {}
        except json.JSONDecodeError as e:
            logger.error(f'Corruption in {filename}: {e}')
            raise

def _generate_id(prefix):
    num = ''.join(random.choices(string.digits, k=6))
    return f'{prefix}-{num}'

def _today():
    return date.today()

def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

# ---- Products & Customers (JSON) ----

def get_all_products(category=None, search=None):
    products = _load_json('products.json')
    if category:
        products = [p for p in products if p.get('category', '').lower() == category.lower()]
    if search:
        search_lower = search.lower()
        products = [p for p in products if search_lower in p.get('name', '').lower() or search_lower in p.get('description', '').lower() or search_lower in p.get('category', '').lower()]
    return products

def get_product(product_id):
    products = _load_json('products.json')
    for p in products:
        if p['id'] == product_id:
            return p
    return None

def get_categories():
    products = _load_json('products.json')
    return sorted(set(p.get('category', '') for p in products))

def get_customer_profile(customer_id):
    customers = _load_json('customers.json')
    return customers.get(customer_id)

# ---- SQLite Helpers ----
def row_to_dict(row):
    if not row: return None
    d = dict(row)
    if 'delivery_steps' in d and isinstance(d['delivery_steps'], str):
        try:
            d['delivery_steps'] = json.loads(d['delivery_steps'])
        except:
            d['delivery_steps'] = []
    # sqlite booleans
    if 'returnable' in d:
        d['returnable'] = bool(d['returnable'])
    return d

# ---- Orders (SQLite) ----

def get_customer_orders(customer_id):
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM orders WHERE customer_id = ?", (customer_id,)).fetchall()
        return [row_to_dict(r) for r in rows]

def get_order(order_id, customer_id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM orders WHERE order_id = ? AND customer_id = ?", (order_id, customer_id)).fetchone()
        return row_to_dict(row)

def create_demo_order(customer_id, product_id, address=None, payment_method='UPI - Demo'):
    with _db_lock:
        product = get_product(product_id)
        if not product:
            return None, 'Product not found'
        if not product.get('in_stock'):
            return None, 'Product out of stock'
        customer = get_customer_profile(customer_id)
        if not customer:
            return None, 'Customer not found'
        today = _today()
        order_id = _generate_id('CT')
        est_days = product.get('delivery_estimate_days', 5)
        from datetime import timedelta
        expected = today + timedelta(days=est_days)
        delivery_steps = [
            {'step': 'Order Placed', 'date': today.isoformat(), 'time': datetime.now().strftime('%I:%M %p'), 'completed': True},
            {'step': 'Packed', 'date': None, 'time': None, 'completed': False},
            {'step': 'Shipped', 'date': None, 'time': None, 'completed': False},
            {'step': 'Out for Delivery', 'date': None, 'time': None, 'completed': False},
            {'step': 'Delivered', 'date': None, 'time': None, 'completed': False}
        ]
        
        order = {
            'order_id': order_id,
            'customer_id': customer_id,
            'product_id': product_id,
            'product_name': product['name'],
            'image_placeholder': product.get('image_placeholder', '📦'),
            'quantity': 1,
            'price': product['price'],
            'currency': product.get('currency', 'INR'),
            'ordered_date': today.isoformat(),
            'delivered_date': None,
            'status': 'Order Placed',
            'returnable': product.get('returnable', True),
            'return_deadline': None,
            'warranty_months': product.get('warranty_months', 0),
            'warranty_end': None,
            'expected_delivery': expected.isoformat(),
            'delivery_steps': json.dumps(delivery_steps),
            'courier': 'Cartora Logistics',
            'tracking_id': f'CL{"".join(random.choices(string.digits, k=9))}',
            'delivery_address': address or customer.get('saved_address', 'Address on file'),
            'payment_method': payment_method
        }
        
        with get_db_connection() as conn:
            columns = ', '.join(order.keys())
            placeholders = ', '.join('?' * len(order))
            conn.execute(f"INSERT INTO orders ({columns}) VALUES ({placeholders})", list(order.values()))
            conn.commit()
            
        order['delivery_steps'] = delivery_steps
        order['returnable'] = bool(order['returnable'])
        return order, None

# ---- Return eligibility ----

def check_return_eligibility(order_id, customer_id):
    order = get_order(order_id, customer_id)
    if not order:
        return None, 'Order not found'
    if order.get('status') != 'Delivered':
        return {'eligible': False, 'reason': 'Order has not been delivered yet.'}, None
    if not order.get('returnable'):
        return {'eligible': False, 'reason': 'This product is not eligible for returns.'}, None
    deadline = _parse_date(order.get('return_deadline'))
    if not deadline:
        return {'eligible': False, 'reason': 'No return deadline available.'}, None
    if _today() > deadline:
        return {
            'eligible': False,
            'reason': f'Return window expired on {order["return_deadline"]}. Today is {_today().isoformat()}.'
        }, None
    return {
        'eligible': True,
        'deadline': order['return_deadline'],
        'product_name': order.get('product_name'),
        'order_id': order_id
    }, None

def create_return(order_id, customer_id, reason, item_condition):
    with _db_lock:
        elig, err = check_return_eligibility(order_id, customer_id)
        if err:
            return None, err
        if not elig or not elig.get('eligible'):
            return None, elig.get('reason', 'Not eligible for return')
        order = get_order(order_id, customer_id)
        return_id = _generate_id('RET')
        today = _today().isoformat()
        ret = {
            'return_id': return_id,
            'order_id': order_id,
            'customer_id': customer_id,
            'product_name': order.get('product_name'),
            'product_id': order.get('product_id'),
            'reason': reason,
            'item_condition': item_condition,
            'status': 'Return Requested',
            'refund_status': 'Pending',
            'refund_amount': order.get('price'),
            'refund_method': order.get('payment_method', 'Original payment method'),
            'created_date': today,
            'last_updated': today
        }
        case = {
            'case_id': _generate_id('CSE'),
            'customer_id': customer_id,
            'type': 'Return',
            'reference_id': return_id,
            'order_id': order_id,
            'product_name': order.get('product_name'),
            'status': 'Open',
            'summary': f'Return request for {order.get("product_name")} - {reason}',
            'created_date': today,
            'last_updated': today
        }
        
        with get_db_connection() as conn:
            c1 = ', '.join(ret.keys())
            p1 = ', '.join('?' * len(ret))
            conn.execute(f"INSERT INTO returns ({c1}) VALUES ({p1})", list(ret.values()))
            
            c2 = ', '.join(case.keys())
            p2 = ', '.join('?' * len(case))
            conn.execute(f"INSERT INTO cases ({c2}) VALUES ({p2})", list(case.values()))
            conn.commit()
            
        return ret, None

# ---- Warranty ----

def check_warranty_status(order_id, customer_id):
    order = get_order(order_id, customer_id)
    if not order:
        return None, 'Order not found'
    warranty_months = order.get('warranty_months', 0)
    if not warranty_months:
        return {'has_warranty': False, 'reason': 'This product does not include a warranty.'}, None
    warranty_end = _parse_date(order.get('warranty_end'))
    if not warranty_end:
        return {'has_warranty': True, 'active': False, 'reason': 'Warranty dates not yet determined. Product may not have been delivered.'}, None
    active = _today() <= warranty_end
    return {
        'has_warranty': True,
        'active': active,
        'warranty_end': order.get('warranty_end'),
        'product_name': order.get('product_name'),
        'order_id': order_id,
        'status': 'Active' if active else 'Expired',
        'reason': None if active else f'Warranty expired on {order["warranty_end"]}.'
    }, None

def create_warranty_claim(order_id, customer_id, issue_category, description):
    with _db_lock:
        wstatus, err = check_warranty_status(order_id, customer_id)
        if err:
            return None, err
        if not wstatus or not wstatus.get('active'):
            reason = wstatus.get('reason', 'Warranty not active') if wstatus else 'Unable to verify warranty'
            return None, reason
        order = get_order(order_id, customer_id)
        claim_id = _generate_id('WRC')
        today = _today().isoformat()
        claim = {
            'claim_id': claim_id,
            'order_id': order_id,
            'customer_id': customer_id,
            'product_name': order.get('product_name'),
            'product_id': order.get('product_id'),
            'issue_category': issue_category,
            'description': description,
            'warranty_end': order.get('warranty_end'),
            'status': 'Claim Submitted',
            'resolution': None,
            'created_date': today,
            'last_updated': today
        }
        case = {
            'case_id': _generate_id('CSE'),
            'customer_id': customer_id,
            'type': 'Warranty',
            'reference_id': claim_id,
            'order_id': order_id,
            'product_name': order.get('product_name'),
            'status': 'Open',
            'summary': f'Warranty claim for {order.get("product_name")} - {issue_category}: {description[:100]}',
            'created_date': today,
            'last_updated': today
        }
        
        with get_db_connection() as conn:
            c1 = ', '.join(claim.keys())
            p1 = ', '.join('?' * len(claim))
            conn.execute(f"INSERT INTO warranties ({c1}) VALUES ({p1})", list(claim.values()))
            
            c2 = ', '.join(case.keys())
            p2 = ', '.join('?' * len(case))
            conn.execute(f"INSERT INTO cases ({c2}) VALUES ({p2})", list(case.values()))
            conn.commit()
            
        return claim, None

# ---- Cases ----

def get_customer_cases(customer_id):
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM cases WHERE customer_id = ?", (customer_id,)).fetchall()
        return [row_to_dict(r) for r in rows]

def get_customer_returns(customer_id):
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM returns WHERE customer_id = ?", (customer_id,)).fetchall()
        return [row_to_dict(r) for r in rows]

def get_customer_warranty_claims(customer_id):
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM warranties WHERE customer_id = ?", (customer_id,)).fetchall()
        return [row_to_dict(r) for r in rows]

# ---- Commerce context for chat ----
def build_commerce_context(customer_id, order_id=None, orders=None):
    lines = []
    if orders is None:
        orders = get_customer_orders(customer_id)
        
    if order_id:
        specific = next((o for o in orders if o['order_id'] == order_id), None)
        if specific:
            lines.append(f'Currently selected order: {specific["order_id"]} - {specific.get("product_name")} '
                        f'- Status: {specific.get("status")} - Price: INR {specific.get("price")}')
            if specific.get('delivered_date'):
                lines.append(f'  Delivered: {specific["delivered_date"]}')
            elif specific.get('expected_delivery'):
                lines.append(f'  Expected delivery: {specific["expected_delivery"]}')
            if specific.get('return_deadline'):
                # evaluate eligibility directly from the specific order dict instead of reading db again
                if specific.get('status') != 'Delivered':
                    lines.append('  Return: Not eligible (Order has not been delivered yet.)')
                elif not specific.get('returnable'):
                    lines.append('  Return: Not eligible (This product is not eligible for returns.)')
                elif specific.get('return_deadline') and _today() > _parse_date(specific.get('return_deadline')):
                    lines.append(f'  Return: Not eligible (Return window expired on {specific["return_deadline"]})')
                else:
                    lines.append(f'  Return: Eligible (deadline: {specific["return_deadline"]})')
                    
            if specific.get('warranty_end'):
                warranty_months = specific.get('warranty_months', 0)
                if not warranty_months:
                    lines.append('  Warranty: No warranty')
                else:
                    wend = _parse_date(specific.get('warranty_end'))
                    if wend:
                        active = _today() <= wend
                        lines.append(f'  Warranty: {"Active" if active else "Expired"} (until: {specific["warranty_end"]})')
    if orders:
        lines.append(f'\\nCustomer has {len(orders)} order(s):')
        for o in orders[:5]:
            line = f'  - {o["order_id"]}: {o.get("product_name")} - {o.get("status")}'
            if o.get('delivered_date'):
                line += f' (delivered {o["delivered_date"]})'
            elif o.get('expected_delivery'):
                line += f' (expected {o["expected_delivery"]})'
            lines.append(line)
    returns = get_customer_returns(customer_id)
    if returns:
        lines.append(f'\\nActive returns: {len(returns)}')
        for r in returns[:3]:
            lines.append(f'  - {r["return_id"]}: {r.get("product_name")} - {r.get("status")}')
    claims = get_customer_warranty_claims(customer_id)
    if claims:
        lines.append(f'\\nWarranty claims: {len(claims)}')
        for c in claims[:3]:
            lines.append(f'  - {c["claim_id"]}: {c.get("product_name")} - {c.get("status")}')
    return '\\n'.join(lines) if lines else None
