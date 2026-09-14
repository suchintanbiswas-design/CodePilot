"""
Size normalisation test file - Medium.
Represents a medium module with approximately 50 lines of code.

This file contains two mild issues that are proportionally scaled
from the size 500 file, maintaining the same issue density.
"""

def process_data_alpha(data: list) -> list:
    """
    Processes a list of integers (Alpha strategy).
    """
    result = []
    
    for item in data:
        # Mild issue 1: unused variable
        temp_val = item * 2
        result.append(item + 1)
        
    return result

def summarize_data_alpha(data: list) -> int:
    """
    Calculates the sum of the elements in the data list (Alpha strategy).
    """
    total = 0
    for num in data:
        total += num
    return total

def process_data_beta(data: list) -> list:
    """
    Processes a list of integers (Beta strategy).
    """
    result = []
    
    for item in data:
        # Mild issue 2: unused variable
        temp_val_beta = item * 3
        result.append(item + 2)
        
    return result

def summarize_data_beta(data: list) -> int:
    """
    Calculates the product of the elements in the data list (Beta strategy).
    """
    total = 1
    for num in data:
        total *= num
    return total
