# flask_app/utils/html_sanitizer.py

"""
HTML sanitization utility for research brief summaries
Uses bleach to sanitize HTML content and prevent XSS attacks
"""

import bleach
from typing import Optional

# Allowed HTML tags for research brief summaries
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'b', 'i', 'u',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'blockquote',
    'a'
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel']
}

# Allowed URL schemes for links
ALLOWED_SCHEMES = ['http', 'https', 'mailto']


def sanitize_html(html_content: Optional[str]) -> str:
    """
    Sanitize HTML content for research brief summaries.
    
    Args:
        html_content: HTML string to sanitize (can be None or empty)
    
    Returns:
        Sanitized HTML string, or empty string if input is None/empty
    """
    if not html_content or not html_content.strip():
        return ''
    
    # Remove empty paragraphs that Quill might create
    html_content = html_content.strip()
    if html_content in ['<p><br></p>', '<p></p>', '<p>\n</p>']:
        return ''
    
    # Sanitize the HTML
    sanitized = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_SCHEMES,
        strip=True  # Strip disallowed tags instead of escaping
    )
    
    return sanitized


def is_html_content(content: Optional[str]) -> bool:
    """
    Check if content appears to be HTML (contains HTML tags).
    
    Args:
        content: Content string to check
    
    Returns:
        True if content appears to be HTML, False otherwise
    """
    if not content:
        return False
    
    # Simple check: if it contains HTML tags, it's likely HTML
    return '<' in content and '>' in content
