"""
Data processing module.
Handles loading and parsing configuration files.
"""

import json

def load_config(filepath: str) -> dict:
    """
    Loads configuration from a JSON file.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data
    except Exception: # Broad except clause
        print("Failed to load configuration file.")
        return {}
