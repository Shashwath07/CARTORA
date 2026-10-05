import re

def format_response(raw_text: str) -> str:
    """Clean and format the LLM response."""
    if not raw_text or not raw_text.strip():
        return ('I apologize, but I was unable to generate a response. '
                'Please try again or contact our support team for assistance.')
    text = raw_text.strip()
    # Strip common agent prefixes
    for prefix in ['Support Agent:', 'Cartora Assist:', 'Assistant:', 'Agent:']:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    # Normalize excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Limit response length
    if len(text) > 1500:
        text = text[:1497] + '...'
    return text
