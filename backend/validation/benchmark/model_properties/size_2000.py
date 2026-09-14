"""
Size normalisation test file - Large.
Represents a large module with approximately 100 lines of code.

This file contains four mild issues that are proportionally scaled
from the size 500 file, maintaining the same issue density.
"""

def process_data_alpha(data: list) -> list:
    """Processes a list of integers (Alpha)."""
    result = []
    for item in data:
        # Mild issue 1: unused variable
        temp_val = item * 2
        result.append(item + 1)
    return result

def summarize_data_alpha(data: list) -> int:
    """Summarizes alpha data."""
    total = 0
    for num in data:
        total += num
    return total

def process_data_beta(data: list) -> list:
    """Processes a list of integers (Beta)."""
    result = []
    for item in data:
        # Mild issue 2: unused variable
        temp_val_beta = item * 3
        result.append(item + 2)
    return result

def summarize_data_beta(data: list) -> int:
    """Summarizes beta data."""
    total = 1
    for num in data:
        total *= num
    return total

def process_data_gamma(data: list) -> list:
    """Processes a list of integers (Gamma)."""
    result = []
    for item in data:
        # Mild issue 3: unused variable
        temp_val_gamma = item * 4
        result.append(item + 3)
    return result

def summarize_data_gamma(data: list) -> int:
    """Summarizes gamma data."""
    total = 0
    for num in data:
        total += num * 2
    return total

def process_data_delta(data: list) -> list:
    """Processes a list of integers (Delta)."""
    result = []
    for item in data:
        # Mild issue 4: unused variable
        temp_val_delta = item * 5
        result.append(item + 4)
    return result

def summarize_data_delta(data: list) -> int:
    """Summarizes delta data."""
    total = 0
    for num in data:
        total += num * 3
    return total

def helper_function_1():
    """Dummy helper 1 to pad length."""
    pass

def helper_function_2():
    """Dummy helper 2 to pad length."""
    pass

def helper_function_3():
    """Dummy helper 3 to pad length."""
    pass

def helper_function_4():
    """Dummy helper 4 to pad length."""
    pass

def helper_function_5():
    """Dummy helper 5 to pad length."""
    pass

def helper_function_6():
    """Dummy helper 6 to pad length."""
    pass

def helper_function_7():
    """Dummy helper 7 to pad length."""
    pass

def helper_function_8():
    """Dummy helper 8 to pad length."""
    pass
