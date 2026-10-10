import os
import json
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import check_password_hash
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')

def get_demo_users():
    path = os.path.join(DATA_DIR, 'demo_users.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load demo users: {e}")
        return {}

# We can apply rate limiting directly to the blueprint routes by importing the global limiter or using it in app.py.
# However, the easiest strict lockout is using a dictionary or relying on the app's limiter.
login_attempts = {}

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
        
    # Lockout check
    ip = request.remote_addr
    attempts = login_attempts.get(ip, 0)
    if attempts >= 5:
        return jsonify({'error': 'Too many failed attempts. Locked out.'}), 429
        
    users = get_demo_users()
    user = users.get(email)
    
    if user and check_password_hash(user.get('password'), password):
        session['customer_id'] = user['customer_id']
        login_attempts[ip] = 0 # reset
        return jsonify({
            'success': True,
            'customer_id': user['customer_id'],
            'name': user['name']
        })
    else:
        login_attempts[ip] = attempts + 1
        return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/api/me', methods=['GET'])
def me():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    from backend.services.commerce_service import get_customer_profile
    profile = get_customer_profile(customer_id)
    if profile:
        return jsonify(profile)
    return jsonify({'error': 'Profile not found'}), 404
