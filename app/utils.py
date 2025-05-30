def get_last_fragment(text, fragment_size=1):
    """Return the last fragment of text (sentence or line)"""
    sentences = text.split('.')
    if len(sentences) > fragment_size:
        return '.'.join(sentences[-fragment_size-1:-1]) + '.' if fragment_size > 1 else sentences[-2] + '.'
    return text