import re
import logging
import asyncio
import threading
from memory.hindsight_client import get_hindsight_client

logger = logging.getLogger(__name__)

# Dedicated event loop running in a background thread for Hindsight async calls.
# This avoids all conflicts with Flask's thread model.
_loop = None
_loop_thread = None
_loop_lock = threading.Lock()


def _get_loop():
    """Get or create a dedicated event loop for Hindsight operations."""
    global _loop, _loop_thread
    if _loop is not None and _loop.is_running():
        return _loop
    with _loop_lock:
        if _loop is not None and _loop.is_running():
            return _loop
        _loop = asyncio.new_event_loop()

        def _run():
            asyncio.set_event_loop(_loop)
            _loop.run_forever()

        _loop_thread = threading.Thread(target=_run, daemon=True)
        _loop_thread.start()
        logger.info('Hindsight async event loop started.')
    return _loop


def _run_in_loop(coro, wait=True, timeout=10):
    """Submit a coroutine to the dedicated event loop."""
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    if wait:
        return future.result(timeout=timeout)
    return future

def get_bank_id(customer_id: str) -> str:
    """Convert customer ID to a safe Hindsight bank ID."""
    safe_id = customer_id.strip().lower()
    safe_id = re.sub(r'[^a-z0-9_-]', '-', safe_id)
    return f'customer-{safe_id}'

def recall_memories(customer_id: str, query: str, max_results: int = 5) -> list:
    """Recall relevant memories from customer's Hindsight bank."""
    client = get_hindsight_client()
    if client is None:
        logger.warning('Hindsight client unavailable. Returning empty memories.')
        return []
    bank_id = get_bank_id(customer_id)
    try:
        response = _run_in_loop(client.arecall(bank_id=bank_id, query=query, budget='low'))
        memories = []
        if response and hasattr(response, 'results') and response.results:
            for r in response.results[:max_results]:
                text = getattr(r, 'text', None)
                if text:
                    memories.append(text)
        
        # Token cap heuristic (approx 4 chars/token). Cap total memory text to ~500 tokens (2000 chars)
        total_chars = 0
        capped_memories = []
        for mem in memories:
            if total_chars + len(mem) > 2000:
                break
            capped_memories.append(f"[Past interaction]: {mem}")
            total_chars += len(mem)
            
        logger.info(f'Recalled {len(capped_memories)} memories from bank {bank_id}')
        return capped_memories
    except Exception as e:
        logger.warning(f'Hindsight recall failed for bank {bank_id}: {e}')
        return []

def retain_memory(customer_id: str, message: str, outcome: str, doc_id: str) -> bool:
    """Store content in customer's Hindsight bank asynchronously (non-blocking)."""
    client = get_hindsight_client()
    if client is None:
        logger.warning('Hindsight client unavailable. Cannot retain memory.')
        return False
    bank_id = get_bank_id(customer_id)
    try:
        content = f"User asked: {message}\nOutcome: {outcome}"
        _run_in_loop(client.aretain(
            bank_id=bank_id,
            content=content,
            context='Customer support conversation',
            document_id=doc_id,
            tags=['support']
        ), wait=False)
        logger.info(f'Dispatched async retain for bank {bank_id}')
        return True
    except Exception as e:
        logger.warning(f'Hindsight retain dispatch failed for bank {bank_id}: {e}')
        return False
