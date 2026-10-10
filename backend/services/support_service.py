import re
import logging
import threading
from backend.services.commerce_service import get_customer_profile, build_commerce_context
from memory.memory_service import recall_memories, retain_memory
from agent.prompts import build_support_prompt
from agent.llm import generate_response, LLMError
from agent.response import format_response

logger = logging.getLogger(__name__)

# Short-term context store (last 5 turns per session)
SHORT_TERM_CONTEXT = {}
_ctx_lock = threading.Lock()

def get_short_term_context(session_id: str):
    with _ctx_lock:
        return SHORT_TERM_CONTEXT.get(session_id, [])

def add_short_term_context(session_id: str, user_msg: str, assistant_msg: str):
    with _ctx_lock:
        if session_id not in SHORT_TERM_CONTEXT:
            SHORT_TERM_CONTEXT[session_id] = []
        SHORT_TERM_CONTEXT[session_id].append({'user': user_msg, 'assistant': assistant_msg})
        # Keep only last 5 turns
        if len(SHORT_TERM_CONTEXT[session_id]) > 5:
            SHORT_TERM_CONTEXT[session_id].pop(0)

class ValidationError(Exception):
    pass

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

def handle_message(customer_id: str, message: str, order_context: str = None, session_id: str = 'default'):
    """Process a customer support message through the full pipeline."""
    import time
    import json
    
    t_start = time.perf_counter()
    
    # 1. Validate
    customer_id, message = validate_request(customer_id, message)
    # 2. Load customer profile
    profile = get_customer_profile(customer_id) or {}
    # 3. Build commerce context
    commerce_ctx = build_commerce_context(customer_id, order_id=order_context)
    
    # 4. Recall relevant memories (only if cues are present)
    t_recall_start = time.perf_counter()
    cues = ['again', 'last time', 'still', 'earlier', 'before', 'already', 'tried', 'previous']
    needs_memory = any(c in message.lower() for c in cues)
    
    memories = []
    if needs_memory:
        memories = recall_memories(customer_id, message)
    
    t_recall = time.perf_counter() - t_recall_start
    memories_used = len(memories)
    
    # Fetch short term context
    recent_turns = get_short_term_context(session_id)
    
    # 5. Build prompt
    prompt_messages = build_support_prompt(
        query=message,
        memories=memories,
        customer_profile=profile,
        commerce_context=commerce_ctx,
        recent_turns=recent_turns
    )
    
    # 6. Generate response
    t_llm_start = time.perf_counter()
    llm_output = generate_response(prompt_messages)
    t_llm = time.perf_counter() - t_llm_start
    raw_reply = llm_output['content']
    usage = llm_output['usage']
    
    # 7. Format response
    reply = format_response(raw_reply)
    
    # Update short term context
    add_short_term_context(session_id, message, reply)
    
    # 8. Retain the exchange (summary only, non-blocking via thread or just non-blocking API call handled in memory_service)
    t_retain_start = time.perf_counter()
    
    # Summarize outcome to save tokens
    summary_len = min(100, len(reply))
    outcome = reply[:summary_len] + '...' if len(reply) > 100 else reply
    doc_id = f"{customer_id}-{session_id}"
    
    memory_saved = retain_memory(customer_id, message, outcome, doc_id)
    t_retain = time.perf_counter() - t_retain_start
    
    t_total = time.perf_counter() - t_start
    
    latency_ms = {
        'recall': round(t_recall * 1000),
        'llm': round(t_llm * 1000),
        'retain': round(t_retain * 1000),
        'total': round(t_total * 1000)
    }
    
    telemetry = {
        'customer_id': customer_id,
        'tokens': usage,
        'latency_ms': latency_ms,
        'memories_used': memories_used
    }
    logger.info(f"TELEMETRY: {json.dumps(telemetry)}")
    
    return {
        'reply': reply,
        'customer_id': customer_id,
        'memories_used': memories_used,
        'memory_saved': memory_saved,
        'tokens': usage,
        'latency_ms': latency_ms
    }
