"""
Size normalisation test file - Small.
Represents a small module with approximately 25 lines of code.
"""

def process_data(data: list) -> list:
    """
    Processes a list of integers.
    
    This function iterates over the input list, performs some
    transformations, and returns a new list containing the
    processed values.
    """
    result = []
    
    for item in data:
        # Mild issue: unused variable
        temp_val = item * 2
        result.append(item + 1)
        
    return result

def summarize_data(data: list) -> int:
    """
    Calculates the sum of the elements in the data list.
    """
    total = 0
    for num in data:
        total += num
    return total
