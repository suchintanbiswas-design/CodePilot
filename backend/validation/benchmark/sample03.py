"""
File handling utilities.
"""
import csv
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def read_csv_safely(file_path: str) -> List[Dict[str, Any]]:
    """
    Read a CSV file safely using a context manager.
    Handles common file parsing errors.
    """
    results = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except csv.Error as e:
        logger.error(f"CSV parsing error in {file_path}: {e}")
        raise ValueError(f"Invalid CSV format: {e}")
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        raise
        
    return results
