import re
import logging
from backend.services.commerce_service import get_customer_profile, build_commerce_context
from memory.memory_service import recall_memories, retain_memory
from agent.prompts import build_support_prompt
from agent.llm import generate_response, LLMError
from agent.response import format_response

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    pass

def validate_request(customer_id: str, message: str):
    """Validate chat request inputs."""
    if not customer_id or not customer_id.strip():
        raise ValidationError('Customer ID is required.')
    customer_id = customer_id.strip()
    if not re.match(r'^[A-Za-z0-9_-]{3,32}$', customer_id):
        raise ValidationError('Customer ID must be 3-32 characters (letters, digits, hyphens, underscores).')
    if not message or not message.strip():
        raise ValidationError('Message is required.')
    message = message.strip()
    if len(message) > 1000:
        raise ValidationError('Message must be under 1000 characters.')
    return customer_id, message

def handle_message(customer_id: str, message: str, order_context: str = None):
    """Process a customer support message through the full pipeline."""
    # 1. Validate
    customer_id, message = validate_request(customer_id, message)
    # 2. Load customer profile
    profile = get_customer_profile(customer_id) or {}
    # 3. Build commerce context
    commerce_ctx = build_commerce_context(customer_id, order_id=order_context)
    # 4. Recall relevant memories
    memories = recall_memories(customer_id, message)
    memories_used = len(memories)
    # 5. Build prompt
    prompt_messages = build_support_prompt(
        query=message,
        memories=memories,
        customer_profile=profile,
        commerce_context=commerce_ctx
    )
    # 6. Generate response
    raw_reply = generate_response(prompt_messages)
    # 7. Format response
    reply = format_response(raw_reply)
    # 8. Retain the exchange
    exchange = f'Customer said: {message}\nSupport agent replied: {reply}'
    memory_saved = retain_memory(customer_id, exchange)
    return {
        'reply': reply,
        'customer_id': customer_id,
        'memories_used': memories_used,
        'memory_saved': memory_saved
    }
