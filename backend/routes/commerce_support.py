from flask import Blueprint, request, jsonify, session
from backend.services.commerce_service import (
    check_return_eligibility, create_return, get_customer_returns,
    check_warranty_status, create_warranty_claim, get_customer_warranty_claims,
    get_customer_cases, get_customer_orders
)

commerce_bp = Blueprint('commerce', __name__)

# ---- Returns ----

@commerce_bp.route('/api/returns/eligibility/<order_id>', methods=['GET'])
def return_eligibility(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    result, error = check_return_eligibility(order_id, customer_id)
    if error:
        return jsonify({'error': error}), 404
    return jsonify(result)

@commerce_bp.route('/api/returns', methods=['GET'])
def list_returns():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    returns = get_customer_returns(customer_id)
    return jsonify({'returns': returns})

@commerce_bp.route('/api/returns', methods=['POST'])
def create_return_request():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    order_id = data.get('order_id')
    reason = data.get('reason', '').strip()
    item_condition = data.get('item_condition', '').strip()
    if not order_id or not reason or not item_condition:
        return jsonify({'error': 'order_id, reason and item_condition are required'}), 400
    ret, error = create_return(order_id, customer_id, reason, item_condition)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'return_request': ret, 'message': 'Return request created successfully!'}), 201

# ---- Warranty ----

@commerce_bp.route('/api/warranty/status/<order_id>', methods=['GET'])
def warranty_status(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    result, error = check_warranty_status(order_id, customer_id)
    if error:
        return jsonify({'error': error}), 404
    return jsonify(result)

@commerce_bp.route('/api/warranty/claims', methods=['GET'])
def list_warranty_claims():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    claims = get_customer_warranty_claims(customer_id)
    return jsonify({'claims': claims})

@commerce_bp.route('/api/warranty/claims', methods=['POST'])
def create_claim():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    order_id = data.get('order_id')
    issue_category = data.get('issue_category', '').strip()
    description = data.get('description', '').strip()
    if not order_id or not issue_category or not description:
        return jsonify({'error': 'order_id, issue_category and description are required'}), 400
    claim, error = create_warranty_claim(order_id, customer_id, issue_category, description)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'claim': claim, 'message': 'Warranty claim submitted successfully!'}), 201

# ---- Cases ----

@commerce_bp.route('/api/cases', methods=['GET'])
def list_cases():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    cases = get_customer_cases(customer_id)
    return jsonify({'cases': cases})
