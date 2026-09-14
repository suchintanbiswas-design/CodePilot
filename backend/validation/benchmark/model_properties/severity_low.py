"""
Utility module for processing string data.
"""

import sys
import os # Unused import

def format_greeting(name: str) -> str:
    """
    Returns a formatted greeting string.
    """
    greeting = f"Hello, {name}!"
    return greeting

def get_length(text: str) -> int:
    """
    Returns the length of the string.
    """
    return len(text)
