import re

def extract_context(text, keywords, window=50):
    """
    Extracts context around specified keywords in a given text.

    Parameters:
    - text (str): The text to search within.
    - keywords (list): List of keywords to search for.
    - window (int): The number of characters to include around each keyword.

    Returns:
    - list: List of context strings around the keywords.
    """
    context_list = []
    for keyword in keywords:
        pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            context_list.append(text[start:end])
    return context_list

