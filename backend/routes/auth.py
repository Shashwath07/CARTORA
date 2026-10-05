import json
import os
import logging
from flask import Blueprint, request, jsonify, session

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')

def _load_demo_users():
    path = os.path.join(DATA_DIR, 'demo_users.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Failed to load demo users: {e}')
        return {}

def _load_customers():
    path = os.path.join(DATA_DIR, 'customers.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Failed to load customers: {e}')
        return {}

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    users = _load_demo_users()
    user = users.get(email)
    if not user or user.get('password') != password:
        return jsonify({'error': 'Invalid email or password'}), 401
    customer_id = user['customer_id']
    customers = _load_customers()
    customer = customers.get(customer_id, {})
    session['customer_id'] = customer_id
    session['customer_name'] = user.get('name', customer.get('name', ''))
    session['customer_email'] = email
    return jsonify({
        'success': True,
        'customer': {
            'id': customer_id,
            'name': user.get('name', customer.get('name', '')),
            'email': email,
            'tier': customer.get('tier', 'Standard'),
            'city': customer.get('city', ''),
            'member_since': customer.get('member_since', ''),
            'avatar_initials': customer.get('avatar_initials', ''),
            'saved_address': customer.get('saved_address', ''),
            'phone': customer.get('phone', '')
        }
    })

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/api/me', methods=['GET'])
def get_me():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    customers = _load_customers()
    customer = customers.get(customer_id, {})
    return jsonify({
        'customer': {
            'id': customer_id,
            'name': session.get('customer_name', customer.get('name', '')),
            'email': session.get('customer_email', ''),
            'tier': customer.get('tier', 'Standard'),
            'city': customer.get('city', ''),
            'member_since': customer.get('member_since', ''),
            'avatar_initials': customer.get('avatar_initials', ''),
            'saved_address': customer.get('saved_address', ''),
            'phone': customer.get('phone', '')
        }
    })
