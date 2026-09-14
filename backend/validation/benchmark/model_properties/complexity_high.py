"""
Complexity Variation - High
4 functions, heavy branching (5-8 branches each).
Average complexity ~20. ~45 lines.
"""

def function_one(a: int, b: int, c: int) -> int:
    """High complexity function."""
    if a > 0:
        if b > 0:
            if c > 0: return 1
            elif c == 0: return 2
            else: return 3
        else:
            if c > 0: return 4
            else: return 5
    else:
        if b > 0: return 6
        elif b < 0: return 7
        else: return 8

def function_two(val: int) -> str:
    """High complexity function."""
    match val:
        case 1: return "One"
        case 2: return "Two"
        case 3: return "Three"
        case 4: return "Four"
        case 5: return "Five"
        case 6: return "Six"
        case 7: return "Seven"
        case _: return "Unknown"

def function_three(data: list) -> int:
    """High complexity function."""
    score = 0
    for item in data:
        if item == 'A': score += 10
        elif item == 'B': score += 8
        elif item == 'C': score += 5
        elif item == 'D': score += 2
        elif item == 'F': score -= 10
        elif item == 'W': score += 0
        elif item == 'I': score += 0
        else: score -= 1
    return score

def function_four(state: dict) -> bool:
    """High complexity function."""
    if state.get('active'):
        if state.get('role') == 'admin':
            return True
        elif state.get('role') == 'moderator':
            return state.get('can_edit', False)
        elif state.get('role') == 'user':
            if state.get('premium'): return True
            else: return False
    elif state.get('pending'):
        if state.get('verified'): return True
    return False
