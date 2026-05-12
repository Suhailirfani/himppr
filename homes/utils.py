import re

def is_malayalam(text):
    if not text:
        return False
    
    text = str(text)
    
    # If it contains Unicode Malayalam characters
    if re.search(r'[\u0D00-\u0D7F]', text):
        return True
    
    # Check for extended ASCII (>127) which is used heavily in legacy ML fonts
    if any(ord(c) > 127 for c in text):
        return True
        
    # Check for specific symbols used heavily in legacy ML mappings
    special_ml_chars = r'[\^\]\[\\_\}\{\|\~`]'
    if re.search(special_ml_chars, text):
        return True
        
    return False

def identify_and_swap(val1, val2):
    """
    Analyzes two strings and returns (malayalam_val, english_val).
    """
    if not val1 and not val2:
        return "", ""
    
    if not val1:
        if is_malayalam(val2):
            return val2, ""
        else:
            return "", val2
            
    if not val2:
        if is_malayalam(val1):
            return val1, ""
        else:
            return "", val1

    # Both are present
    v1_is_ml = is_malayalam(val1)
    v2_is_ml = is_malayalam(val2)

    if v1_is_ml and not v2_is_ml:
        return val1, val2
    elif v2_is_ml and not v1_is_ml:
        return val2, val1
    elif v1_is_ml and v2_is_ml:
        # Both are Malayalam? Return as is or prioritize first
        return val1, val2
    else:
        # Both are English? Return as is or prioritize first as Malayalam (unlikely but safe)
        return val1, val2
