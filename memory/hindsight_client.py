import os
import logging
import threading

logger = logging.getLogger(__name__)

_client = None
_lock = threading.Lock()


def get_hindsight_client():
    """Get or create singleton Hindsight client."""
    global _client
    if _client is not None:
        return _client
    with _lock:
        if _client is not None:
            return _client
        try:
            from hindsight_client import Hindsight
            api_key = os.environ.get('HINDSIGHT_API_KEY')
            base_url = os.environ.get('HINDSIGHT_BASE_URL', 'https://api.hindsight.vectorize.io')
            if not api_key:
                logger.warning('HINDSIGHT_API_KEY not set. Memory features will be unavailable.')
                return None
            _client = Hindsight(
                base_url=base_url, 
                api_key=api_key,
                timeout=15,
                max_attempts=2
            )
            logger.info('Hindsight client initialized successfully.')
        except ImportError:
            logger.warning('hindsight-client package not installed. Memory features unavailable.')
            return None
        except Exception as e:
            logger.error(f'Failed to initialize Hindsight client: {e}')
            return None
    return _client
