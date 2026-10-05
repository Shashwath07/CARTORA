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


def _run_in_loop(coro):
    """Submit a coroutine to the dedicated event loop and wait for its result."""
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=30)


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
        response = _run_in_loop(client.arecall(bank_id=bank_id, query=query))
        memories = []
        if response and hasattr(response, 'results') and response.results:
            for r in response.results[:max_results]:
                text = getattr(r, 'text', None)
                if text:
                    memories.append(text)
        logger.info(f'Recalled {len(memories)} memories from bank {bank_id}')
        return memories
    except Exception as e:
        logger.warning(f'Hindsight recall failed for bank {bank_id}: {e}')
        return []


def retain_memory(customer_id: str, content: str) -> bool:
    """Store content in customer's Hindsight bank."""
    client = get_hindsight_client()
    if client is None:
        logger.warning('Hindsight client unavailable. Cannot retain memory.')
        return False
    bank_id = get_bank_id(customer_id)
    try:
        _run_in_loop(client.aretain(
            bank_id=bank_id,
            content=content,
            context='Customer support conversation'
        ))
        logger.info(f'Retained memory in bank {bank_id}')
        return True
    except Exception as e:
        logger.warning(f'Hindsight retain failed for bank {bank_id}: {e}')
        return False
