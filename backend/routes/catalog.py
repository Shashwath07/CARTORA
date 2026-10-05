from flask import Blueprint, request, jsonify
from backend.services.commerce_service import get_all_products, get_product, get_categories

catalog_bp = Blueprint('catalog', __name__)

@catalog_bp.route('/api/products', methods=['GET'])
def list_products():
    category = request.args.get('category')
    search = request.args.get('search')
    products = get_all_products(category=category, search=search)
    categories = get_categories()
    return jsonify({'products': products, 'categories': categories})

@catalog_bp.route('/api/products/<product_id>', methods=['GET'])
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'product': product})
