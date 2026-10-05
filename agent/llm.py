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

def generate_response(messages: list) -> str:
    """Generate response using Groq."""
    try:
        client = get_groq_client()
        model = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMError('Empty response from model')
        return content
    except LLMError:
        raise
    except Exception as e:
        logger.error(f'Groq generation failed: {e}')
        raise LLMError(f'LLM generation failed: {e}')
