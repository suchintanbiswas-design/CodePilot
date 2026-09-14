"""
Complexity Variation - Medium
4 functions, moderate branching (3-4 branches each).
Average complexity ~10. ~40 lines.
"""

def function_one(a: int, b: int) -> int:
    """Moderate complexity function."""
    if a > 0 and b > 0:
        if a > b:
            return a
        else:
            return b
    elif a < 0 and b < 0:
        return a + b
    return 0

def function_two(x: int) -> str:
    """Moderate complexity function."""
    if x < 10:
        return "Small"
    elif x < 100:
        if x % 2 == 0:
            return "Medium Even"
        return "Medium Odd"
    elif x < 1000:
        return "Large"
    return "Huge"

def function_three(items: list) -> int:
    """Moderate complexity function."""
    total = 0
    for item in items:
        if item % 2 == 0:
            total += item
        elif item % 3 == 0:
            total -= item
        else:
            total += 1
    return total

def function_four(command: str) -> bool:
    """Moderate complexity function."""
    if command == "start":
        return True
    elif command == "stop":
        return False
    elif command == "pause":
        return True
    elif command == "resume":
        return True
    return False
