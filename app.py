import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask, send_from_directory, session, redirect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, static_folder=None)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'cartora-demo-secret-change-in-production')
    
    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.chat import chat_bp
    from backend.routes.catalog import catalog_bp
    from backend.routes.orders import orders_bp
    from backend.routes.commerce_support import commerce_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(commerce_bp)
    
    # Frontend routes
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    
    @app.route('/')
    def login_page():
        if session.get('customer_id'):
            return redirect('/app')
        return send_from_directory(frontend_dir, 'login.html')
    
    @app.route('/app')
    def app_page():
        if not session.get('customer_id'):
            return redirect('/')
        return send_from_directory(frontend_dir, 'app.html')
    
    @app.route('/frontend/<path:filename>')
    def frontend_static(filename):
        return send_from_directory(frontend_dir, filename)
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    logger.info(f'Starting Cartora on port {port} (debug={debug})')
    app.run(host='0.0.0.0', port=port, debug=debug)
