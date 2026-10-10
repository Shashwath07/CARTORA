import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Raised when LLM generation fails."""
    pass

def get_groq_client():
    """Create Groq client."""
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        raise LLMError('GROQ_API_KEY not configured')
    return Groq(api_key=api_key)

def generate_response(messages: list) -> dict:
    """Generate response using Groq with fallback chain and backoff."""
    import time
    client = get_groq_client()
    
    # Priority queue of models
    models = []
    if os.environ.get('GROQ_MODEL'):
        models.append(os.environ.get('GROQ_MODEL'))
    models.extend(['openai/gpt-oss-120b', 'qwen/qwen3-32b', 'llama-3.3-70b-versatile', 'llama3-70b-8192'])
    
    # Remove duplicates preserving order
    unique_models = []
    for m in models:
        if m not in unique_models:
            unique_models.append(m)

    last_error = None
    for attempt in range(2): # Simple backoff
        for model in unique_models:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500,
                    timeout=10.0
                )
                content = response.choices[0].message.content
                if not content:
                    continue
                
                usage = response.usage
                return {
                    'content': content,
                    'usage': {
                        'prompt_tokens': getattr(usage, 'prompt_tokens', 0) if usage else 0,
                        'completion_tokens': getattr(usage, 'completion_tokens', 0) if usage else 0
                    }
                }
            except Exception as e:
                logger.warning(f'Model {model} failed: {e}')
                last_error = e
        
        # If all models failed, wait before retrying the chain
        time.sleep(2 ** attempt)

    logger.error(f'All LLM fallbacks failed. Last error: {last_error}')
    raise LLMError('Support service is temporarily unavailable. Please try again.')
