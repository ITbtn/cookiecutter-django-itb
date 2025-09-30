import html
import re
import unicodedata
from typing import Any

from rest_framework.exceptions import ValidationError as RestValidationError


def remove_diacritics(text: str) -> str:
    """
    Remove diacritics (accents) from text.
    
    Args:
        text: Input text that may contain accented characters
        
    Returns:
        Text with diacritics removed
        
    Example:
        >>> remove_diacritics("café")
        'cafe'
        >>> remove_diacritics("naïve")
        'naive'
    """
    if not isinstance(text, str):
        return text
    
    # Normalize to NFD (decomposed form) then filter out combining characters
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(
        char for char in normalized 
        if unicodedata.category(char) != 'Mn'
    )
    return without_accents


def validate_script_in_text(value: Any) -> str:
    """
    Validate text against potentially malicious script content.
    
    This validator checks for common XSS attack patterns including:
    - Script tags (case insensitive, with optional spaces)
    - JavaScript event handlers (onmouseover, onload)
    - JavaScript protocol handlers
    - Alert function calls
    
    Args:
        value: The value to validate (will be converted to string)
        
    Returns:
        The original value if validation passes
        
    Raises:
        RestValidationError: If malicious content is detected
        
    Example:
        >>> validate_script_in_text("Hello World")
        'Hello World'
        >>> validate_script_in_text("<script>alert('xss')</script>")
        RestValidationError: Invalid characters/script found in the value
    """
    if value is None:
        return value
    
    # Convert to string if not already
    text_value = str(value)
    
    # Remove diacritics to prevent bypass attempts
    normalized_value = remove_diacritics(text_value)
    
    # Decode HTML entities (e.g., &lt;script&gt; -> <script>)
    unescaped_value = html.unescape(normalized_value)
    
    # Regular expression pattern to match blacklisted patterns
    # Case-insensitive matching for various script injection attempts
    blacklist_patterns = [
        r'<\s*script\b',           # <script or < script
        r'onmouseover\s*=',        # onmouseover=
        r'onload\s*=',             # onload=
        r'onclick\s*=',            # onclick=
        r'onerror\s*=',            # onerror=
        r'onsubmit\s*=',           # onsubmit=
        r'alert\s*\(',             # alert(
        r'javascript\s*:',         # javascript:
        r'eval\s*\(',              # eval(
        r'document\.cookie',       # document.cookie
        r'document\.write',        # document.write
    ]
    
    # Combine all patterns with OR
    combined_pattern = '|'.join(f'({pattern})' for pattern in blacklist_patterns)
    blacklist_regex = re.compile(combined_pattern, re.IGNORECASE)
    
    if blacklist_regex.search(unescaped_value):
        error_message = "Invalid characters/script found in the value"
        raise RestValidationError({"error": error_message, "message": error_message})
    
    return value
    