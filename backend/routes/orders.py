from flask import Blueprint, request, jsonify, session
from backend.services.commerce_service import (
    get_customer_orders, get_order, create_demo_order
)

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/api/orders', methods=['GET'])
def list_orders():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return jsonify({'error': 'CSRF token missing or invalid'}), 403
    orders = get_customer_orders(customer_id)
    return jsonify({'orders': orders})

@orders_bp.route('/api/orders/<order_id>', methods=['GET'])
def order_detail(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return jsonify({'error': 'CSRF token missing or invalid'}), 403

    order = get_order(order_id, customer_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'order': order})

@orders_bp.route('/api/orders/demo-checkout', methods=['POST'])
def demo_checkout():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return jsonify({'error': 'CSRF token missing or invalid'}), 403
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400
    address = data.get('address')
    payment = data.get('payment_method', 'UPI - Demo')
    order, error = create_demo_order(customer_id, product_id, address, payment)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'order': order, 'message': 'Demo order placed successfully!'}), 201
