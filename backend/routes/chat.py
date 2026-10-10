import logging
from flask import Blueprint, request, jsonify, session
from backend.services.support_service import handle_message, ValidationError
from agent.llm import LLMError

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'Cartora Support'})

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    # Require authentication
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    message = data.get('message', '').strip()
    order_context = data.get('order_context')
    session_id = data.get('session_id', 'default-session')
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    try:
        result = handle_message(
            customer_id=customer_id,
            message=message,
            order_context=order_context,
            session_id=session_id
        )
        return jsonify(result)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except LLMError as e:
        logger.error(f'LLM error: {e}')
        return jsonify({'error': 'Support service is temporarily unavailable. Please try again.'}), 502
    except Exception as e:
        logger.error(f'Unexpected error in chat: {e}', exc_info=True)
        return jsonify({'error': 'An unexpected error occurred.'}), 500
