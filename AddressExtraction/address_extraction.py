import re

def extract_entities(text):
    # Regular expression pattern to extract addresses
    address_pattern = r'\b(?:\d+[ ,\-/\w]*\s+[\w\s,.#\-/\']+?,?\s*(?:(?:near|behind|beside|between|at)?\s*(?:[\w\s]+(?:college|school|park|hospital|shop|store|mall|street|road))?,?\s*)?\s*(?:(?:\b[\w\s]*\b\d{5}\b))?\b)'
    
    # Find all addresses matching the pattern
    addresses = re.findall(address_pattern, text)
    
    return addresses
