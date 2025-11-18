"""Text cleaning utilities for PowerPoint generation."""

import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean text from encoding issues and special characters.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # First, fix the most common pattern: é9, è8, à0, etc.
    # These appear when accented characters are incorrectly parsed
    patterns_to_fix = [
        (r'é9', 'é'),
        (r'è8', 'è'),
        (r'à0', 'à'),
        (r'â2', 'â'),
        (r'ê0', 'ê'),
        (r'î4', 'î'),
        (r'ô4', 'ô'),
        (r'û3', 'û'),
        (r'ç7', 'ç'),
        (r'É9', 'É'),
        (r'È8', 'È'),
        (r'À0', 'À'),
        (r'Ç7', 'Ç'),
    ]
    
    # Apply the main fixes first
    for pattern, replacement in patterns_to_fix:
        text = text.replace(pattern, replacement)
    
    # Then handle other encoding issues
    text = text.replace('\u000e', 'é')  # This is often é
    text = text.replace('\\u000e', 'é')
    text = text.replace('\x0e', 'é')
    text = text.replace('\\x0e', 'é')
    text = text.replace('\u0009', 'é')
    text = text.replace('\\u0009', 'é')
    
    # Common encoding issue patterns
    replacements = {
        r'_x000E_9': 'é',  # Specific pattern for é
        r'_x000E_8': 'è', 
        r'_x000E_0': 'à',
        r'_x000E_2': 'â',
        r'_x000E_A': 'ê',
        r'_x000E_E': 'î',
        r'_x000E_4': 'ô',
        r'_x000E_B': 'û',
        r'_x000E_7': 'ç',
        r'_x000E_': 'é',  # Default for other _x000E_ patterns
        r'_x000F_': '',  # Remove these artifacts
        r'_x000[0-9A-F]_': '',  # Remove other Excel/Word encoding artifacts
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ã ': 'à',
        'Ã¢': 'â',
        'Ãª': 'ê',
        'Ã®': 'î',
        'Ã´': 'ô',
        'Ã»': 'û',
        'Ã§': 'ç',
        'Ã‰': 'É',
        'Ãˆ': 'È',
        'Ã€': 'À',
        'â€™': "'",
        'â€œ': '"',
        'â€': '"',
        'â€"': '–',
        'â€"': '—',
        'â€¦': '...',
        'R\u000e9': 'Ré',  # Specific case from your example
    }
    
    # Apply replacements
    cleaned = text
    for pattern, replacement in replacements.items():
        if pattern.startswith('_') or pattern.startswith('\\'):
            # Use regex for patterns
            cleaned = re.sub(pattern, replacement, cleaned)
        else:
            # Direct string replacement
            cleaned = cleaned.replace(pattern, replacement)
    
    # Remove control characters except newlines and tabs
    cleaned = ''.join(
        char for char in cleaned 
        if char in '\n\t' or not unicodedata.category(char).startswith('C')
    )
    
    # Normalize Unicode
    cleaned = unicodedata.normalize('NFC', cleaned)
    
    # Fix common French encoding issues
    french_fixes = {
        'eÌ': 'é',
        'eÌ€': 'è',
        'aÌ€': 'à',
        'eÌ‚': 'ê',
        'oÌ‚': 'ô',
        'uÌ‚': 'û',
        'iÌ‚': 'î',
        'aÌ‚': 'â',
    }
    
    for pattern, replacement in french_fixes.items():
        cleaned = cleaned.replace(pattern, replacement)
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Trim
    cleaned = cleaned.strip()
    
    return cleaned


def fix_json_encoding(json_str: str) -> str:
    """
    Fix encoding issues in JSON string before parsing.
    
    Args:
        json_str: JSON string with potential encoding issues
        
    Returns:
        Fixed JSON string
    """
    # Fix common JSON encoding issues
    fixed = json_str
    
    # Replace Unicode escape sequences that might be malformed
    fixed = re.sub(r'\\u000e', 'é', fixed)
    fixed = re.sub(r'\\u0009', 'é', fixed)
    fixed = re.sub(r'\\u000a', '', fixed)  # Remove line feeds in JSON
    fixed = re.sub(r'\\u000d', '', fixed)  # Remove carriage returns
    
    # Fix escaped quotes
    fixed = fixed.replace('\\"', '"')
    fixed = fixed.replace("\\'", "'")
    
    return fixed