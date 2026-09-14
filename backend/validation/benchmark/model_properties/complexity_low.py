"""
Complexity Variation - Low
4 simple functions, each with ~1-2 branches.
Average complexity ~5. ~40 lines.
"""

def function_one(a: int, b: int) -> int:
    """Simple function with 1 branch."""
    if a > b:
        return a + b
    return a - b

def function_two(x: int) -> int:
    """Simple function with 1 branch."""
    if x % 2 == 0:
        return x // 2
    return x * 3 + 1

def function_three(name: str) -> str:
    """Simple function with 2 branches."""
    if not name:
        return "Unknown"
    elif len(name) > 10:
        return name[:10]
    return name

def function_four(items: list) -> int:
    """Simple function with 2 branches."""
    if not items:
        return 0
    if len(items) == 1:
        return items[0]
    return items[0] + items[-1]

def padding_to_reach_40_lines():
    """Padding function."""
    pass

def more_padding():
    """More padding."""
    pass
