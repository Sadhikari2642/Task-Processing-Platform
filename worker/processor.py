def process(operation, text):
    """Process text according to operation."""
    if operation == 'uppercase':
        return text.upper()
    if operation == 'lowercase':
        return text.lower()
    if operation == 'reverse':
        return text[::-1]
    if operation == 'wordcount':
        return {'count': len(text.split())}
    raise ValueError('unknown op')
